"""Catalogue pages: the shop grid with filters, product detail, reviews."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import services
from .models import Category, Product, ProductSize, Review, Size, Tag


# ------------------------------------------------------------- filtering --

SORTS = {
    "": ("ordering",),
    "newest": ("-created_at",),
    "price-asc": ("price",),
    "price-desc": ("-price",),
    "name": ("name",),
    "rating": ("-rating", "-reviews_count"),
}


def _selected(request, key: str) -> list[str]:
    raw = request.GET.get(key, "") or ""
    return [value for value in raw.split(",") if value]


def build_filter_context(request, category=None):
    """Everything the sidebar needs, plus the active-filter summary."""
    products = Product.objects.active().select_related("category").prefetch_related("images")

    query = (request.GET.get("q") or "").strip()
    if query:
        products = products.search(query)

    if category is not None:
        products = products.in_category(category)

    sizes = _selected(request, "size")
    size_objects = []
    if sizes:
        size_objects = list(Size.objects.filter(slug__in=sizes))
        if size_objects:
            products = products.filter(sizes__size__in=size_objects).distinct()

    tags = _selected(request, "tag")
    tag_objects = []
    if tags:
        tag_objects = list(Tag.objects.filter(slug__in=tags))
        if tag_objects:
            products = products.filter(tags__in=tag_objects).distinct()

    # Price range, as two comma-separated numbers.
    price_min = price_max = None
    price_raw = (request.GET.get("price") or "").strip()
    if price_raw:
        parts = [p for p in price_raw.split(",") if p]
        try:
            if len(parts) >= 1 and parts[0]:
                price_min = Decimal(parts[0])
            if len(parts) >= 2 and parts[1]:
                price_max = Decimal(parts[1])
        except InvalidOperation:
            price_min = price_max = None
        if price_min is not None:
            products = products.filter(price__gte=price_min)
        if price_max is not None:
            products = products.filter(price__lte=price_max)

    ordering = SORTS.get(request.GET.get("sort", "") or "", SORTS[""])
    products = products.order_by(*ordering)

    # Sidebar counts: a category shows its whole subtree, as in the mockup.
    category_rows = []
    roots = (
        Category.objects.filter(is_active=True, parent__isnull=True)
        .prefetch_related("children")
        .order_by("ordering", "name")
    )
    for root in roots:
        family_ids = root.get_family_ids()
        category_rows.append({
            "category": root,
            "count": Product.objects.active().filter(category_id__in=family_ids).count(),
            "children": [
                {
                    "category": child,
                    "count": Product.objects.active().in_category(child).count(),
                }
                for child in root.children.filter(is_active=True).order_by("ordering", "name")
            ],
        })

    return {
        "filter_products": products,
        "search_query": query,
        "selected_sizes": size_objects,
        "selected_tags": tag_objects,
        "price_min": price_min,
        "price_max": price_max,
        "sort": request.GET.get("sort", "") or "",
        "sort_options": [
            ("", "Default"), ("newest", "Newest first"), ("price-asc", "Price: low to high"),
            ("price-desc", "Price: high to low"), ("rating", "Best rated"), ("name", "Name A–Z"),
        ],
        "all_sizes": Size.objects.order_by("ordering"),
        "all_tags": Tag.objects.filter(is_active=True).order_by("name"),
        "category_rows": category_rows,
    }


def paginate(request, queryset, per_page=None):
    """Django's paginator, pinned to a sane page on a bad ?page=."""
    from django.conf import settings

    paginator = Paginator(queryset, per_page or settings.PRODUCTS_PER_PAGE)
    page_number = request.GET.get("page") or 1
    try:
        page_obj = paginator.page(page_number)
    except Exception:  # non-numeric or out-of-range page
        page_obj = paginator.page(1)
    return paginator, page_obj


# ----------------------------------------------------------------- views --

def shop(request, category: Category | None = None):
    """The catalogue grid, optionally narrowed to a category subtree."""
    context = build_filter_context(request, category)
    paginator, page_obj = paginate(request, context["filter_products"])
    context.update({
        "nav_active": "shop",
        "page_obj": page_obj,
        "paginator": paginator,
        "category": category,
        "page_title": f"{category.name} — GreenShop" if category else "Shop — GreenShop",
        "breadcrumbs": category.breadcrumbs if category else [],
    })
    return render(request, "shop.html", context)


def category_detail(request, slug: str):
    category = get_object_or_404(
        Category.objects.filter(is_active=True), slug=slug
    )
    return shop(request, category=category)


def product_detail(request, slug: str):
    product = get_object_or_404(
        Product.objects.active()
        .select_related("category")
        .prefetch_related("images", "tags", "sizes__size", "reviews__user"),
        slug=slug,
    )

    reviews = [
        review for review in product.reviews.filter(is_approved=True)
    ]
    paginator, review_page = paginate(request, reviews, per_page=5)

    # Related: same category, excluding this product, then backfilled.
    related = list(
        Product.objects.active()
        .in_category(product.category)
        .exclude(pk=product.pk)
        .select_related("category")
        .prefetch_related("images")
    )[:4]
    if len(related) < 4:
        backfill = list(
            Product.objects.active()
            .exclude(pk__in=[p.pk for p in related] + [product.pk])
            .select_related("category")
            .prefetch_related("images")
        )[: 4 - len(related)]
        related += backfill

    in_wishlist = services.is_wishlisted(request.user, product)

    context = {
        "nav_active": "shop",
        "product": product,
        "sizes": product.get_sizes(),
        "reviews": review_page,
        "paginator": paginator,
        "related": related,
        "in_wishlist": in_wishlist,
        "breadcrumb_category": product.category,
        "page_title": f"{product.name} — GreenShop",
    }
    return render(request, "product.html", context)


def wishlist(request):
    if not request.user.is_authenticated:
        # Send them to the login page, not back to this URL — redirecting to
        # `?next=<self>` loops forever.
        return redirect(f"{reverse('core:login')}?next={quote(request.path)}")

    entries = (
        request.user.wishlist.select_related("product__category")
        .prefetch_related("product__images")
    )
    products = [entry.product for entry in entries]
    return render(request, "wishlist.html", {
        "nav_active": "wishlist",
        "products": products,
        "page_title": "My Wishlist — GreenShop",
    })


@login_required
@require_POST
def wishlist_toggle(request, product_id: int):
    product = get_object_or_404(Product, pk=product_id)
    added = services.toggle_wishlist(request.user, product)
    if added:
        messages.success(request, f"{product.name} added to your wishlist.")
    else:
        messages.info(request, f"{product.name} removed from your wishlist.")

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)
    return redirect(product)


@login_required
@require_POST
def add_review(request, product_id: int):
    product = get_object_or_404(Product, pk=product_id)

    try:
        rating = int(request.POST.get("rating", 0))
    except (TypeError, ValueError):
        rating = 0
    if not 1 <= rating <= 5:
        messages.error(request, "Please choose a rating between 1 and 5.")
        return redirect(product)

    if Review.objects.filter(product=product, user=request.user).exists():
        messages.info(request, "You have already reviewed this product.")
        return redirect(product)

    Review.objects.create(
        product=product,
        user=request.user,
        rating=rating,
        title=(request.POST.get("title") or "").strip()[:120],
        body=(request.POST.get("body") or "").strip(),
        is_approved=False,
    )
    messages.success(request, "Thanks! Your review will appear once it is approved.")
    return redirect(product)

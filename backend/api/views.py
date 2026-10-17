from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation

from django.contrib import auth as django_auth
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from catalog import services as catalog_services
from catalog.models import Category, Product, ProductSize, Review, Size, Tag, Wishlist
from core.models import Address, Subscriber
from orders import services as order_services
from orders.forms import CheckoutForm
from orders.models import Cart, Order

from . import serializers
from .models import BlogPost


DEFAULT_LIMIT = 9
MAX_LIMIT = 50
TRUTHY = {"1", "true", "yes", "on"}


def json_body(request) -> dict | None:
    try:
        data = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def error_response(errors: dict, status: int = 400) -> JsonResponse:
    return JsonResponse({"errors": errors}, status=status)


def detail_response(detail: str, status: int) -> JsonResponse:
    return JsonResponse({"detail": detail}, status=status)


def _is_staff(user) -> bool:
    return bool(user is not None and user.is_authenticated and user.is_staff)


def _int_param(request, name: str, default: int):
    raw = request.GET.get(name)
    if raw is None or raw == "":
        return default, None
    try:
        return int(raw), None
    except (TypeError, ValueError):
        return None, f"{name} must be an integer."


def _decimal_param(request, name: str, errors: dict):
    raw = (request.GET.get(name) or "").strip()
    if not raw:
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        errors[name] = ["Must be a number."]
        return None


def _next_url(request, offset: int, limit: int, total: int):
    if offset + limit >= total:
        return None
    params = request.GET.copy()
    params["offset"] = str(offset + limit)
    params["limit"] = str(limit)
    return request.build_absolute_uri(f"{request.path}?{params.urlencode()}")


def paginate(request, queryset, serializer, default_limit=DEFAULT_LIMIT):
    limit, limit_err = _int_param(request, "limit", default_limit)
    offset, offset_err = _int_param(request, "offset", 0)
    if limit_err or offset_err:
        return None, error_response({"detail": limit_err or offset_err})
    if limit < 1:
        return None, error_response({"detail": "limit must be at least 1."})
    if offset < 0:
        return None, error_response({"detail": "offset must not be negative."})

    limit = min(limit, MAX_LIMIT)
    total = len(queryset) if isinstance(queryset, list) else queryset.count()
    rows = [serializer(obj) for obj in queryset[offset : offset + limit]]
    meta = {
        "limit": limit,
        "offset": offset,
        "count": total,
        "next": _next_url(request, offset, limit, total),
    }
    return rows, meta


def _find_product(value) -> Product | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return Product.objects.filter(pk=value).first()
    value = str(value).strip()
    if not value:
        return None
    if value.isdigit():
        return Product.objects.filter(pk=int(value)).first()
    return Product.objects.filter(slug=value).first()


SORTS = {
    "": ("ordering",),
    "newest": ("-created_at",),
    "price-asc": ("price",),
    "price-desc": ("-price",),
    "name": ("name",),
    "rating": ("-rating", "-reviews_count"),
}


@require_http_methods(["GET"])
@ensure_csrf_cookie
def product_list(request):
    staff = _is_staff(request.user)
    include_disabled = staff and request.GET.get("include_disabled") in TRUTHY

    products = Product.objects.select_related(
        "category__parent"
    ).prefetch_related("images", "tags")
    if not include_disabled:
        products = products.active()

    category_slug = (request.GET.get("category") or "").strip()
    if category_slug:
        category = get_object_or_404(
            Category.objects.filter(is_active=True), slug=category_slug
        )
        products = products.in_category(category)

    sizes = [value for value in (request.GET.get("size") or "").split(",") if value]
    if sizes:
        size_rows = Size.objects.filter(slug__in=sizes)
        products = products.filter(
            sizes__size__in=size_rows, sizes__is_active=True
        ).distinct()

    tags = [value for value in (request.GET.get("tag") or "").split(",") if value]
    if tags:
        tag_rows = Tag.objects.filter(slug__in=tags, is_active=True)
        products = products.filter(tags__in=tag_rows).distinct()

    errors: dict = {}
    price_min = _decimal_param(request, "price_min", errors)
    price_max = _decimal_param(request, "price_max", errors)
    if errors:
        return error_response(errors)
    if price_min is not None:
        products = products.filter(price__gte=price_min)
    if price_max is not None:
        products = products.filter(price__lte=price_max)

    if request.GET.get("sale") in TRUTHY:
        products = products.on_sale()
    if request.GET.get("featured") in TRUTHY:
        products = products.filter(is_featured=True)

    query = (request.GET.get("q") or "").strip()
    if query:
        products = products.search(query)

    sort = request.GET.get("sort", "") or ""
    products = products.order_by(*SORTS.get(sort, SORTS[""]))

    rows, meta = paginate(request, products, serializers.serialize_product_summary)
    if rows is None:
        return meta
    return JsonResponse({"products": rows, "meta": meta})


@require_http_methods(["GET"])
def product_detail(request, slug: str):
    staff = _is_staff(request.user)
    products = Product.objects.select_related("category__parent").prefetch_related(
        "images", "tags", "sizes__size"
    )
    if not staff:
        products = products.active()
    product = get_object_or_404(products, slug=slug)

    reviews = Review.objects.filter(product=product).select_related("user")
    if not staff:
        if request.user.is_authenticated:
            reviews = reviews.filter(Q(is_approved=True) | Q(user=request.user))
        else:
            reviews = reviews.filter(is_approved=True)
    review_rows = [
        serializers.serialize_review(review, include_product=False)
        for review in reviews.order_by("-created_at")
    ]

    row = serializers.serialize_product_detail(product, review_rows)
    return JsonResponse({"product": row})


@require_http_methods(["GET"])
def category_tree(request):
    active = list(Category.objects.filter(is_active=True).order_by("ordering", "name"))

    children_map: dict[int | None, list] = {}
    for category in active:
        children_map.setdefault(category.parent_id, []).append(category)

    own_counts = dict(
        Product.objects.filter(is_active=True)
        .values_list("category_id")
        .annotate(n=Count("id"))
    )

    def subtree_count(category) -> int:
        return own_counts.get(category.pk, 0) + sum(
            subtree_count(child) for child in children_map.get(category.pk, [])
        )

    def node(category) -> dict:
        return serializers.serialize_category_node(
            category,
            [node(child) for child in children_map.get(category.pk, [])],
            subtree_count(category),
        )

    rows = [node(category) for category in children_map.get(None, [])]
    return JsonResponse({"categories": rows})


@require_http_methods(["GET"])
def size_list(request):
    counts = {
        row["size_id"]: row["n"]
        for row in ProductSize.objects.filter(
            is_active=True, product__is_active=True
        )
        .values("size_id")
        .annotate(n=Count("id", distinct=True))
    }
    rows = [
        serializers.serialize_size(size, counts.get(size.pk, 0))
        for size in Size.objects.order_by("ordering", "name")
    ]
    return JsonResponse({"sizes": rows})


@require_http_methods(["GET"])
def tag_list(request):
    tags = Tag.objects.filter(is_active=True).order_by("name")
    return JsonResponse({"tags": [serializers.serialize_tag(tag) for tag in tags]})


def _live_blog_posts():
    return BlogPost.objects.filter(
        is_published=True, published_at__lte=timezone.now()
    )


@require_http_methods(["GET"])
def blog_list(request):
    staff = _is_staff(request.user)
    posts = BlogPost.objects.all() if staff else _live_blog_posts()

    query = (request.GET.get("q") or "").strip()
    if query:
        posts = posts.filter(
            Q(title__icontains=query)
            | Q(excerpt__icontains=query)
            | Q(body__icontains=query)
        )

    tag = (request.GET.get("tag") or "").strip()
    if tag:
        posts = [post for post in posts if tag in post.tags_list]

    rows, meta = paginate(
        request, posts, serializers.serialize_blog_post, default_limit=10
    )
    if rows is None:
        return meta
    return JsonResponse({"posts": rows, "meta": meta})


@require_http_methods(["GET"])
def blog_detail(request, slug: str):
    staff = _is_staff(request.user)
    posts = BlogPost.objects.all() if staff else _live_blog_posts()
    post = get_object_or_404(posts, slug=slug)
    return JsonResponse({"post": serializers.serialize_blog_post(post)})


def _serialize_cart(cart) -> dict:
    lines = list(cart.items)
    subtotal = cart.subtotal
    discount = cart.discount
    shipping = (
        order_services.shipping_cost(subtotal - discount) if lines else Decimal("0.00")
    )
    total = max(subtotal - discount + shipping, Decimal("0.00"))
    return {
        "id": cart.pk,
        "coupon_code": cart.coupon_code or None,
        "item_count": sum(line.quantity for line in lines),
        "items": [serializers.serialize_cart_line(line) for line in lines],
        "subtotal": serializers.money(subtotal),
        "discount": serializers.money(discount),
        "shipping": serializers.money(shipping),
        "total": serializers.money(total),
        "free_shipping_threshold": serializers.money(
            order_services.FREE_SHIPPING_OVER
        ),
    }


def _cart_response(request, status: int = 200) -> JsonResponse:
    cart = order_services.get_cart(request)
    if cart is None:
        return detail_response("You have no cart yet.", 404)
    return JsonResponse({"cart": _serialize_cart(cart)}, status=status)


@require_http_methods(["GET", "DELETE"])
@ensure_csrf_cookie
def cart_detail(request):
    if request.method == "DELETE":
        cart = order_services.get_cart(request)
        if cart is None:
            return detail_response("You have no cart to clear.", 404)
        cart.clear()
        return _cart_response(request)

    order_services.get_cart(request, create=True)
    return _cart_response(request)


@require_http_methods(["POST"])
def cart_item_add(request):
    body = json_body(request)
    if body is None:
        return detail_response("Expected a JSON object body.", 400)

    errors: dict = {}

    product = None
    raw_product = body.get("product")
    if raw_product in (None, ""):
        errors["product"] = ["This field is required."]
    else:
        product = _find_product(raw_product)
        if product is None:
            errors["product"] = ["Unknown product."]
        elif not product.is_active:
            errors["product"] = ["This product is no longer for sale."]

    size = None
    raw_size = body.get("size")
    if raw_size not in (None, ""):
        if product is None:
            errors["size"] = ["Cannot pick a size without a valid product."]
        else:
            try:
                size = ProductSize.objects.select_related("size").get(
                    pk=int(raw_size), product=product
                )
            except (ProductSize.DoesNotExist, TypeError, ValueError):
                errors["size"] = ["This size is not offered for the chosen product."]
            else:
                if not size.is_active:
                    errors["size"] = ["This size is no longer offered."]
                    size = None

    try:
        quantity = int(body.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = None
    if quantity is None or quantity < 1:
        errors["quantity"] = ["Quantity must be a positive integer."]

    if errors:
        return error_response(errors)

    try:
        order_services.add_to_cart(request, product, size=size, quantity=quantity)
    except ValidationError as exc:
        return error_response(exc.message_dict)
    return _cart_response(request, status=201)


@require_http_methods(["PATCH", "DELETE"])
def cart_item_detail(request, line_id: int):
    cart = order_services.get_cart(request)
    line = cart.lines.filter(pk=line_id).first() if cart is not None else None
    if line is None:
        return detail_response("No such item in your cart.", 404)

    if request.method == "DELETE":
        order_services.remove_line(request, line_id)
        return _cart_response(request)

    body = json_body(request)
    if body is None:
        return detail_response("Expected a JSON object body.", 400)
    if "quantity" not in body:
        return error_response({"quantity": ["This field is required."]})
    try:
        quantity = int(body["quantity"])
    except (TypeError, ValueError):
        return error_response({"quantity": ["Quantity must be an integer."]})

    try:
        order_services.set_quantity(request, line_id, quantity)
    except ValidationError as exc:
        return error_response(exc.message_dict)
    return _cart_response(request)


@require_http_methods(["PATCH", "POST"])
def cart_coupon(request):
    body = json_body(request)
    if body is None:
        return detail_response("Expected a JSON object body.", 400)

    code = str(body.get("code") or "").strip()
    if code and code.upper() != "GREEN10":
        return error_response({"code": [f"“{code}” is not a valid coupon code."]})
    order_services.apply_coupon(request, code)
    return _cart_response(request)


@require_http_methods(["POST"])
def checkout(request):
    if not request.user.is_authenticated:
        return detail_response("Sign in to place an order.", 401)

    body = json_body(request)
    if body is None:
        return detail_response("Expected a JSON object body.", 400)

    cart = order_services.get_cart(request)
    if cart is None or cart.is_empty:
        return error_response({"cart": ["Your basket is empty."]})

    data = {key: value for key, value in body.items() if key != "address_id"}

    raw_address = body.get("address_id")
    if raw_address not in (None, ""):
        try:
            address_id = int(raw_address)
        except (TypeError, ValueError):
            address_id = None
        address = (
            Address.objects.filter(pk=address_id, user=request.user).first()
            if address_id is not None
            else None
        )
        if address is None:
            return error_response(
                {"address_id": ["No such address in your address book."]}
            )
        adopted = {
            "full_name": address.full_name,
            "phone": address.phone,
            "address_line": address.line1,
            "city": address.city,
            "region": address.region,
            "postal_code": address.postal_code,
            "country": address.country,
        }
        overrides = {key: value for key, value in data.items() if value not in (None, "")}
        data = {**adopted, **overrides}

    form = CheckoutForm(data)
    if not form.is_valid():
        return error_response(
            {key: [str(message) for message in messages] for key, messages in form.errors.items()}
        )

    try:
        order = order_services.place_order(
            request,
            full_name=form.cleaned_data["full_name"],
            email=form.cleaned_data["email"],
            phone=form.cleaned_data["phone"],
            address_line=form.cleaned_data["address_line"],
            city=form.cleaned_data["city"],
            region=form.cleaned_data["region"],
            postal_code=form.cleaned_data["postal_code"],
            country=form.cleaned_data["country"],
            note=form.cleaned_data["note"],
            payment_method=form.cleaned_data["payment_method"],
        )
    except ValidationError as exc:
        return error_response(exc.message_dict)

    return JsonResponse({"order": serializers.serialize_order(order)}, status=201)


@require_http_methods(["GET"])
def order_list(request):
    if not request.user.is_authenticated:
        return detail_response("Sign in to see your orders.", 401)
    staff = _is_staff(request.user)

    see_all = staff and request.GET.get("all") in TRUTHY
    orders = Order.objects.all() if see_all else Order.objects.for_user(request.user)

    status_param = (request.GET.get("status") or "").strip()
    if status_param:
        if not staff:
            return detail_response(
                "Only staff may filter orders by status.", 403
            )
        if status_param not in Order.Status.values:
            return error_response({"status": ["Unknown order status."]})
        orders = orders.filter(status=status_param)

    rows = [
        serializers.serialize_order(order)
        for order in orders.prefetch_related("items")
    ]
    return JsonResponse({"orders": rows, "meta": {"count": len(rows)}})


@require_http_methods(["GET", "PATCH"])
def order_detail(request, number: str):
    if not request.user.is_authenticated:
        return detail_response("Sign in to view this order.", 401)

    order = get_object_or_404(Order.objects.prefetch_related("items"), number=number)
    staff = _is_staff(request.user)
    if order.user_id != request.user.pk and not staff:
        return detail_response("No such order.", 404)

    if request.method == "GET":
        return JsonResponse({"order": serializers.serialize_order(order)})

    body = json_body(request)
    if body is None:
        return detail_response("Expected a JSON object body.", 400)

    status_value = body.get("status")
    if status_value not in Order.Status.values:
        return error_response(
            {"status": [f"Must be one of: {', '.join(Order.Status.values)}."]}
        )
    if not staff and (
        status_value != Order.Status.CANCELLED or order.status != Order.Status.NEW
    ):
        return detail_response(
            "You may only cancel an order that has not started yet.", 403
        )

    order.transition(status_value)
    return JsonResponse({"order": serializers.serialize_order(order)})


@require_http_methods(["GET", "POST"])
def review_list(request):
    if request.method == "POST":
        return _create_review(request)

    staff = _is_staff(request.user)
    reviews = Review.objects.select_related("user", "product")
    if not staff:
        if request.user.is_authenticated:
            reviews = reviews.filter(Q(is_approved=True) | Q(user=request.user))
        else:
            reviews = reviews.filter(is_approved=True)

    product_param = (request.GET.get("product") or "").strip()
    if product_param:
        product = _find_product(product_param)
        if product is None:
            return error_response({"product": ["Unknown product."]})
        reviews = reviews.filter(product=product)

    rows = [serializers.serialize_review(review) for review in reviews]
    return JsonResponse({"reviews": rows, "meta": {"count": len(rows)}})


def _create_review(request):
    if not request.user.is_authenticated:
        return detail_response("Sign in to write a review.", 401)

    body = json_body(request)
    if body is None:
        return detail_response("Expected a JSON object body.", 400)

    errors: dict = {}

    product = None
    raw_product = body.get("product")
    if raw_product in (None, ""):
        errors["product"] = ["This field is required."]
    else:
        product = _find_product(raw_product)
        if product is None or not product.is_active:
            errors["product"] = ["Unknown product."]

    try:
        rating = int(body.get("rating"))
    except (TypeError, ValueError):
        rating = None
    if rating is None or not 1 <= rating <= 5:
        errors["rating"] = ["Rating must be between 1 and 5."]

    if errors:
        return error_response(errors)

    if Review.objects.filter(product=product, user=request.user).exists():
        return error_response(
            {"product": ["You have already reviewed this product."]}
        )

    review = Review.objects.create(
        product=product,
        user=request.user,
        rating=rating,
        title=str(body.get("title") or "").strip()[:120],
        body=str(body.get("body") or "").strip(),
        is_approved=False,
    )
    return JsonResponse({"review": serializers.serialize_review(review)}, status=201)


@require_http_methods(["GET", "POST"])
def wishlist(request):
    if not request.user.is_authenticated:
        return detail_response("Sign in to use your wishlist.", 401)

    if request.method == "GET":
        entries = request.user.wishlist.select_related(
            "product__category__parent"
        ).prefetch_related("product__images", "product__tags")
        rows = [serializers.serialize_product_summary(entry.product) for entry in entries]
        return JsonResponse({"products": rows, "meta": {"count": len(rows)}})

    body = json_body(request)
    if body is None:
        return detail_response("Expected a JSON object body.", 400)

    product = _find_product(body.get("product"))
    if product is None or not product.is_active:
        return error_response({"product": ["Unknown product."]})
    wished = catalog_services.toggle_wishlist(request.user, product)
    return JsonResponse({"product_id": product.pk, "wishlisted": wished})


@require_http_methods(["DELETE"])
def wishlist_remove(request, product_id: int):
    if not request.user.is_authenticated:
        return detail_response("Sign in to use your wishlist.", 401)
    entry = request.user.wishlist.filter(product_id=product_id).first()
    if entry is None:
        return detail_response("That product is not in your wishlist.", 404)
    entry.delete()
    return JsonResponse({"product_id": product_id, "wishlisted": False})


@require_http_methods(["POST"])
def auth_login(request):
    body = json_body(request)
    if body is None:
        return detail_response("Expected a JSON object body.", 400)

    errors: dict = {}
    username = str(body.get("username") or "").strip()
    password = str(body.get("password") or "")
    if not username:
        errors["username"] = ["This field is required."]
    if not password:
        errors["password"] = ["This field is required."]
    if errors:
        return error_response(errors)

    user = django_auth.authenticate(request, username=username, password=password)
    if user is None:
        return detail_response("Invalid username or password.", 401)

    if request.session.session_key:
        anon = Cart.objects.filter(
            session_key=request.session.session_key
        ).first()
        if anon is not None:
            order_services.attach_cart_to_user(anon, user)

    django_auth.login(request, user)
    return JsonResponse({"user": serializers.serialize_user(user)})


@require_http_methods(["POST"])
def auth_logout(request):
    django_auth.logout(request)
    return HttpResponse(status=204)


@require_http_methods(["GET"])
def auth_me(request):
    if not request.user.is_authenticated:
        return detail_response("Not signed in.", 401)
    return JsonResponse({"user": serializers.serialize_user(request.user)})


@require_http_methods(["POST"])
def newsletter_subscribe(request):
    body = json_body(request)
    if body is None:
        return detail_response("Expected a JSON object body.", 400)

    email = str(body.get("email") or "").strip().lower()
    if not email:
        return error_response({"email": ["This field is required."]})
    try:
        validate_email(email)
    except ValidationError:
        return error_response({"email": ["Enter a valid email address."]})

    subscriber, created = Subscriber.objects.get_or_create(email=email)
    if not created and not subscriber.is_active:
        subscriber.is_active = True
        subscriber.save(update_fields=["is_active", "updated_at"])

    if created:
        return JsonResponse({"detail": f"{email} is subscribed.", "email": email}, status=201)
    return JsonResponse({"detail": f"{email} is already subscribed.", "email": email})

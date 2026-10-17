from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from catalog.models import Category, Product, Tag
from catalog.services import category_row_tree, sizes_cached, sidebar_counts
from orders.models import Order
from orders.services import attach_cart_to_user, get_cart, prime_cart

from .forms import AddressForm, RegisterForm
from .models import Address, Subscriber, User


def home(request):
    featured = (
        Product.objects.active()
        .featured()
        .select_related("category")
        .prefetch_related("images")
    )
    products = list(featured)[:9]
    if len(products) < 9:
        extras = (
            Product.objects.active()
            .exclude(pk__in=[p.pk for p in products])
            .select_related("category")
            .prefetch_related("images")
        )[: 9 - len(products)]
        products += list(extras)

    category_rows = category_row_tree()

    size_counts = sidebar_counts()["sizes"]
    size_rows = [
        {"size": size, "count": size_counts.get(size.pk, 0)}
        for size in sizes_cached()
    ]

    context = {
        "nav_active": "home",
        "page_title": "GreenShop — plants for a better planet",
        "hero_products": products[:3],
        "products": products,
        "category_rows": category_rows,
        "size_rows": size_rows,
        "tags": Tag.objects.filter(is_active=True),
        "sale_products": Product.objects.active().on_sale().order_by("ordering")[:3],
    }
    return render(request, "home.html", context)


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("core:account")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user: User = form.save()
                anon_cart = get_cart(request)
                if anon_cart is not None:
                    prime_cart(request, attach_cart_to_user(anon_cart, user))
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name or user.username}!")
            next_url = request.GET.get("next") or request.POST.get("next")
            return redirect(next_url if next_url and next_url.startswith("/") else "core:home")
    else:
        form = RegisterForm()

    return render(request, "register.html", {
        "form": form,
        "nav_active": "register",
        "page_title": "Register — GreenShop",
    })


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:account")

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if request.session.session_key:
            from orders.models import Cart

            anon = Cart.objects.filter(session_key=request.session.session_key).first()
            if anon is not None:
                prime_cart(request, attach_cart_to_user(anon, user))
        login(request, user)
        messages.success(request, f"Signed in as {user}.")
        next_url = request.GET.get("next") or request.POST.get("next")
        return redirect(next_url if next_url and next_url.startswith("/") else "core:home")

    return render(request, "login.html", {
        "form": form,
        "nav_active": "login",
        "page_title": "Login — GreenShop",
    })


@login_required
def account(request):
    orders = Order.objects.for_user(request.user)[:10]
    context = {
        "page_title": "My Account — GreenShop",
        "orders": orders,
        "order_count": orders.count(),
        "addresses": request.user.addresses.all(),
        "wishlist_count": request.user.wishlist.count(),
        "review_count": request.user.reviews.filter(is_approved=True).count(),
    }
    return render(request, "account.html", context)


@login_required
def address_list(request):
    return render(request, "address.html", {
        "page_title": "Address Book — GreenShop",
        "addresses": request.user.addresses.all(),
        "form": AddressForm(),
    })


@login_required
@require_http_methods(["GET", "POST"])
def address_create(request):
    form = AddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        address: Address = form.save(commit=False)
        address.user = request.user
        address.save()
        messages.success(request, "Address saved.")
        return redirect("core:address-list")
    return render(request, "address_form.html", {
        "form": form, "page_title": "Add Address — GreenShop", "editing": False,
    })


@login_required
@require_http_methods(["GET", "POST"])
def address_update(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    form = AddressForm(request.POST or None, instance=address)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Address updated.")
        return redirect("core:address-list")
    return render(request, "address_form.html", {
        "form": form, "address": address, "editing": True,
        "page_title": "Edit Address — GreenShop",
    })


@login_required
@require_POST
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.info(request, "Address removed.")
    return redirect("core:address-list")


@require_POST
def subscribe(request):
    email = (request.POST.get("email") or "").strip().lower()
    if not email:
        messages.error(request, "Please enter an email address.")
        return redirect(request.META.get("HTTP_REFERER") or "core:home")

    subscriber, created = Subscriber.objects.get_or_create(email=email)
    if not created and not subscriber.is_active:
        subscriber.is_active = True
        subscriber.save(update_fields=["is_active", "updated_at"])

    if created:
        messages.success(request, f"Thanks — {email} is subscribed.")
    else:
        messages.info(request, f"{email} is already subscribed.")
    return redirect(request.META.get("HTTP_REFERER") or "core:home")

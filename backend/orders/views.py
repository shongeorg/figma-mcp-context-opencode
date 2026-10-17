from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from catalog.models import Product, ProductSize

from . import services
from .forms import CheckoutForm
from .models import Order


def _redirect_back(request, fallback="orders:cart"):
    candidate = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(candidate)
    return redirect(fallback)


def cart(request):
    cart_obj = services.get_cart(request)
    lines = list(cart_obj.items) if cart_obj else []
    subtotal = cart_obj.subtotal if cart_obj else 0
    discount = cart_obj.discount if cart_obj else 0
    shipping = services.shipping_cost(subtotal - discount) if cart_obj else 0
    context = {
        "nav_active": "shop",
        "cart": cart_obj,
        "lines": lines,
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "total": max(subtotal - discount + shipping, 0) if cart_obj else 0,
        "free_shipping_over": services.FREE_SHIPPING_OVER,
        "page_title": "Shopping Cart — GreenShop",
    }
    return render(request, "cart.html", context)


@require_POST
def add_to_cart(request, product_id: int):
    product = get_object_or_404(Product, pk=product_id, is_active=True)

    size = None
    size_id = request.POST.get("size")
    if size_id:
        size = get_object_or_404(
            ProductSize, pk=size_id, product=product, is_active=True
        )

    try:
        quantity = max(int(request.POST.get("quantity", 1)), 1)
    except (TypeError, ValueError):
        quantity = 1

    try:
        line = services.add_to_cart(request, product, size=size, quantity=quantity)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
        return _redirect_back(request, product)

    messages.success(request, f"Added {line.quantity} × {product.name} to your cart.")
    return _redirect_back(request, "orders:cart")


@require_POST
def update_cart(request, line_id: int):
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1
    services.set_quantity(request, line_id, quantity)
    if quantity <= 0:
        messages.info(request, "Item removed from your cart.")
    return redirect("orders:cart")


@require_POST
def remove_from_cart(request, line_id: int):
    services.remove_line(request, line_id)
    messages.info(request, "Item removed from your cart.")
    return redirect("orders:cart")


@require_POST
def apply_coupon(request):
    code = (request.POST.get("coupon") or "").strip()
    cart_obj = services.apply_coupon(request, code)
    if cart_obj.coupon_code:
        messages.success(request, f"Coupon {cart_obj.coupon_code} applied.")
    else:
        messages.error(request, f"“{code or '—'}” is not a valid coupon code.")
    return redirect("orders:cart")


def checkout(request):
    cart_obj = services.get_cart(request)
    if cart_obj is None or cart_obj.is_empty:
        messages.info(request, "Your cart is empty.")
        return redirect("orders:cart")

    initial = {}
    if request.user.is_authenticated:
        user = request.user
        default_address = user.addresses.filter(is_default=True).first()
        if default_address:
            initial.update({
                "full_name": default_address.full_name,
                "phone": default_address.phone,
                "address_line": default_address.line1,
                "city": default_address.city,
                "region": default_address.region,
                "postal_code": default_address.postal_code,
                "country": default_address.country,
            })
        else:
            initial.update({
                "full_name": user.get_full_name(),
                "phone": user.phone,
                "email": user.email,
            })

    if request.method == "POST":
        form = CheckoutForm(request.POST, initial=initial)
        if form.is_valid():
            try:
                order = services.place_order(
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
                messages.error(request, "; ".join(exc.messages))
                return redirect("orders:cart")

            messages.success(
                request,
                f"Order {order.number} received. We will confirm it by email.",
            )
            return redirect("orders:detail", number=order.number)
    else:
        form = CheckoutForm(initial=initial)

    subtotal = cart_obj.subtotal
    discount = cart_obj.discount
    shipping = services.shipping_cost(subtotal - discount)

    return render(request, "checkout.html", {
        "nav_active": "shop",
        "form": form,
        "cart": cart_obj,
        "lines": list(cart_obj.items),
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "total": max(subtotal - discount + shipping, 0),
        "page_title": "Checkout — GreenShop",
    })


@login_required
def order_list(request):
    orders = Order.objects.for_user(request.user)
    return render(request, "orders.html", {
        "nav_active": "account",
        "orders": orders,
        "page_title": "My Orders — GreenShop",
    })


@login_required
def order_detail(request, number: str):
    order = get_object_or_404(
        Order.objects.for_user(request.user).prefetch_related("items"), number=number
    )
    return render(request, "order_detail.html", {
        "nav_active": "account",
        "order": order,
        "page_title": f"Order {order.number} — GreenShop",
    })

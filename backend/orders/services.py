from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q, Sum
from django.db.models.functions import Greatest
from django.utils import timezone

from catalog.models import Product, ProductSize

from .models import Cart, CartItem, Order, OrderItem

SHIPPING_FLAT = Decimal("9.00")
FREE_SHIPPING_OVER = Decimal("120.00")

_CART_ATTR = "_greenshop_cart"


def get_cart(request, create: bool = False) -> Cart | None:
    memo = request.__dict__.setdefault(_CART_ATTR, {})
    if "cart" in memo and (memo["cart"] is not None or not create):
        return memo["cart"]

    cart = _resolve_cart(request, create)
    memo["cart"] = cart
    return cart


def prime_cart(request, cart: Cart | None) -> None:
    request.__dict__.setdefault(_CART_ATTR, {})["cart"] = cart


def _resolve_cart(request, create: bool) -> Cart | None:
    user = getattr(request, "user", None)
    badge = Sum("lines__quantity", filter=Q(lines__is_active=True))

    if user is not None and user.is_authenticated:
        cart = Cart.objects.filter(user=user).annotate(badge_count=badge).first()
        if cart is None and create:
            anon_key = request.session.session_key
            anon = Cart.objects.filter(session_key=anon_key).first() if anon_key else None
            if anon is not None:
                return attach_cart_to_user(anon, user)
            cart = Cart.objects.create(user=user)
        return cart

    key = request.session.session_key
    if not key:
        if not create:
            return None
        request.session.create()
        key = request.session.session_key

    cart = Cart.objects.filter(session_key=key).annotate(badge_count=badge).first()
    if cart is None and create:
        cart = Cart.objects.create(session_key=key)
    return cart


@transaction.atomic
def attach_cart_to_user(anon_cart: Cart, user) -> Cart:
    existing = Cart.objects.filter(user=user).first()
    if existing is None:
        anon_cart.user = user
        anon_cart.session_key = None
        anon_cart.save(update_fields=["user", "session_key", "updated_at"])
        anon_cart.invalidate_items()
        return anon_cart

    if anon_cart.pk == existing.pk:
        return existing

    for line in anon_cart.lines.all():
        other = existing.lines.filter(product=line.product, size=line.size).first()
        if other is None:
            line.cart = existing
            line.save(update_fields=["cart", "updated_at"])
        else:
            other.quantity += line.quantity
            other.save(update_fields=["quantity", "updated_at"])
            line.delete()

    anon_cart.delete()
    existing.invalidate_items()
    return existing


@transaction.atomic
def add_to_cart(request, product, size=None, quantity: int = 1) -> CartItem:
    if not product.is_active:
        raise ValidationError({"product": "This product is no longer for sale."})

    available = size.stock if size is not None else product.stock
    if available < quantity:
        raise ValidationError({"quantity": f"Only {available} left in stock."})

    cart = get_cart(request, create=True)
    line, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=size,
        defaults={"quantity": quantity},
    )
    if not created:
        line.quantity += quantity
    line.save()
    cart.invalidate_items()
    return line


def set_quantity(request, line_id: int, quantity: int) -> CartItem | None:
    cart = get_cart(request)
    if cart is None:
        return None
    line = cart.lines.filter(pk=line_id).first()
    if line is None:
        return None
    if quantity <= 0:
        line.delete()
        cart.invalidate_items()
        return None
    line.quantity = quantity
    line.save()
    cart.invalidate_items()
    return line


def remove_line(request, line_id: int) -> None:
    cart = get_cart(request)
    if cart is not None:
        cart.lines.filter(pk=line_id).delete()
        cart.invalidate_items()


def apply_coupon(request, code: str) -> Cart:
    cart = get_cart(request, create=True)
    code = (code or "").strip().upper()
    if code == "GREEN10":
        cart.coupon_code = code
        cart.coupon_discount = (cart.subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
    else:
        cart.coupon_code = ""
        cart.coupon_discount = Decimal("0.00")
    cart.save()
    return cart


def shipping_cost(subtotal) -> Decimal:
    if subtotal >= FREE_SHIPPING_OVER:
        return Decimal("0.00")
    return SHIPPING_FLAT


@transaction.atomic
def place_order(request, *, full_name, email, phone="", address_line, city,
                region="", postal_code="", country="USA", note="",
                payment_method=Order.PaymentMethod.COD) -> Order:
    cart = get_cart(request, create=False)
    if cart is None or cart.is_empty:
        raise ValidationError({"cart": "Your basket is empty."})

    lines = list(cart.items)
    user = request.user if request.user.is_authenticated else None

    subtotal = cart.subtotal
    discount = cart.discount
    shipping = shipping_cost(subtotal - discount)

    order = Order.objects.create(
        user=user,
        full_name=full_name,
        email=email,
        phone=phone,
        address_line=address_line,
        city=city,
        region=region,
        postal_code=postal_code,
        country=country,
        note=note,
        payment_method=payment_method,
        coupon_code=cart.coupon_code,
        subtotal=subtotal,
        discount=discount,
        shipping=shipping,
        total=max(subtotal - discount + shipping, Decimal("0.00")),
    )

    for line in lines:
        OrderItem.from_cart_line(order, line)
        if line.size_id and line.size:
            ProductSize.objects.filter(pk=line.size_id).update(
                stock=Greatest(F("stock") - line.quantity, 0)
            )
        Product.objects.filter(pk=line.product_id).update(
            stock=Greatest(F("stock") - line.quantity, 0)
        )

    cart.clear()
    return order


def collect_stale_carts() -> int:
    from django.conf import settings

    cutoff = timezone.now() - timezone.timedelta(days=settings.CART_SESSION_DAYS)
    deleted, _ = Cart.objects.filter(user__isnull=True, updated_at__lt=cutoff).delete()
    return deleted

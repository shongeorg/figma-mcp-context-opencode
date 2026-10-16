"""Cart and checkout behaviour.

Kept out of the views so that the same rules apply to the storefront, the
basket page and any future API.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Cart, CartItem, Order, OrderItem

SHIPPING_FLAT = Decimal("9.00")
FREE_SHIPPING_OVER = Decimal("120.00")


def get_cart(request, create: bool = False) -> Cart | None:
    """Return the visitor's cart, creating one only when asked.

    A signed-in user always gets their own row; an anonymous visitor gets a
    session-keyed one.  Signing in merges the anonymous cart into the user's
    cart rather than losing it (see :func:`attach_cart_to_user`).
    """
    user = getattr(request, "user", None)

    if user is not None and user.is_authenticated:
        cart = Cart.objects.filter(user=user).first()
        if cart is None and create:
            # Adopt the anonymous basket first, so nothing in it is lost.
            anon = Cart.objects.filter(session_key=request.session.session_key).first()
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

    cart = Cart.objects.filter(session_key=key).first()
    if cart is None and create:
        cart = Cart.objects.create(session_key=key)
    return cart


def attach_cart_to_user(anon_cart: Cart, user) -> Cart:
    """Fold an anonymous basket into the signed-in user's basket."""
    existing = Cart.objects.filter(user=user).first()
    if existing is None:
        anon_cart.user = user
        anon_cart.session_key = None
        anon_cart.save(update_fields=["user", "session_key", "updated_at"])
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
    return existing


def add_to_cart(request, product, size=None, quantity: int = 1) -> CartItem:
    """Add (or top up) a line in the visitor's basket."""
    if not product.is_active:
        raise ValidationError({"product": "This product is no longer for sale."})

    cart = get_cart(request, create=True)
    available = size.stock if size is not None else product.stock
    if available < quantity:
        raise ValidationError({"quantity": f"Only {available} left in stock."})

    line, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size=size,
        defaults={"quantity": quantity},
    )
    if not created:
        line.quantity += quantity
    line.save()
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
        return None
    line.quantity = quantity
    line.save()
    return line


def remove_line(request, line_id: int) -> None:
    cart = get_cart(request)
    if cart is not None:
        cart.lines.filter(pk=line_id).delete()


def apply_coupon(request, code: str) -> Cart:
    """Apply a coupon code.

    The demo ships one code; anything else clears the discount.  Real coupon
    rules would live here.
    """
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
def place_order(request, *, full_name, email, phone, address_line, city,
                region="", postal_code="", country="USA", note="",
                payment_method=Order.PaymentMethod.COD) -> Order:
    """Turn the visitor's basket into an order.

    Stock is decremented and the basket emptied in the same transaction, so
    a failure leaves nothing half-done.  No payment is attempted — the order
    simply appears in the admin queue.
    """
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
        # Take the stock off the shelf while we still hold the row lock.
        if line.size_id and line.size:
            line.size.stock = max(line.size.stock - line.quantity, 0)
            line.size.save(update_fields=["stock", "updated_at"])
        line.product.stock = max(line.product.stock - line.quantity, 0)
        line.product.save(update_fields=["stock", "updated_at"])

    cart.clear()
    return order


def collect_stale_carts() -> int:
    """Delete anonymous baskets older than the retention window."""
    from django.conf import settings

    cutoff = timezone.now() - timezone.timedelta(days=settings.CART_SESSION_DAYS)
    deleted, _ = Cart.objects.filter(user__isnull=True, updated_at__lt=cutoff).delete()
    return deleted

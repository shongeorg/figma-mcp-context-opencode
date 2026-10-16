"""Cart and orders.

There is deliberately **no payment integration**: a visitor submits an order,
it lands in the admin as a request, and a human confirms, ships or cancels it.
``Order.payment_method`` only records what the mockup *offers*, it never
charges a card.
"""

from __future__ import annotations

import secrets
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.models import TimeStampedModel


# ---------------------------------------------------------------- managers --

class OrderQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status=Order.Status.NEW)

    def for_user(self, user):
        if user.is_authenticated:
            return self.filter(user=user)
        return self.none()


# ------------------------------------------------------------------ models --

class Cart(TimeStampedModel):
    """A basket, either tied to a signed-in user or to an anonymous session.

    Exactly one of the two keys is set. Anonymous carts are collected once
    they are older than ``settings.CART_SESSION_DAYS``.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart",
    )
    session_key = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    coupon_code = models.CharField(max_length=40, blank=True)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        verbose_name = "cart"
        verbose_name_plural = "carts"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, session_key__isnull=True)
                    | models.Q(user__isnull=True, session_key__isnull=False)
                ),
                name="cart_has_user_xor_session",
            )
        ]

    def __str__(self) -> str:
        owner = self.user or f"session {self.session_key[:8]}"
        return f"Cart of {owner} ({self.item_count} items)"

    @classmethod
    def new_session_key(cls) -> str:
        return secrets.token_urlsafe(32)[:64]

    # -- line maths --------------------------------------------------------

    @property
    def items(self):
        return self.lines.select_related("product", "size").filter(is_active=True)

    @property
    def item_count(self) -> int:
        return sum(line.quantity for line in self.items)

    @property
    def subtotal(self):
        return sum((line.line_total for line in self.items), Decimal("0.00"))

    @property
    def discount(self):
        if self.coupon_discount:
            return min(self.coupon_discount, self.subtotal)
        return Decimal("0.00")

    @property
    def total(self):
        return max(self.subtotal - self.discount, Decimal("0.00"))

    @property
    def is_empty(self) -> bool:
        return self.item_count == 0

    def clear(self):
        self.lines.all().delete()
        self.coupon_code = ""
        self.coupon_discount = Decimal("0.00")
        self.save(update_fields=["coupon_code", "coupon_discount", "updated_at"])


class CartItem(TimeStampedModel):
    """One line in the basket: a product, optionally in a specific size."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="cart_lines"
    )
    size = models.ForeignKey(
        "catalog.ProductSize", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="cart_lines",
    )
    quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "cart item"
        verbose_name_plural = "cart items"
        constraints = [
            models.UniqueConstraint(
                fields=("cart", "product", "size"), name="unique_cart_line"
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1), name="cart_item_quantity_positive"
            ),
        ]

    def __str__(self) -> str:
        suffix = f" / {self.size.size.name}" if self.size_id and self.size else ""
        return f"{self.quantity} × {self.product.name}{suffix}"

    @property
    def unit_price(self):
        return self.size.price if self.size_id and self.size else self.product.price

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def size_label(self) -> str:
        return self.size.size.name if self.size_id and self.size else ""

    def clean(self):
        if self.quantity < 1:
            raise ValidationError({"quantity": "Quantity must be at least 1."})
        available = self.size.stock if self.size_id and self.size else self.product.stock
        if self.quantity > available:
            raise ValidationError(
                {"quantity": f"Only {available} left in stock."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Order(TimeStampedModel):
    """A submitted order — the admin's "order request" queue."""

    class Status(models.TextChoices):
        NEW = "new", "New"                 # just submitted, awaiting review
        CONFIRMED = "confirmed", "Confirmed"
        PACKING = "packing", "Packing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentMethod(models.TextChoices):
        CARD = "card", "Credit card"
        BANK = "bank", "Direct bank transfer"
        COD = "cod", "Cash on delivery"

    number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    # Contact details are copied onto the order so an order survives account
    # deletion and so an admin can read it without following FKs.
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)

    # Delivery snapshot — normally filled from Address.one_line at checkout.
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    region = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=16, blank=True)
    country = models.CharField(max_length=80, default="USA")
    note = models.TextField(blank=True)

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.NEW, db_index=True
    )
    payment_method = models.CharField(
        max_length=16,
        choices=PaymentMethod.choices,
        default=PaymentMethod.COD,
    )
    # Set by an admin once the money has actually been taken care of.
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    coupon_code = models.CharField(max_length=40, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    processed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)

    objects = OrderQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "order"
        verbose_name_plural = "orders"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["is_paid", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Order {self.number}"

    def get_absolute_url(self):
        return reverse("orders:detail", args=[self.number])

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_number(cls) -> str:
        """GS-YYMMDD-XXXX, unique and short enough to read out over a phone."""
        today = timezone.localdate().strftime("%y%m%d")
        for _ in range(50):
            candidate = f"GS-{today}-{secrets.token_hex(2).upper()}"
            if not cls.objects.filter(number=candidate).exists():
                return candidate
        raise RuntimeError("Could not allocate a unique order number")

    @property
    def delivery_address(self) -> str:
        parts = [self.address_line, self.city, self.region, self.postal_code, self.country]
        return ", ".join(p for p in parts if p)

    @property
    def is_pending(self) -> bool:
        return self.status == self.Status.NEW

    @property
    def status_class(self) -> str:
        """Bootstrap-ish badge class used by the templates."""
        return {
            self.Status.NEW: "warning",
            self.Status.CONFIRMED: "info",
            self.Status.PACKING: "info",
            self.Status.SHIPPED: "primary",
            self.Status.DELIVERED: "success",
            self.Status.CANCELLED: "danger",
        }.get(self.status, "secondary")

    def mark_paid(self):
        self.is_paid = True
        self.paid_at = timezone.now()
        self.save(update_fields=["is_paid", "paid_at", "updated_at"])

    def transition(self, new_status: str):
        """Move the order along, stamping the matching timestamp."""
        self.status = new_status
        fields = ["status", "updated_at"]
        now = timezone.now()
        if new_status == self.Status.CONFIRMED and not self.processed_at:
            self.processed_at = now
            fields.append("processed_at")
        if new_status == self.Status.SHIPPED and not self.shipped_at:
            self.shipped_at = now
            fields.append("shipped_at")
        self.save(update_fields=fields)


class OrderItem(models.Model):
    """A frozen copy of a cart line at the moment the order was placed."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.SET_NULL, null=True, related_name="order_items"
    )
    # Snapshots keep the invoice readable even if the product is renamed,
    # repriced or deleted later.
    product_name = models.CharField(max_length=160)
    product_slug = models.CharField(max_length=180, blank=True)
    size_name = models.CharField(max_length=24, blank=True)
    sku = models.CharField(max_length=40, blank=True)
    image_url = models.CharField(max_length=255, blank=True)

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    line_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ("pk",)
        verbose_name = "order item"
        verbose_name_plural = "order items"

    def __str__(self) -> str:
        suffix = f" / {self.size_name}" if self.size_name else ""
        return f"{self.quantity} × {self.product_name}{suffix}"

    @classmethod
    def from_cart_line(cls, order: Order, line: CartItem) -> "OrderItem":
        size = line.size if line.size_id else None
        return cls.objects.create(
            order=order,
            product=line.product,
            product_name=line.product.name,
            product_slug=line.product.slug,
            size_name=size.size.name if size else "",
            sku=line.product.sku,
            image_url=line.product.image_url,
            quantity=line.quantity,
            unit_price=line.unit_price,
            line_total=line.line_total,
        )

"""Orders admin — the manual "order request" queue.

There is no payment gateway: a visitor submits an order, it lands here with
status *New*, and a human confirms it, marks the money as received, ships it
or cancels it.
"""

from __future__ import annotations

from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html

from .models import Cart, CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ("image", "product_name", "size_name", "sku", "quantity", "unit_price", "line_total")
    readonly_fields = fields
    classes = ("collapse",)

    @admin.display(description="")
    def image(self, obj):
        if not obj.image_url:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="height:32px;width:32px;object-fit:contain">',
            obj.image_url,
        )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "number", "status_badge", "full_name", "city", "total_col",
        "payment_method", "is_paid", "created_at",
    )
    list_filter = ("status", "payment_method", "is_paid", "created_at")
    search_fields = ("number", "full_name", "email", "phone", "city", "address_line")
    readonly_fields = (
        "number", "user", "subtotal", "discount", "shipping", "total",
        "coupon_code", "created_at", "updated_at",
    )
    inlines = (OrderItemInline,)
    date_hierarchy = "created_at"
    list_per_page = 25
    save_on_top = True
    fieldsets = (
        ("Order", {
            "fields": (("number", "status"), ("created_at", "processed_at"), "shipped_at"),
        }),
        ("Customer", {
            "fields": (("full_name", "email", "phone"), "user"),
        }),
        ("Delivery", {
            "fields": ("address_line", ("city", "region"), ("postal_code", "country"), "note"),
        }),
        ("Payment", {
            "fields": (("payment_method", "is_paid", "paid_at"),),
            "description": "No gateway is wired up — record the outcome here by hand.",
        }),
        ("Totals", {
            "fields": (("subtotal", "discount", "shipping", "total"), "coupon_code"),
        }),
    )
    actions = (
        "confirm_orders", "mark_packing", "mark_shipped",
        "mark_delivered", "cancel_orders", "mark_paid",
    )

    # -- presentation ------------------------------------------------------

    @admin.display(description="status", ordering="status")
    def status_badge(self, obj):
        colours = {
            Order.Status.NEW: "#f0ad4e",
            Order.Status.CONFIRMED: "#5bc0de",
            Order.Status.PACKING: "#5bc0de",
            Order.Status.SHIPPED: "#46a358",
            Order.Status.DELIVERED: "#2f7d32",
            Order.Status.CANCELLED: "#d9534f",
        }
        colour = colours.get(obj.status, "#727272")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;'
            'font-size:11px;font-weight:600">{}</span>',
            colour, obj.get_status_display(),
        )

    @admin.display(description="total", ordering="total")
    def total_col(self, obj):
        # Pre-format: format_html() escapes its arguments into SafeStrings,
        # which then refuse the `,.2f` format spec.
        total = f"${obj.total:,.2f}"
        if obj.discount:
            return format_html(
                '<strong>{}</strong> <small style="color:#46a358">−{}</small>',
                total, f"${obj.discount:,.2f}",
            )
        return format_html("<strong>{}</strong>", total)

    @admin.display(description="paid", boolean=True)
    def paid_flag(self, obj):
        return obj.is_paid

    # -- workflow actions --------------------------------------------------

    @admin.action(description="Confirm selected orders")
    def confirm_orders(self, request, queryset):
        updated = queryset.filter(status=Order.Status.NEW).update(
            status=Order.Status.CONFIRMED,
            processed_at=timezone.now(),
            updated_at=timezone.now(),
        )
        self.message_user(request, f"{updated} orders confirmed.", messages.SUCCESS)

    @admin.action(description="Mark selected orders as packing")
    def mark_packing(self, request, queryset):
        updated = queryset.exclude(
            status__in=[Order.Status.SHIPPED, Order.Status.DELIVERED, Order.Status.CANCELLED]
        ).update(status=Order.Status.PACKING, updated_at=timezone.now())
        self.message_user(request, f"{updated} orders moved to packing.", messages.SUCCESS)

    @admin.action(description="Mark selected orders as shipped")
    def mark_shipped(self, request, queryset):
        updated = queryset.exclude(
            status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED]
        ).update(status=Order.Status.SHIPPED, shipped_at=timezone.now(), updated_at=timezone.now())
        self.message_user(request, f"{updated} orders marked as shipped.", messages.SUCCESS)

    @admin.action(description="Mark selected orders as delivered")
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status=Order.Status.DELIVERED, updated_at=timezone.now())
        self.message_user(request, f"{updated} orders delivered.", messages.SUCCESS)

    @admin.action(description="Cancel selected orders")
    def cancel_orders(self, request, queryset):
        updated = queryset.update(status=Order.Status.CANCELLED, updated_at=timezone.now())
        self.message_user(request, f"{updated} orders cancelled.", messages.WARNING)

    @admin.action(description="Mark selected orders as paid")
    def mark_paid(self, request, queryset):
        updated = queryset.update(is_paid=True, paid_at=timezone.now(), updated_at=timezone.now())
        self.message_user(
            request, f"{updated} orders marked as paid (manual, no gateway).", messages.SUCCESS
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("product", "size", "quantity", "line_total", "is_active")
    readonly_fields = ("line_total",)
    autocomplete_fields = ("product",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("owner", "item_count", "subtotal_col", "coupon_code", "updated_at")
    list_filter = ("coupon_code",)
    search_fields = ("user__username", "user__email", "session_key", "coupon_code")
    readonly_fields = ("created_at", "updated_at")
    inlines = (CartItemInline,)
    date_hierarchy = "updated_at"

    @admin.display(description="owner")
    def owner(self, obj):
        if obj.user:
            return f"{obj.user} (user)"
        return format_html("<code>session {}…</code>", (obj.session_key or "")[:8])

    @admin.display(description="subtotal")
    def subtotal_col(self, obj):
        return f"${obj.subtotal:,.2f}"

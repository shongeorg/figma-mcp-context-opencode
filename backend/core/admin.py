"""Accounts admin: users, addresses, newsletter subscribers."""

from __future__ import annotations

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import Address, Subscriber, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "full_name", "role", "is_active", "date_joined", "order_count")
    list_filter = ("role", "is_active", "is_superuser")
    search_fields = ("username", "first_name", "last_name", "email", "phone")
    list_editable = ("role", "is_active")
    list_per_page = 50
    ordering = ("-date_joined",)
    date_hierarchy = "date_joined"
    fieldsets = BaseUserAdmin.fieldsets + (
        ("GreenShop", {"fields": ("role", "phone", "avatar")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("GreenShop", {"fields": ("role", "email", "phone")}),
    )
    actions = ("make_admin", "make_client")

    @admin.display(description="name")
    def full_name(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description="orders")
    def order_count(self, obj):
        return obj.orders.count()

    @admin.action(description="Turn selected users into admins")
    def make_admin(self, request, queryset):
        updated = queryset.update(role=User.Role.ADMIN, is_staff=True)
        self.message_user(request, f"{updated} users are now admins.", messages.SUCCESS)

    @admin.action(description="Turn selected users into clients")
    def make_client(self, request, queryset):
        updated = queryset.filter(is_superuser=False).update(
            role=User.Role.CLIENT, is_staff=False
        )
        self.message_user(
            request, f"{updated} users are now clients.", messages.WARNING
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("avatar")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "full_name", "city", "country", "is_default", "created_at")
    list_filter = ("label", "country", "is_default")
    search_fields = ("user__username", "user__email", "full_name", "city", "line1", "line2")
    list_editable = ("is_default",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("email",)
    list_editable = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    actions = ("activate", "deactivate")

    @admin.display(description="subscribed")
    def subscribed_since(self, obj):
        return format_html("<small>{}</small>", obj.created_at.strftime("%d %b %Y"))

    @admin.action(description="Activate selected subscribers")
    def activate(self, request, queryset):
        self.message_user(
            request, f"{queryset.update(is_active=True)} subscribers activated.", messages.SUCCESS
        )

    @admin.action(description="Deactivate selected subscribers")
    def deactivate(self, request, queryset):
        self.message_user(
            request, f"{queryset.update(is_active=False)} subscribers deactivated.",
            messages.WARNING,
        )

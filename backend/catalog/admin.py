"""Catalogue admin: categories (with subcategories), products, tags, sizes."""

from __future__ import annotations

from django.contrib import admin, messages
from django.utils.html import format_html, mark_safe

from . import services
from .models import (
    Category,
    Product,
    ProductImage,
    ProductSize,
    Review,
    Size,
    Tag,
    Wishlist,
)


# ---------------------------------------------------------------- helpers --

class TreeOrderingFilter(admin.SimpleListFilter):
    """Filter products by the category they sit in, subtree included."""

    title = "category"
    parameter_name = "category"

    def lookups(self, request, model_admin):
        return [(c.pk, f"{c.name} ({c.product_count})") for c in Category.objects.all()]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        try:
            category = Category.objects.get(pk=self.value())
        except Category.DoesNotExist:
            return queryset.none()
        return queryset.in_category(category)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "preview", "alt", "is_primary", "ordering")
    readonly_fields = ("preview",)
    ordering = ("-is_primary", "ordering")

    @admin.display(description="preview")
    def preview(self, obj):
        if not obj or not obj.image:
            return "—"
        return format_html(
            '<img src="{}" alt="{}" style="height:48px;width:auto;border-radius:4px">',
            obj.image.url,
            obj.alt or obj.product.name,
        )


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 4
    autocomplete_fields = ("size",)
    fields = ("size", "price_delta", "stock", "is_active")


# ------------------------------------------------------------- categories --

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "depth_badge", "product_count_col", "is_active", "ordering")
    list_filter = ("is_active", "parent")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("ordering", "is_active")
    list_per_page = 50
    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "description", "image")}),
        ("Display", {"fields": ("is_active", "ordering")}),
    )
    actions = ("activate", "deactivate")

    @admin.display(description="level", ordering="parent")
    def depth_badge(self, obj):
        if obj.depth == 0:
            # Constant markup — format_html() needs at least one argument.
            return mark_safe('<span style="color:#46a358;font-weight:600">root</span>')
        indent = "&nbsp;" * (obj.depth * 3)
        return format_html(
            '<span style="color:#727272">└ {}level {}</span>', indent, obj.depth
        )

    @admin.display(description="products")
    def product_count_col(self, obj):
        return obj.product_count

    @admin.action(description="Activate selected categories")
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} categories activated.", messages.SUCCESS)

    @admin.action(description="Deactivate selected categories")
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} categories deactivated.", messages.SUCCESS)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("parent")


# ---------------------------------------------------------------- product --

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "thumb", "name", "sku", "category", "price_col", "stock",
        "is_active", "is_featured", "is_new", "rating", "reviews_count",
    )
    list_filter = (TreeOrderingFilter, "is_active", "is_featured", "is_new", "tags")
    search_fields = ("name", "slug", "sku", "short_description", "description")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category", "tags")
    inlines = (ProductImageInline, ProductSizeInline)
    list_editable = ("is_active", "is_featured", "is_new")
    list_per_page = 25
    readonly_fields = ("rating", "reviews_count", "created_at", "updated_at")
    date_hierarchy = "created_at"
    save_on_top = True
    fieldsets = (
        ("Identity", {"fields": ("name", "slug", "sku", "category", "tags")}),
        ("Description", {
            "classes": ("collapse",),
            "fields": ("short_description", "description"),
        }),
        ("Pricing", {"fields": (("price", "old_price"), ("stock",))}),
        ("Flags", {"fields": (("is_active", "is_featured", "is_new"), "ordering")}),
        ("Review summary", {
            "classes": ("collapse",),
            "fields": (("rating", "reviews_count"), ("created_at", "updated_at")),
        }),
    )
    actions = ("activate", "deactivate", "mark_featured", "clear_featured", "recalculate_ratings")

    @admin.display(description="price")
    def price_col(self, obj):
        # Format the numbers first: format_html() escapes its arguments, and
        # a SafeString refuses to accept `,.2f`.
        price = f"${obj.price:,.2f}"
        if obj.is_on_sale:
            return format_html(
                '<span style="color:#46a358;font-weight:600">{}</span> '
                '<s style="color:#a5a5a5">{}</s> <small>−{}%</small>',
                price, f"${obj.old_price:,.2f}", obj.discount_percent,
            )
        return price

    @admin.display(description="image", ordering="name")
    def thumb(self, obj):
        image = obj.primary_image
        if not image:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="height:36px;width:36px;object-fit:contain">',
            image.image.url,
        )

    @admin.action(description="Activate selected products")
    def activate(self, request, queryset):
        self.message_user(
            request, f"{queryset.update(is_active=True)} products activated.", messages.SUCCESS
        )

    @admin.action(description="Deactivate selected products")
    def deactivate(self, request, queryset):
        self.message_user(
            request, f"{queryset.update(is_active=False)} products deactivated.", messages.SUCCESS
        )

    @admin.action(description="Mark as featured")
    def mark_featured(self, request, queryset):
        self.message_user(
            request, f"{queryset.update(is_featured=True)} products featured.", messages.SUCCESS
        )

    @admin.action(description="Clear featured flag")
    def clear_featured(self, request, queryset):
        self.message_user(
            request, f"{queryset.update(is_featured=False)} products unfeatured.", messages.SUCCESS
        )

    @admin.action(description="Recalculate ratings from approved reviews")
    def recalculate_ratings(self, request, queryset):
        for product in queryset:
            services.refresh_product_rating(product.pk)
        self.message_user(request, "Ratings recalculated.", messages.SUCCESS)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category").prefetch_related("images")


# ------------------------------------------------------- tags / sizes ------

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "product_count")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_active",)

    @admin.display(description="products")
    def product_count(self, obj):
        return obj.products.count()


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "ordering", "product_count")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("ordering",)

    @admin.display(description="products")
    def product_count(self, obj):
        return obj.products.count()


# ------------------------------------------------------------- reviews -----

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating_col", "is_approved", "created_at", "title")
    list_filter = ("is_approved", "rating")
    search_fields = ("product__name", "user__username", "user__email", "title", "body")
    list_editable = ("is_approved",)
    readonly_fields = ("product", "user", "rating", "title", "body", "created_at", "updated_at")
    date_hierarchy = "created_at"
    actions = ("approve", "unapprove")

    @admin.display(description="rating")
    def rating_col(self, obj):
        filled = "★" * obj.rating
        empty = "☆" * (5 - obj.rating)
        return format_html(
            '<span style="color:#46a358">{}</span><span style="color:#c9c9c9">{}</span> {}',
            filled, empty, obj.rating,
        )

    @admin.action(description="Approve selected reviews")
    def approve(self, request, queryset):
        for review in queryset:
            services.approve_review(review)
        self.message_user(request, f"{queryset.count()} reviews approved.", messages.SUCCESS)

    @admin.action(description="Unapprove selected reviews")
    def unapprove(self, request, queryset):
        for review in queryset:
            review.is_approved = False
            review.save(update_fields=["is_approved", "updated_at"])
            services.refresh_product_rating(review.product_id)
        self.message_user(request, f"{queryset.count()} reviews unapproved.", messages.WARNING)


# ------------------------------------------------------------ wishlist -----

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    search_fields = ("user__username", "user__email", "product__name")
    readonly_fields = ("user", "product", "created_at")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

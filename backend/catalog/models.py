"""Catalogue: categories (with subcategories), products, sizes, tags, reviews."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from core.models import TimeStampedModel
from core.utils import unique_slugify


# ---------------------------------------------------------------- managers --

class ProductQuerySet(models.QuerySet):
    """Every storefront filter the shop needs, in one place."""

    def active(self):
        return self.filter(is_active=True)

    def on_sale(self):
        return self.filter(old_price__gt=models.F("price"), is_active=True)

    def featured(self):
        return self.filter(is_featured=True, is_active=True)

    def new_arrivals(self):
        return self.filter(is_new=True, is_active=True)

    def in_stock(self):
        return self.filter(stock__gt=0)

    def in_category(self, category):
        """Include the whole subtree, not just the direct children."""
        if category is None:
            return self
        ids = [category.pk]
        ids += list(category.get_descendants_ids())
        return self.filter(category_id__in=ids)

    def search(self, query):
        if not query:
            return self
        return self.filter(
            models.Q(name__icontains=query)
            | models.Q(short_description__icontains=query)
            | models.Q(description__icontains=query)
            | models.Q(category__name__icontains=query)
        )


class CategoryQuerySet(models.QuerySet):
    def roots(self):
        return self.filter(parent__isnull=True)


# ------------------------------------------------------------------ models --

class Category(TimeStampedModel):
    """A category tree node.

    ``parent`` being ``NULL`` marks a top-level category. The storefront
    shows category product counts in the mockup (House Plants 33, Potter
    Plants 12 …), and those counts include the whole subtree.
    """

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, allow_unicode=False)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0, db_index=True)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        ordering = ("ordering", "name")
        verbose_name = "category"
        verbose_name_plural = "categories"
        indexes = [models.Index(fields=["parent", "ordering"])]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:category", args=[self.slug])

    def save(self, *args, **kwargs):
        # ЧПУ for categories too — a subcategory slug is globally unique, so
        # "Seeds" and "Small Plants" never collide even under different parents.
        if not self.slug:
            self.slug = unique_slugify(self, self.name, max_length=140)
        if self.parent_id and self.parent_id == self.pk:
            self.parent = None
        super().save(*args, **kwargs)

    # -- tree helpers ------------------------------------------------------

    def get_descendants(self):
        """All nested categories below this one, breadth-first."""
        result = []
        frontier = [self]
        seen = {self.pk}
        while frontier:
            node = frontier.pop(0)
            for child in node.children.all():
                if child.pk not in seen:
                    seen.add(child.pk)
                    result.append(child)
                    frontier.append(child)
        return result

    def get_descendants_ids(self):
        return [c.pk for c in self.get_descendants()]

    def get_family_ids(self):
        """Self plus every descendant — what the product counts are built on."""
        return [self.pk] + self.get_descendants_ids()

    def get_products(self):
        return Product.objects.active().in_category(self)

    @property
    def product_count(self):
        """Cached by the view; computed here so the template stays dumb."""
        cached = getattr(self, "_product_count", None)
        if cached is None:
            cached = Product.objects.active().in_category(self).count()
            self._product_count = cached
        return cached

    @property
    def breadcrumbs(self):
        """Root → self, for the "Shop → House Plants" trail."""
        chain = []
        node = self
        while node is not None:
            chain.append(node)
            node = node.parent
        return list(reversed(chain))

    @property
    def depth(self):
        return len(self.breadcrumbs) - 1


class Tag(TimeStampedModel):
    """Free-form labels shown as the shop's tag cloud."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "tag"
        verbose_name_plural = "tags"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, max_length=80)
        super().save(*args, **kwargs)


class Product(TimeStampedModel):
    """A single plant in the shop."""

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")

    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    sku = models.CharField(max_length=40, unique=True, blank=True)

    short_description = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    # When set and above `price`, the shop shows "N% OFF" — exactly how the
    # mockup renders African Violet at $199.00 (was $229.00, 13% OFF).
    old_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)

    # Denormalised review summary, refreshed by `catalog.reviews`.
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    reviews_count = models.PositiveIntegerField(default=0)

    ordering = models.PositiveIntegerField(default=0, db_index=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ("ordering", "-created_at")
        verbose_name = "product"
        verbose_name_plural = "products"
        indexes = [
            models.Index(fields=["is_active", "ordering"]),
            models.Index(fields=["category", "is_active"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(old_price__isnull=True)
                | models.Q(old_price__gt=models.F("price")),
                name="product_old_price_above_price",
            )
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:product", args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, max_length=180)
        if not self.sku:
            base = (self.slug or "item").upper().replace("-", "")[:12]
            sku, n = base, 2
            while Product.objects.filter(sku=sku).exclude(pk=self.pk).exists():
                sku = f"{base}-{n}"
                n += 1
            self.sku = sku
        # Guard the "was $X" display rule at the model level too.
        if self.old_price is not None and self.old_price <= self.price:
            self.old_price = None
        super().save(*args, **kwargs)

    # -- display helpers ---------------------------------------------------

    @property
    def is_on_sale(self) -> bool:
        return self.old_price is not None and self.old_price > self.price

    @property
    def discount_percent(self) -> int | None:
        if not self.is_on_sale:
            return None
        saved = self.old_price - self.price
        return int(round(saved / self.old_price * 100))

    @property
    def primary_image(self):
        image = getattr(self, "_primary_image", None)
        if image is None:
            image = self.images.filter(is_primary=True).first() or self.images.first()
            self._primary_image = image
        return image

    @property
    def image_url(self) -> str:
        image = self.primary_image
        return image.image.url if image else ""

    def get_sizes(self):
        return self.sizes.select_related("size").filter(is_active=True)


class ProductImage(TimeStampedModel):
    """Extra product shots. The first `is_primary` row is the grid tile."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt = models.CharField(max_length=160, blank=True)
    is_primary = models.BooleanField(default=False)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-is_primary", "ordering", "pk")
        verbose_name = "product image"
        verbose_name_plural = "product images"
        indexes = [models.Index(fields=["product", "-is_primary", "ordering"])]

    def __str__(self) -> str:
        return self.alt or f"{self.product.name} image"

    def save(self, *args, **kwargs):
        if not self.alt:
            self.alt = self.product.name
        super().save(*args, **kwargs)


class Size(TimeStampedModel):
    """S / M / L / XL — the plant sizes the mockup offers on every product."""

    name = models.CharField(max_length=24, unique=True)
    slug = models.SlugField(max_length=32, unique=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("ordering", "name")
        verbose_name = "size"
        verbose_name_plural = "sizes"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, max_length=32)
        super().save(*args, **kwargs)


class ProductSize(TimeStampedModel):
    """Which sizes a product is sold in, and at what delta."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name="products")
    # Added to the product price for this size (a big pot costs more).
    price_delta = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("size__ordering", "size__name")
        verbose_name = "product size"
        verbose_name_plural = "product sizes"
        constraints = [
            models.UniqueConstraint(
                fields=("product", "size"), name="unique_product_size"
            )
        ]

    def __str__(self) -> str:
        return f"{self.product.name} — {self.size.name}"

    @property
    def price(self):
        return self.product.price + self.price_delta


class Review(TimeStampedModel):
    """A customer review. Pending until an admin approves it."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "review"
        verbose_name_plural = "reviews"
        constraints = [
            models.UniqueConstraint(
                fields=("product", "user"), name="one_review_per_user_per_product"
            )
        ]
        indexes = [models.Index(fields=["product", "is_approved", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.user} — {self.product.name} ({self.rating}★)"

    @property
    def stars(self) -> list[int]:
        return list(range(1, 6))

    @property
    def filled_stars(self) -> list[int]:
        return list(range(1, self.rating + 1))


class Wishlist(TimeStampedModel):
    """The heart icon in the mockup's header and product cards."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "wishlist entry"
        verbose_name_plural = "wishlist"
        constraints = [
            models.UniqueConstraint(fields=("user", "product"), name="unique_wishlist_row")
        ]

    def __str__(self) -> str:
        return f"{self.user} ♥ {self.product.name}"

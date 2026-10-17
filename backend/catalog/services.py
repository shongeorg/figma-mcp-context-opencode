from __future__ import annotations

from decimal import Decimal

from django.core.cache import cache
from django.db import connection, transaction
from django.db.models import Avg, Count

from .models import Category, Product, Review, Size, Tag, Wishlist

_SQL_CATEGORY_COUNTS = """
WITH RECURSIVE tree AS (
    SELECT id, id AS root_id
      FROM catalog_category
     WHERE is_active
    UNION ALL
    SELECT child.id, tree.root_id
      FROM catalog_category child
      JOIN tree ON child.parent_id = tree.id
)
SELECT tree.root_id, COUNT(DISTINCT product.id)
  FROM tree
  JOIN catalog_product product
    ON product.category_id = tree.id
   AND product.is_active
 GROUP BY tree.root_id
"""

_SQL_SIZE_COUNTS = """
SELECT product_size.size_id, COUNT(DISTINCT product.id)
  FROM catalog_product product
  JOIN catalog_productsize product_size ON product_size.product_id = product.id
 WHERE product.is_active
 GROUP BY product_size.size_id
"""

SIDEBAR_CACHE_KEY = "greenshop:sidebar-counts:v1"
NAV_CACHE_KEY = "greenshop:nav-categories:v1"
FAMILY_CACHE_KEY = "greenshop:category-families:v1"
SIZE_CACHE_KEY = "greenshop:sizes:v1"
TAG_CACHE_KEY = "greenshop:tags:v1"
SIDEBAR_CACHE_SECONDS = 600


def invalidate_catalog_cache() -> None:
    cache.delete_many(
        [SIDEBAR_CACHE_KEY, NAV_CACHE_KEY, FAMILY_CACHE_KEY, SIZE_CACHE_KEY, TAG_CACHE_KEY]
    )


def _uncached_sidebar_counts() -> dict:
    categories: dict[int, int] = {}
    sizes: dict[int, int] = {}

    with connection.cursor() as cursor:
        cursor.execute(_SQL_CATEGORY_COUNTS)
        for pk, count in cursor.fetchall():
            categories[pk] = count

        cursor.execute(_SQL_SIZE_COUNTS)
        for pk, count in cursor.fetchall():
            sizes[pk] = count

    return {"categories": categories, "sizes": sizes}


def _uncached_family_map() -> dict[int, list[int]]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, parent_id FROM catalog_category")
        rows = cursor.fetchall()

    children: dict[int, list[int]] = {}
    for pk, parent in rows:
        children.setdefault(parent, []).append(pk)

    family: dict[int, list[int]] = {}

    def walk(pk: int, chain: tuple = ()) -> list[int]:
        if pk in family:
            return family[pk]
        if pk in chain:
            return []
        chain = (*chain, pk)
        acc = [pk]
        for child in children.get(pk, ()):
            acc.extend(walk(child, chain))
        family[pk] = acc
        return acc

    for pk, _parent in rows:
        walk(pk)
    return family


def family_ids(category: Category) -> list[int]:
    cached = cache.get(FAMILY_CACHE_KEY)
    if cached is None:
        cached = _uncached_family_map()
        cache.set(FAMILY_CACHE_KEY, cached, SIDEBAR_CACHE_SECONDS)
    family = cached.get(category.pk)
    if family is None:
        return [category.pk]
    return list(family)


def nav_categories_cached() -> list:
    cached = cache.get(NAV_CACHE_KEY)
    if cached is None:
        cached = list(
            Category.objects.filter(is_active=True, parent__isnull=True)
            .prefetch_related("children")
            .order_by("ordering", "name")
        )
        cache.set(NAV_CACHE_KEY, cached, SIDEBAR_CACHE_SECONDS)
    return cached


def sizes_cached() -> list:
    cached = cache.get(SIZE_CACHE_KEY)
    if cached is None:
        cached = list(Size.objects.order_by("ordering", "name"))
        cache.set(SIZE_CACHE_KEY, cached, SIDEBAR_CACHE_SECONDS)
    return cached


def tags_cached() -> list:
    cached = cache.get(TAG_CACHE_KEY)
    if cached is None:
        cached = list(Tag.objects.filter(is_active=True).order_by("name"))
        cache.set(TAG_CACHE_KEY, cached, SIDEBAR_CACHE_SECONDS)
    return cached


def sidebar_counts() -> dict:
    cached = cache.get(SIDEBAR_CACHE_KEY)
    if cached is None:
        cached = _uncached_sidebar_counts()
        cache.set(SIDEBAR_CACHE_KEY, cached, SIDEBAR_CACHE_SECONDS)
    return cached


def category_row_tree() -> list[dict]:
    counts = sidebar_counts()["categories"]
    rows = []
    for root in nav_categories_cached():
        rows.append({
            "category": root,
            "count": counts.get(root.pk, 0),
            "children": [
                {"category": child, "count": counts.get(child.pk, 0)}
                for child in root.children.all()
                if child.is_active
            ],
        })
    return rows


def refresh_product_rating(product_id: int) -> None:
    stats = (
        Review.objects.filter(product_id=product_id, is_approved=True)
        .aggregate(avg=Avg("rating"), total=Count("*"))
    )
    Product.objects.filter(pk=product_id).update(
        rating=Decimal(str(stats["avg"])).quantize(Decimal("0.01"))
        if stats["avg"] is not None
        else Decimal("0.00"),
        reviews_count=stats["total"] or 0,
    )


@transaction.atomic
def approve_review(review: Review) -> Review:
    review.is_approved = True
    review.save(update_fields=["is_approved", "updated_at"])
    refresh_product_rating(review.product_id)
    return review


def pending_review_count() -> int:
    return Review.objects.filter(is_approved=False).count()


def toggle_wishlist(user, product: Product) -> bool:
    entry = Wishlist.objects.filter(user=user, product=product).first()
    if entry is None:
        Wishlist.objects.create(user=user, product=product)
        return True
    entry.delete()
    return False


def is_wishlisted(user, product: Product) -> bool:
    if not user.is_authenticated:
        return False
    return Wishlist.objects.filter(user=user, product=product).exists()


def wishlist_ids(user) -> set:
    if not user.is_authenticated:
        return set()
    return set(Wishlist.objects.filter(user=user).values_list("product_id", flat=True))

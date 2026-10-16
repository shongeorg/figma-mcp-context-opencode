"""Catalogue behaviour: review scoring and the wishlist heart."""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Avg, Count

from .models import Product, Review, Wishlist


def refresh_product_rating(product_id: int) -> None:
    """Recompute the denormalised ``rating`` / ``reviews_count`` pair."""
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
    """Admin action: publish a review and rescore the product."""
    review.is_approved = True
    review.save(update_fields=["is_approved", "updated_at"])
    refresh_product_rating(review.product_id)
    return review


def pending_review_count() -> int:
    return Review.objects.filter(is_approved=False).count()


def toggle_wishlist(user, product: Product) -> bool:
    """Add/remove a product from a signed-in user's wishlist.

    Returns ``True`` when the product is now wishlisted.
    """
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

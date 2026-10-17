from __future__ import annotations

from django.conf import settings


def shop(request):
    from catalog.services import nav_categories_cached
    from orders.services import get_cart

    cart = get_cart(request)
    cart_count = cart.item_count if cart is not None else 0

    wishlist_count = 0
    if request.user.is_authenticated:
        wishlist_count = request.user.wishlist.count()

    return {
        "SITE_NAME": settings.SITE_NAME,
        "CURRENCY": settings.CURRENCY,
        "nav_categories": nav_categories_cached(),
        "cart_count": cart_count,
        "wishlist_count": wishlist_count,
        "products_per_page": settings.PRODUCTS_PER_PAGE,
    }

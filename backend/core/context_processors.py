"""Context available in every template without repeating the boilerplate."""

from __future__ import annotations

from django.conf import settings


def shop(request):
    """Site-wide values: branding, currency, nav tree, cart badge."""
    # Imported lazily: orders depends on core, so a module-level import here
    # would close the loop.
    from catalog.models import Category
    from orders.models import Cart

    categories = (
        Category.objects.filter(is_active=True, parent__isnull=True)
        .prefetch_related("children")
        .order_by("ordering", "name")
    )

    cart_count = 0
    wishlist_count = 0
    if getattr(request, "user", None) is not None and request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        cart_count = cart.item_count if cart else 0
        wishlist_count = request.user.wishlist.count()
    elif request.session.session_key:
        cart = Cart.objects.filter(session_key=request.session.session_key).first()
        cart_count = cart.item_count if cart else 0

    return {
        "SITE_NAME": settings.SITE_NAME,
        "CURRENCY": settings.CURRENCY,
        "nav_categories": categories,
        "cart_count": cart_count,
        "wishlist_count": wishlist_count,
        "products_per_page": settings.PRODUCTS_PER_PAGE,
    }

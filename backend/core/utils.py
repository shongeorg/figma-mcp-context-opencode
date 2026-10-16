"""Shared helpers for the GreenShop apps."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from django.utils.text import slugify

# Characters that are legal in a slug after Django's own slugify() has run.
_NON_SLUG = re.compile(r"[^a-z0-9-]+")


def ascii_slug(value: str, max_length: int = 200) -> str:
    """Build a URL-safe slug out of an arbitrary product or category name.

    ``django.utils.text.slugify`` is applied first, then anything that is not
    ``a-z 0-9 -`` is stripped, so that names such as ``Angel Wing Begonia``
    and ``Cera Pro`` produce stable, human-readable slugs.
    """
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    value = slugify(value, allow_unicode=False) or "item"
    value = _NON_SLUG.sub("-", value).strip("-")
    # Collapse the runs of dashes that stripping can leave behind.
    value = re.sub(r"-{2,}", "-", value)
    return value[:max_length].strip("-") or "item"


def unique_slugify(
    instance,
    value: str,
    slug_field: str = "slug",
    queryset=None,
    max_length: int = 200,
) -> str:
    """Return a slug for ``value`` that is unused within ``queryset``.

    ``queryset`` defaults to the model's own objects, excluding ``instance``
    itself so that editing a record does not rename it out from under its
    own canonical URL.

    Collisions get a numeric suffix, matching what the admin expects:
    ``barberton-daisy``, ``barberton-daisy-2``, ``barberton-daisy-3``.
    """
    model = instance.__class__
    if queryset is None:
        queryset = model._default_manager.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)

    base = ascii_slug(value, max_length=max_length - 6)
    candidate = base
    counter = 2

    while queryset.filter(**{slug_field: candidate}).exists():
        suffix = f"-{counter}"
        candidate = f"{base[: max_length - len(suffix)]}{suffix}"
        counter += 1

    return candidate


def money(value) -> str:
    """Format a decimal as the storefront does: ``$119.00``."""
    from django.conf import settings

    if value is None:
        return ""
    return f"{settings.CURRENCY}{value:,.2f}"


def product_image_names(product) -> Iterable[str]:
    """Alt texts for a product's images, used by the sitemap-ish helpers."""
    return (img.alt or product.name for img in product.images.all())

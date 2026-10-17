from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from django.utils.text import slugify

_NON_SLUG = re.compile(r"[^a-z0-9-]+")


def ascii_slug(value: str, max_length: int = 200) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    value = slugify(value, allow_unicode=False) or "item"
    value = _NON_SLUG.sub("-", value).strip("-")
    value = re.sub(r"-{2,}", "-", value)
    return value[:max_length].strip("-") or "item"


def unique_slugify(
    instance,
    value: str,
    slug_field: str = "slug",
    queryset=None,
    max_length: int = 200,
) -> str:
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
    from django.conf import settings

    if value is None:
        return ""
    return f"{settings.CURRENCY}{value:,.2f}"


def product_image_names(product) -> Iterable[str]:
    return (img.alt or product.name for img in product.images.all())

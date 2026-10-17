from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from . import services
from .models import Category, Product, ProductSize, Review, Size, Tag

CATALOGUE_MODELS = (Category, Product, ProductSize, Review, Size, Tag)


def _invalidate(sender, **kwargs) -> None:
    services.invalidate_catalog_cache()


for _model in CATALOGUE_MODELS:
    post_save.connect(
        _invalidate, sender=_model, dispatch_uid=f"greenshop.invalidate.{_model.__name__}.save"
    )
    post_delete.connect(
        _invalidate, sender=_model, dispatch_uid=f"greenshop.invalidate.{_model.__name__}.delete"
    )

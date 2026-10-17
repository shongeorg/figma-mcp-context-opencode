from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = "catalog"

    def ready(self) -> None:
        from . import receivers  # noqa: F401  (registers cache invalidation)

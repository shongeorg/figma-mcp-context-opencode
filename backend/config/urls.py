"""Root URL configuration.

Shop pages will be mounted at ``/`` by ``core.urls``; the Django admin sits
at ``/admin/`` and is the back office for products, categories and the
manual order queue.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "GreenShop administration"
admin.site.site_title = "GreenShop admin"
admin.site.index_title = "Catalogue, orders and customers"

urlpatterns = [
    path("admin/", admin.site.urls),
    # The three storefront apps each own their slice of the URL space, so
    # `shop/`, `product/<slug>/` and `cart/` sit flat under the site root.
    path("", include("core.urls")),
    path("", include("catalog.urls")),
    path("", include("orders.urls")),
]

if settings.DEBUG:
    # The dev server serves uploads; WhiteNoise handles the rest.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

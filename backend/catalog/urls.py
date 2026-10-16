"""Catalogue URLs: the shop grid, product detail, reviews and wishlist."""

from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("shop/", views.shop, name="shop"),
    path("shop/category/<slug:slug>/", views.category_detail, name="category"),
    path("product/<slug:slug>/", views.product_detail, name="product"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", views.wishlist_toggle, name="wishlist-toggle"),
    path("review/<int:product_id>/", views.add_review, name="add-review"),
]

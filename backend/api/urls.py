from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("products/", views.product_list, name="product-list"),
    path("products/<slug:slug>/", views.product_detail, name="product-detail"),
    path("categories/", views.category_tree, name="category-tree"),
    path("sizes/", views.size_list, name="size-list"),
    path("tags/", views.tag_list, name="tag-list"),
    path("blog/", views.blog_list, name="blog-list"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog-detail"),
    path("cart/", views.cart_detail, name="cart-detail"),
    path("cart/items/", views.cart_item_add, name="cart-item-add"),
    path("cart/items/<int:line_id>/", views.cart_item_detail, name="cart-item-detail"),
    path("cart/coupon/", views.cart_coupon, name="cart-coupon"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.order_list, name="order-list"),
    path("orders/<slug:number>/", views.order_detail, name="order-detail"),
    path("reviews/", views.review_list, name="review-list"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/<int:product_id>/", views.wishlist_remove, name="wishlist-remove"),
    path("auth/login/", views.auth_login, name="auth-login"),
    path("auth/logout/", views.auth_logout, name="auth-logout"),
    path("auth/me/", views.auth_me, name="auth-me"),
    path("newsletter/", views.newsletter_subscribe, name="newsletter"),
]

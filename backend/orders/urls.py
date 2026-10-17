from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add"),
    path("cart/update/<int:line_id>/", views.update_cart, name="update"),
    path("cart/remove/<int:line_id>/", views.remove_from_cart, name="remove"),
    path("cart/coupon/", views.apply_coupon, name="coupon"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.order_list, name="list"),
    path("orders/<slug:number>/", views.order_detail, name="detail"),
]

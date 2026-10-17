from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("account/", views.account, name="account"),
    path("account/addresses/", views.address_list, name="address-list"),
    path("account/addresses/add/", views.address_create, name="address-create"),
    path("account/addresses/<int:pk>/", views.address_update, name="address-detail"),
    path("account/addresses/<int:pk>/delete/", views.address_delete, name="address-delete"),
    path("subscribe/", views.subscribe, name="subscribe"),
]

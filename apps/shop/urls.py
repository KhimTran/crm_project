from django.urls import path

from . import views

app_name = "shop"
urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.products, name="products"),
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
]

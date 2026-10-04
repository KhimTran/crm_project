from django.urls import path
from . import views

app_name = "catalog_admin"
urlpatterns = [
    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers/create/", views.supplier_create, name="supplier_create"),
    path("suppliers/<int:supplier_id>/edit/", views.supplier_edit, name="supplier_edit"),
    path("suppliers/<int:supplier_id>/delete/", views.supplier_delete, name="supplier_delete"),
    path("products/", views.product_list, name="product_list"),
    path("products/create/", views.product_create, name="product_create"),
    path("products/<int:product_id>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:product_id>/delete/", views.product_delete, name="product_delete"),
]

from django.urls import path

from . import views

app_name = "customers"
urlpatterns = [
    path("", views.customer_list, name="list"),
    path("new/", views.customer_create, name="create"),
    path("<int:customer_id>/lock/", views.customer_lock, name="lock"),
    path("<int:customer_id>/unlock/", views.customer_unlock, name="unlock"),
    path("<int:customer_id>/delete/", views.customer_delete, name="delete"),
]

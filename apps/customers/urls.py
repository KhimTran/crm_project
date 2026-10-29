from django.urls import path
from . import views

app_name = "customers"

urlpatterns = [
    path("crm/customers/", views.customer_list, name="list"),
    path("crm/customers/new/", views.customer_create, name="create"),
    path("crm/customers/<int:customer_id>/", views.customer_detail, name="detail"),
    path("crm/customers/<int:customer_id>/edit/", views.customer_edit, name="edit"),
    path("crm/customers/<int:customer_id>/lock/", views.customer_lock, name="lock"),
    path("crm/customers/<int:customer_id>/unlock/", views.customer_unlock, name="unlock"),
    path("crm/customers/<int:customer_id>/delete/", views.customer_delete, name="delete"),
    path("crm/customer-report/", views.customer_report, name="report"),
    path("account/profile/", views.profile, name="profile"),
    path("profile/", views.profile),
]

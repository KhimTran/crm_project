from django.urls import path
from . import views
from .portal_text import set_portal_language

app_name = "customers"

urlpatterns = [
    path("account/profile/", views.profile, name="profile"),
    path("portal-language/", set_portal_language, name="portal_language"),
    path("crm/customers/", views.customer_list, name="list"),
    path("crm/customers/new/", views.customer_create, name="create"),
    path("crm/customers/<int:customer_id>/", views.customer_detail, name="detail"),
    path("crm/customers/<int:customer_id>/lock/", views.customer_lock, name="lock"),
    path("crm/customers/<int:customer_id>/unlock/", views.customer_unlock, name="unlock"),
    path("crm/customers/<int:customer_id>/delete/", views.customer_delete, name="delete"),
]

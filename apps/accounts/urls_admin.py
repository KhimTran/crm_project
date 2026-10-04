from django.urls import path

from . import views


app_name = "accounts_admin"

urlpatterns = [
    path("", views.account_list, name="list"),
    path("create/", views.account_create, name="create"),
    path("<int:account_id>/", views.account_detail, name="detail"),
    path("<int:account_id>/role/", views.account_role, name="role"),
    path("<int:account_id>/lock/", views.account_lock, name="lock"),
    path("<int:account_id>/unlock/", views.account_unlock, name="unlock"),
    path("<int:account_id>/reset-password/", views.account_reset_password, name="reset_password"),
    path("<int:account_id>/delete/", views.account_delete, name="delete"),
]

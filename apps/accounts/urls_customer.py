from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import customer_views as views
from .customer_forms import AccountPasswordResetForm

app_name = "customer_auth"
urlpatterns = [
    path("login/", views.customer_login, name="login"),
    path("logout/", views.customer_logout, name="logout"),
    path("register/", views.register, name="register"),
    path("crm/", views.crm_home, name="crm_home"),
    path("account/password/change/", views.password_change, name="password_change"),
    path("password/reset/", auth_views.PasswordResetView.as_view(
        form_class=AccountPasswordResetForm, template_name="accounts/customer/password_reset.html",
        email_template_name="accounts/customer/password_reset_email.txt",
        subject_template_name="accounts/customer/password_reset_subject.txt",
        success_url=reverse_lazy("customer_auth:password_reset_done"),
    ), name="password_reset"),
    path("password/reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/customer/password_reset_done.html",
    ), name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/", views.AccountPasswordResetConfirmView.as_view(
        template_name="accounts/customer/password_reset_confirm.html",
        success_url=reverse_lazy("customer_auth:password_reset_complete"),
    ), name="password_reset_confirm"),
    path("password/reset/complete/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/customer/password_reset_complete.html",
    ), name="password_reset_complete"),
]

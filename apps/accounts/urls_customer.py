from django.urls import path

from . import customer_views as views

app_name = "customer_auth"
urlpatterns = [
    path("login/", views.customer_login, name="login"),
    path("logout/", views.customer_logout, name="logout"),
    path("register/", views.register, name="register"),
    path("crm/", views.crm_home, name="crm_home"),
    path("account/password/change/", views.password_change, name="password_change"),
]

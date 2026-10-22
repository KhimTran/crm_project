from django.urls import include, path
from . import views


urlpatterns = [
    path("", views.manager_home, name="manager_home"),
    # Staff login and logout handlers for Manager Portal
    path("login/", views.staff_login, name="manager_login"),
    path("logout/", views.manager_logout, name="manager_logout"),
    path("profile/", views.manager_profile, name="manager_profile"),
    path("catalog/", include("apps.catalog.urls")),
]

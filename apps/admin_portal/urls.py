from django.urls import include, path

urlpatterns = [
    path("", include("apps.admin_portal.urls_admin")),
]

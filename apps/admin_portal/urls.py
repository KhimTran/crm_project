from django.urls import include, path
from . import views


urlpatterns = [
    path("database/", views.database_tools, name="database_tools"),
    path("database/seed/", views.seed_data, name="seed_data"),
    path("accounts/", include("apps.accounts.urls_admin")),
    path("catalog/", include("apps.catalog.urls")),
]

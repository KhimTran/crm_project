from django.urls import include, path
from . import views


urlpatterns = [
    path("", views.admin_home, name="admin_home"),
    path("", views.admin_home, name="admin_portal_home"),
    # Staff login and logout handlers for Admin Portal
    path("login/", views.staff_login, name="admin_login"),
    path("login/", views.staff_login, name="login"),
    path("logout/", views.admin_logout, name="admin_logout"),
    path("logout/", views.admin_logout, name="logout"),
    path("database/", views.database_tools, name="database_tools"),
    path("database/backup/", views.backup_database, name="database_backup"),
    path("database/restore/", views.restore_database, name="database_restore"),
    path("database/backups/<str:filename>/download/", views.download_backup, name="database_download_backup"),
    path("database/seed/", views.seed_data, name="seed_data"),
    path("accounts/", include("apps.accounts.urls_admin")),
]

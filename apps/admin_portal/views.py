import logging

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.html import format_html
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.managers import AccountManager
from apps.accounts.permissions import account_admin_required, manager_required, require_active_admin, require_active_manager
from apps.accounts.errors import AccountPermissionDenied
from apps.admin_portal.services.backup_service import create_database_backup, list_database_backups
from apps.admin_portal.services.restore_service import RestoreFailed, restore_confirmation, restore_database_from_backup, validate_backup_filename


logger = logging.getLogger(__name__)


class PortalLoginForm(forms.Form):
    email = forms.EmailField(max_length=255, widget=forms.EmailInput(attrs={"autocomplete": "username", "autofocus": True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


def _safe_staff_next(request, account):
    destination = request.POST.get("next") or request.GET.get("next") or ""
    host = request.get_host()
    if not destination.startswith("/") or destination.startswith("//"):
        destination = ""
    elif not url_has_allowed_host_and_scheme(destination, {host}, require_https=request.is_secure()):
        destination = ""

    role = getattr(account, "role", None)

    if role == AccountRole.ADMIN:
        default_admin = reverse("accounts_admin:list")
        if destination in ("/admin", "/admin/"):
            return default_admin
        if (
            destination.startswith("/admin/")
            and not destination.startswith("/admin/login")
            and not destination.startswith("/admin/logout")
        ):
            return destination
        return default_admin

    if role == AccountRole.MANAGER:
        default_manager = reverse("catalog_admin:product_list")
        if destination in ("/manager", "/manager/"):
            return default_manager
        if (
            (destination.startswith("/manager/") or destination.startswith("/crm/"))
            and not destination.startswith("/manager/login")
            and not destination.startswith("/manager/logout")
        ):
            return destination
        return default_manager

    return "/"


def _safe_admin_next(request):
    destination = request.POST.get("next") or request.GET.get("next") or ""
    if destination in ("/admin", "/admin/"):
        return reverse("accounts_admin:list")
    if (destination.startswith("/admin/") and
            not destination.startswith("/admin/login") and
            not destination.startswith("/admin/logout") and
            url_has_allowed_host_and_scheme(destination, {request.get_host()}, require_https=request.is_secure())):
        return destination
    return reverse("accounts_admin:list")


def _safe_manager_next(request):
    destination = request.POST.get("next") or request.GET.get("next") or ""
    if destination in ("/manager", "/manager/"):
        return reverse("catalog_admin:product_list")
    if ((destination.startswith("/manager/") or destination.startswith("/crm/")) and
            not destination.startswith("/manager/login") and
            not destination.startswith("/manager/logout") and
            url_has_allowed_host_and_scheme(destination, {request.get_host()}, require_https=request.is_secure())):
        return destination
    return reverse("catalog_admin:product_list")


# Backward compatibility helper
_safe_next = _safe_admin_next


@never_cache
@sensitive_post_parameters("password")
@require_http_methods(["GET", "POST"])
def staff_login(request):
    next_url = request.POST.get("next") or request.GET.get("next") or ""

    if request.user.is_authenticated and request.user.is_active:
        role = getattr(request.user, "role", None)
        if role == AccountRole.ADMIN:
            return redirect(_safe_staff_next(request, request.user))
        if role == AccountRole.MANAGER:
            return redirect(_safe_staff_next(request, request.user))
        form = PortalLoginForm()
        form.add_error(None, "Access Denied: Staff only.")
        return render(request, "admin/portal/login.html", {"form": form, "next": next_url})

    form = PortalLoginForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        if form.is_valid():
            email = AccountManager.normalize_account_email(form.cleaned_data["email"])
            account = authenticate(request, email=email, password=form.cleaned_data["password"])
            if account is not None:
                if account.status != AccountStatus.ACTIVE:
                    form.add_error(None, "Unable to sign in with these credentials.")
                elif account.role == AccountRole.CUSTOMER:
                    form.add_error(None, "Access Denied: Staff only.")
                elif account.role in (AccountRole.ADMIN, AccountRole.MANAGER):
                    login(request, account)
                    return redirect(_safe_staff_next(request, account))
                else:
                    form.add_error(None, "Access Denied: Staff only.")
            else:
                form.add_error(None, "Unable to sign in with these credentials.")

    return render(request, "admin/portal/login.html", {"form": form, "next": next_url})


# Staff login aliases
admin_login = staff_login
manager_login = staff_login


# --- Admin Portal Views (/admin) ---

@require_GET
def admin_home(request):
    try:
        require_active_admin(request.user)
    except AccountPermissionDenied:
        return redirect("admin_login")
    return redirect("accounts_admin:list")


@require_POST
def admin_logout(request):
    logout(request)
    return redirect("admin_login")


@account_admin_required
@require_GET
def database_tools(request):
    backups = list_database_backups()
    return render(request, "admin/portal/database.html", {
        "active_section": "database",
        "seed_available": settings.DEBUG,
        "backups": backups,
        "database_name": settings.DATABASES["default"]["NAME"],
    })


@account_admin_required
@require_POST
def backup_database(request):
    try:
        backup_path = create_database_backup(actor_id=request.user.pk)
        messages.success(request, f"Database backup created successfully: {backup_path.name}")
    except (OSError, ValueError, RuntimeError) as exc:
        logger.error("database_backup request_failure actor_id=%s reason=%s", request.user.pk, type(exc).__name__)
        messages.error(request, "Database backup failed. No verified backup was published; check the server log and database tool configuration.")
    return redirect("database_tools")


@account_admin_required
@require_GET
def download_backup(request, filename):
    try:
        file_path = validate_backup_filename(filename)
        return FileResponse(file_path.open("rb"), as_attachment=True, filename=filename)
    except (OSError, ValueError):
        messages.error(request, "Unable to download the selected backup.")
        return redirect("database_tools")


@account_admin_required
@require_POST
def restore_database(request):
    filename = request.POST.get("filename", "").strip()
    confirm = (request.POST.get("restore_confirm") or request.POST.get("confirm") or "").strip()
    if not filename:
        messages.error(request, "Please select a backup file to restore.")
        return redirect("database_tools")
    database_name = settings.DATABASES["default"]["NAME"]
    if (request.POST.get("target_database") != database_name
            or confirm != restore_confirmation(filename, database_name)
            or request.POST.get("maintenance_ack") != "on"):
        messages.error(request, "Confirm the exact backup file, target database and maintenance window before restoring.")
        return redirect("database_tools")

    try:
        recovery_path = restore_database_from_backup(
            filename, confirm, actor=request.user,
            target_database=request.POST.get("target_database", ""),
            maintenance_ack=request.POST.get("maintenance_ack") == "on",
        )
        # The imported dump may replace django_session, including this session.
        # Report the result without a session save or database-backed rendering.
        response = HttpResponse(format_html(
            "<h1>Database restored</h1><p>Database <code>{}</code> was restored from <code>{}</code>.</p>"
            "<p>Recovery backup retained: <code>{}</code>.</p><p><a href=\"{}\">Sign in again</a></p>",
            database_name, filename, recovery_path.name, reverse("admin_login"),
        ))
        response.delete_cookie(settings.SESSION_COOKIE_NAME, path=settings.SESSION_COOKIE_PATH,
                               domain=settings.SESSION_COOKIE_DOMAIN, samesite=settings.SESSION_COOKIE_SAMESITE)
        return response
    except RestoreFailed as exc:
        # A partially imported database may no longer support sessions or context processors.
        return HttpResponse(format_html("<h1>Database recovery required</h1><p>{}</p>", str(exc)), status=503)
    except AccountPermissionDenied:
        return HttpResponseForbidden("Database restoration is restricted to active administrators.")
    except (ValueError, RuntimeError) as exc:
        logger.warning("database_restore request_rejected actor_id=%s reason=%s", request.user.pk, type(exc).__name__)
        messages.error(request, str(exc))
    except OSError:
        logger.error("database_restore request_failure actor_id=%s reason=filesystem_error", request.user.pk)
        return HttpResponse("Database restore could not complete. Keep external writers stopped and check the server log and "
                            "database/backups/.restore-recovery.json for recovery instructions.", status=503, content_type="text/plain")
    return redirect("database_tools")


@account_admin_required
@require_POST
def seed_data(request):
    if not settings.DEBUG:
        return HttpResponseForbidden("Seed data is available only in development mode")
    if request.POST.get("confirm") != "SEED":
        messages.error(request, "Confirm the seed operation before continuing.")
        return redirect("database_tools")
    try:
        call_command("seed_data", verbosity=0)
    except (CommandError, ValueError):
        messages.error(request, "Seed data could not be completed. Check the server log.")
    else:
        messages.success(request, "Seed data completed.")
    return redirect("database_tools")


# --- Manager Portal Views (/manager) ---

@require_GET
def manager_home(request):
    try:
        require_active_manager(request.user)
    except AccountPermissionDenied:
        return redirect("manager_login")
    return redirect("catalog_admin:product_list")


@require_POST
def manager_logout(request):
    logout(request)
    return redirect("manager_login")


# Aliases for backwards compatibility
home = admin_home
portal_login = staff_login
portal_logout = admin_logout

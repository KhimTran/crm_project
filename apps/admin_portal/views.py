from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.managers import AccountManager
from apps.accounts.permissions import account_admin_required, require_active_admin
from apps.accounts.errors import AccountPermissionDenied


class PortalLoginForm(forms.Form):
    email = forms.EmailField(max_length=255, widget=forms.EmailInput(attrs={"autocomplete": "username", "autofocus": True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))


def _safe_next(request):
    destination = request.POST.get("next") or request.GET.get("next") or ""
    if (destination.startswith("/admin-portal/") and
            url_has_allowed_host_and_scheme(destination, {request.get_host()})):
        return destination
    return reverse("accounts_admin:list")


@require_GET
def home(request):
    try:
        require_active_admin(request.user)
    except AccountPermissionDenied:
        return redirect("login")
    return redirect("accounts_admin:list")


@require_http_methods(["GET", "POST"])
def portal_login(request):
    try:
        require_active_admin(request.user)
    except AccountPermissionDenied:
        pass
    else:
        return redirect(_safe_next(request))
    form = PortalLoginForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        if form.is_valid():
            email = AccountManager.normalize_account_email(form.cleaned_data["email"])
            account = authenticate(request, email=email, password=form.cleaned_data["password"])
            if account is not None:
                try:
                    require_active_admin(account)
                except AccountPermissionDenied:
                    pass
                else:
                    login(request, account)
                    return redirect(_safe_next(request))
        form.add_error(None, "Unable to sign in to the Admin Portal with these credentials.")
    return render(request, "admin_portal/login.html", {"form": form, "next": _safe_next(request)})


@require_POST
def portal_logout(request):
    logout(request)
    return redirect("login")


@account_admin_required
@require_GET
def database_tools(request):
    return render(request, "admin_portal/database.html", {
        "active_section": "database", "seed_available": settings.DEBUG,
    })


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

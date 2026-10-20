"""Shared role/group guards and home destinations for function-based views."""

from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .constants import AccountRole, AccountStatus, normalize_account_choice
from .models import Account


_CRM_GROUPS = frozenset({"CRM_MANAGER", "CUSTOMER_SERVICE"})
_ALLOWED_ROLES = frozenset(AccountRole.values) | _CRM_GROUPS
_ACCESS_DENIED_MESSAGE = "You do not have permission to access this feature."


def _get_active_account(user):
    if (not getattr(user, "is_authenticated", False)
            or not getattr(user, "is_active", False)
            or not getattr(user, "pk", None)):
        return None
    # Re-read DB so that stale session/object does not retain permissions after lock or role change.
    return Account.objects.filter(pk=user.pk, status=AccountStatus.ACTIVE).only(
        "account_id", "role", "status",
    ).first()


def _normalize_role(value):
    normalized = normalize_account_choice(value)
    if normalized is not None and normalized in _ALLOWED_ROLES:
        return normalized
    if isinstance(value, str):
        candidate = value.strip().upper()
        if candidate in _ALLOWED_ROLES:
            return candidate
    raise ValueError(f"Unknown role or group: {value}")


def _home_path(account):
    if account.role == AccountRole.ADMIN:
        return "/admin/"
    if account.role == AccountRole.MANAGER:
        return "/manager/"
    return "/"


def get_home_path(account):
    return _home_path(account)


def role_required(*allowed):
    permissions = {_normalize_role(item) for item in allowed}
    if not permissions:
        raise ValueError("role_required requires at least one role or CRM group.")

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not getattr(request.user, "is_authenticated", False):
                return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

            account = _get_active_account(request.user)
            if account is None:
                return HttpResponseForbidden("Account is inactive.")

            if account.role in permissions:
                return view(request, *args, **kwargs)
            groups = permissions & _CRM_GROUPS
            if groups and account.groups.filter(name__in=groups).exists():
                return view(request, *args, **kwargs)

            messages.error(request, _ACCESS_DENIED_MESSAGE)
            destination = _home_path(account)
            if request.path.rstrip("/") == destination.rstrip("/"):
                return HttpResponseForbidden(_ACCESS_DENIED_MESSAGE)
            return redirect(destination)

        return wrapped

    return decorator

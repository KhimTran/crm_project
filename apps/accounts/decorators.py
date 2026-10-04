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
_ACCESS_DENIED_MESSAGE = "Bạn không có quyền truy cập chức năng này."


def _get_active_account(user):
    if (not getattr(user, "is_authenticated", False)
            or not getattr(user, "is_active", False)
            or not getattr(user, "pk", None)):
        return None
    # Đọc lại DB để session/object cũ không giữ quyền sau khi khóa hoặc đổi role.
    return Account.objects.filter(pk=user.pk, status=AccountStatus.ACTIVE).only(
        "account_id", "role", "status",
    ).first()


def _home_path(account):
    if account is None:
        return "/"
    if account.role == AccountRole.ADMIN:
        return "/admin-portal/"
    if account.groups.filter(name__in=_CRM_GROUPS).exists():
        return "/crm/"
    return "/"


def get_home_path(user):
    """Return a destination; this helper does not create or protect any route.

    Priority: ADMIN, CRM_MANAGER, CUSTOMER_SERVICE, CUSTOMER. Anonymous,
    inactive or missing accounts fall back to /. CRM permissions are Groups,
    and a CUSTOMER Account may also belong to either CRM Group.
    """
    return _home_path(_get_active_account(user))


def role_required(*allowed_roles):
    """Require any listed Account role or CRM Group on a synchronous FBV.

    Accept ADMIN, CUSTOMER, CRM_MANAGER and CUSTOMER_SERVICE (strip/upper).
    ADMIN has no implicit bypass for a Group-only view. Invalid or empty
    configuration raises ValueError immediately, before a request is handled.
    """
    if not allowed_roles:
        raise ValueError("role_required requires at least one role or group")
    permissions = set()
    for role in allowed_roles:
        permission = normalize_account_choice(role)
        if not isinstance(permission, str) or permission not in _ALLOWED_ROLES:
            raise ValueError("Role must be ADMIN, CUSTOMER, CRM_MANAGER or CUSTOMER_SERVICE")
        permissions.add(permission)

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not getattr(request.user, "is_authenticated", False):
                return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

            account = _get_active_account(request.user)
            if account is None:
                return HttpResponseForbidden("Tài khoản không hoạt động.")

            if account.role in permissions:
                return view(request, *args, **kwargs)
            groups = permissions & _CRM_GROUPS
            if groups and account.groups.filter(name__in=groups).exists():
                return view(request, *args, **kwargs)

            messages.error(request, _ACCESS_DENIED_MESSAGE)
            destination = _home_path(account)
            # So sánh cả biến thể thiếu slash để tránh vòng lặp APPEND_SLASH.
            if request.path.rstrip("/") == destination.rstrip("/"):
                return HttpResponseForbidden(_ACCESS_DENIED_MESSAGE)
            return redirect(destination)

        return wrapped

    return decorator

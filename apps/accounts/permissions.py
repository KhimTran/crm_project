from .constants import AccountRole, AccountStatus
from .errors import AccountPermissionDenied
from .models import Account
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import urlencode


def require_active_admin(actor, *, for_update=False):
    """Return the current database Account or deny Account management access."""
    if not getattr(actor, "is_authenticated", False) or not getattr(actor, "pk", None):
        raise AccountPermissionDenied("An active admin account is required")
    query = Account.objects.filter(pk=actor.pk).only("account_id", "role", "status")
    if for_update:
        query = query.select_for_update()
    account = query.first()
    if account is None or account.role != AccountRole.ADMIN or account.status != AccountStatus.ACTIVE:
        raise AccountPermissionDenied("An active admin account is required")
    return account


def account_admin_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not getattr(request.user, "is_authenticated", False):
            destination = request.get_full_path() if request.method in ("GET", "HEAD") else reverse("accounts_admin:list")
            return redirect(f"{reverse('login')}?{urlencode({'next': destination})}")
        try:
            require_active_admin(request.user)
        except AccountPermissionDenied:
            return HttpResponseForbidden("Account administration is restricted")
        return view(request, *args, **kwargs)
    return wrapped

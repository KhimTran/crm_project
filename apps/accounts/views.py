from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils.http import urlencode
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .errors import AccountNotFound, AccountPermissionDenied, AccountServiceError
from .forms import AccountCreateForm, AccountListFilterForm, AccountRoleForm, AdminPasswordResetForm
from .permissions import account_admin_required
from .selectors import get_account, list_account_page
from .services import change_account_role, create_account, delete_account, lock_account, reset_account_password, unlock_account


def _get_account_or_404(actor, account_id):
    try:
        return get_account(actor, account_id)
    except AccountNotFound as exc:
        raise Http404("Account not found") from exc


def _run_action(request, account_id, service, success_message, *args):
    try:
        service(request.user, account_id, *args)
    except AccountNotFound as exc:
        raise Http404("Account not found") from exc
    except AccountPermissionDenied:
        return HttpResponseForbidden("Account administration is restricted")
    except AccountServiceError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, success_message)
    return redirect("accounts_admin:list")


def _page_context(request, *, create_form=None, reset_form=None, reset_account=None):
    filters = AccountListFilterForm(request.GET)
    filters_valid = filters.is_valid()
    page_obj = None
    if filters_valid:
        page_obj = list_account_page(
            request.user, page=request.GET.get("page", 1),
            q=filters.cleaned_data["q"], role=filters.cleaned_data["role"],
            status=filters.cleaned_data["status"],
        )
    filter_query = ""
    if filters_valid:
        filter_query = urlencode({
            key: filters.cleaned_data[key]
            for key in ("q", "role", "status")
            if filters.cleaned_data[key]
        })
    return {
        "active_section": "accounts", "filters": filters, "filters_valid": filters_valid,
        "page_obj": page_obj,
        "filter_query": filter_query,
        "create_form": create_form or AccountCreateForm(),
        "reset_form": reset_form or AdminPasswordResetForm(),
        "role_form": AccountRoleForm(), "reset_account": reset_account,
        "show_create_modal": create_form is not None,
        "show_reset_modal": reset_form is not None,
        "form": create_form or reset_form,
    }


@account_admin_required
@require_GET
def account_list(request):
    return render(request, "accounts/admin/account_list.html", _page_context(request))


@account_admin_required
@require_GET
def account_detail(request, account_id):
    account = _get_account_or_404(request.user, account_id)
    return render(request, "accounts/admin/account_detail.html", {
        "account": account, "role_form": AccountRoleForm(initial={"role": account["role"]}),
        "active_section": "accounts",
    })


@account_admin_required
@require_http_methods(["GET", "POST"])
def account_create(request):
    form = AccountCreateForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            account = create_account(request.user, **{
                key: form.cleaned_data[key] for key in ("email", "role", "status", "password")
            })
        except AccountPermissionDenied:
            return HttpResponseForbidden("Account administration is restricted")
        except (AccountServiceError, ValidationError, ValueError) as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, "Account created")
            return redirect("accounts_admin:list")
    return render(request, "accounts/admin/account_list.html", _page_context(request, create_form=form))


@account_admin_required
@require_POST
def account_role(request, account_id):
    form = AccountRoleForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid account role")
        return redirect("accounts_admin:list")
    return _run_action(request, account_id, change_account_role, "Account role changed", form.cleaned_data["role"])


@account_admin_required
@require_POST
def account_lock(request, account_id):
    return _run_action(request, account_id, lock_account, "Account locked")


@account_admin_required
@require_POST
def account_unlock(request, account_id):
    return _run_action(request, account_id, unlock_account, "Account unlocked")


@account_admin_required
@require_http_methods(["GET", "POST"])
def account_reset_password(request, account_id):
    account = _get_account_or_404(request.user, account_id)
    form = AdminPasswordResetForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            reset_account_password(request.user, account_id, form.cleaned_data["new_password"])
        except AccountPermissionDenied:
            return HttpResponseForbidden("Account administration is restricted")
        except AccountNotFound as exc:
            raise Http404("Account not found") from exc
        except AccountServiceError as exc:
            form.add_error("new_password", str(exc))
        else:
            messages.success(request, "Password reset")
            return redirect("accounts_admin:list")
    return render(request, "accounts/admin/account_list.html", _page_context(
        request, reset_form=form, reset_account=account,
    ))


@account_admin_required
@require_POST
def account_delete(request, account_id):
    try:
        delete_account(request.user, account_id)
    except AccountPermissionDenied:
        return HttpResponseForbidden("Account administration is restricted")
    except AccountNotFound as exc:
        raise Http404("Account not found") from exc
    except AccountServiceError as exc:
        messages.error(request, str(exc))
        return redirect("accounts_admin:list")
    messages.success(request, "Account deleted")
    return redirect("accounts_admin:list")

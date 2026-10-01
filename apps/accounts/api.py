from datetime import datetime

from django.core.exceptions import ValidationError
from ninja import Router, Schema
from ninja.errors import HttpError
from pydantic import ConfigDict

from .errors import (
    AccountAlreadyActive, AccountAlreadyLocked, AccountDeleteProtectedError,
    AccountNotFound, AccountPermissionDenied, AccountServiceError,
    CannotDeleteOwnAccount, CannotLockOwnAccount, DuplicateAccountEmail,
    InvalidAccountRole, LastActiveAdminError, PasswordValidationError,
)
from .forms import AccountCreateForm
from .permissions import require_active_admin
from .selectors import get_account, list_account_page
from .services import change_account_role, create_account, delete_account, lock_account, reset_account_password, unlock_account


router = Router(tags=["Accounts"])


class StrictSchema(Schema):
    model_config = ConfigDict(extra="forbid")


class AccountCreateInput(StrictSchema):
    email: str
    role: str
    status: str
    password: str
    password_confirm: str


class AccountRoleInput(StrictSchema):
    role: str


class AccountPasswordResetInput(StrictSchema):
    new_password: str
    new_password_confirm: str


class AccountOutput(Schema):
    account_id: int
    email: str
    role: str
    status: str
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AccountPage(Schema):
    items: list[AccountOutput]
    page: int
    page_size: int
    total: int


class AccountIdOutput(Schema):
    account_id: int


def _guard(request):
    try:
        require_active_admin(request.user)
    except AccountPermissionDenied as exc:
        raise HttpError(403, "Account administration is restricted") from exc


def _run(action, *args, **kwargs):
    try:
        return action(*args, **kwargs)
    except AccountPermissionDenied as exc:
        raise HttpError(403, "Account administration is restricted") from exc
    except AccountNotFound as exc:
        raise HttpError(404, "Account not found") from exc
    except (DuplicateAccountEmail, AccountAlreadyActive, AccountAlreadyLocked,
            AccountDeleteProtectedError, CannotDeleteOwnAccount,
            CannotLockOwnAccount, LastActiveAdminError) as exc:
        raise HttpError(409, str(exc)) from exc
    except (InvalidAccountRole, PasswordValidationError, ValidationError, ValueError) as exc:
        raise HttpError(400, "Invalid account input") from exc


def _valid_form(form):
    if not form.is_valid():
        raise HttpError(400, "Invalid account input: " + ", ".join(form.errors.keys()))
    return form.cleaned_data


@router.get("/", response=AccountPage)
def account_list(request, page: int = 1, page_size: int = 20,
                 role: str | None = None, status: str | None = None):
    _guard(request)
    if page < 1 or not 1 <= page_size <= 100:
        raise HttpError(400, "Invalid pagination")
    result = _run(list_account_page, request.user, page=page, page_size=page_size,
                  role=role, status=status)
    return {"items": result.object_list, "page": result.number,
            "page_size": page_size, "total": result.paginator.count}


@router.post("/", response={201: AccountOutput})
def account_create(request, payload: AccountCreateInput):
    _guard(request)
    data = _valid_form(AccountCreateForm(payload.dict()))
    return 201, _run(create_account, request.user, email=data["email"],
                     role=data["role"], status=data["status"], password=data["password"])


@router.get("/{account_id}", response=AccountOutput)
def account_detail(request, account_id: int):
    _guard(request)
    return _run(get_account, request.user, account_id)


@router.post("/{account_id}/role", response=AccountOutput)
def account_role(request, account_id: int, payload: AccountRoleInput):
    _guard(request)
    return _run(change_account_role, request.user, account_id, payload.role)


@router.post("/{account_id}/lock", response=AccountOutput)
def account_lock(request, account_id: int):
    _guard(request)
    return _run(lock_account, request.user, account_id)


@router.post("/{account_id}/unlock", response=AccountOutput)
def account_unlock(request, account_id: int):
    _guard(request)
    return _run(unlock_account, request.user, account_id)


@router.post("/{account_id}/reset-password", response=AccountIdOutput)
def account_reset_password(request, account_id: int, payload: AccountPasswordResetInput):
    _guard(request)
    if payload.new_password != payload.new_password_confirm:
        raise HttpError(400, "Passwords do not match")
    return _run(reset_account_password, request.user, account_id, payload.new_password)


@router.delete("/{account_id}", response=AccountIdOutput)
def account_delete(request, account_id: int):
    _guard(request)
    return _run(delete_account, request.user, account_id)

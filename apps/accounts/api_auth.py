from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.utils import check_csrf
from pydantic import ConfigDict

from .managers import AccountManager


router = Router(tags=["Authentication"])


class LoginInput(Schema):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class SessionAccount(Schema):
    account_id: int
    email: str
    role: str
    status: str


class LoginOutput(Schema):
    authenticated: bool
    account: SessionAccount


class CurrentUserOutput(SessionAccount):
    authenticated: bool


class LogoutOutput(Schema):
    authenticated: bool


class CsrfOutput(Schema):
    csrf_token: str


def _account_data(account):
    return {"account_id": account.account_id, "email": account.email,
            "role": account.role, "status": account.status}


def _require_csrf(request):
    # Ninja wraps operations outside Django's standard CSRF view check.
    # Run Django's CSRF middleware check explicitly for public login.
    if check_csrf(request):
        raise HttpError(403, "CSRF check failed")


@router.get("/csrf", auth=None, response=CsrfOutput)
def csrf_token(request):
    return {"csrf_token": get_token(request)}


@router.post("/login", auth=None, response=LoginOutput)
def session_login(request, payload: LoginInput):
    _require_csrf(request)
    try:
        email = AccountManager.normalize_account_email(payload.email)
    except ValueError as exc:
        raise HttpError(401, "Invalid credentials") from exc
    account = authenticate(request, email=email, password=payload.password)
    if account is None:
        raise HttpError(401, "Invalid credentials")
    login(request, account)
    return {"authenticated": True, "account": _account_data(account)}


@router.get("/me", response=CurrentUserOutput)
def current_user(request):
    return {"authenticated": True, **_account_data(request.user)}


@router.post("/logout", response=LogoutOutput)
def session_logout(request):
    logout(request)
    return {"authenticated": False}

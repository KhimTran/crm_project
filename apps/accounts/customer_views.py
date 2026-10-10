import logging
from urllib.parse import urlsplit

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordResetConfirmView
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import Resolver404, resolve
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.customers.self_services import register_customer
from .constants import AccountStatus
from .customer_forms import CustomerLoginForm, CustomerRegistrationForm
from .decorators import get_home_path, role_required
from .models import Account

logger = logging.getLogger(__name__)


def safe_login_destination(request, account):
    fallback = get_home_path(account)
    destination = request.POST.get("next") or request.GET.get("next") or ""
    if (not destination.startswith("/") or destination.startswith("//")
            or not url_has_allowed_host_and_scheme(destination, {request.get_host()}, require_https=request.is_secure())):
        return fallback
    try:
        match = resolve(urlsplit(destination).path)
    except Resolver404:
        return fallback
    allowed = {"shop:home", "shop:products", "shop:product_detail", "customer_auth:password_change"}
    if account.role == "CUSTOMER":
        allowed.add("customers:profile")
    if fallback in ("/crm/", "/admin-portal/"):
        allowed.add("customer_auth:crm_home")
    if fallback == "/admin-portal/":
        allowed.update({"admin_portal_home", "accounts_admin:list", "accounts_admin:detail"})
    return destination if match.view_name in allowed else fallback


@never_cache
@sensitive_post_parameters("password")
@require_http_methods(["GET", "POST"])
def customer_login(request):
    if request.user.is_authenticated and request.user.is_active:
        return redirect(safe_login_destination(request, request.user))
    form = CustomerLoginForm(request, request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        login(request, form.account)
        return redirect(safe_login_destination(request, form.account))
    return render(request, "accounts/customer/login.html", {"form": form, "next": request.POST.get("next", request.GET.get("next", ""))})


@require_POST
def customer_logout(request):
    logout(request)
    return redirect("customer_auth:login")


@never_cache
@sensitive_post_parameters("password", "password_confirm")
@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect(get_home_path(request.user))
    form = CustomerRegistrationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            register_customer(email=form.cleaned_data["email"], password=form.cleaned_data["password"], profile_data=form.cleaned_data)
        except ValidationError as exc:
            for field, errors in (exc.message_dict if hasattr(exc, "message_dict") else {"__all__": exc.messages}).items():
                form.add_error(field if field in form.fields else None, errors)
        else:
            messages.success(request, "Đăng ký thành công. Bạn có thể đăng nhập.")
            return redirect("customer_auth:login")
    return render(request, "accounts/customer/form.html", {"form": form, "title": "Đăng ký khách hàng", "submit_label": "Đăng ký"})


@role_required("ADMIN", "CUSTOMER")
@never_cache
@sensitive_post_parameters("old_password", "new_password1", "new_password2")
@require_http_methods(["GET", "POST"])
def password_change(request):
    with transaction.atomic():
        account = Account.objects.select_for_update().filter(pk=request.user.pk).first()
        if account is None or not account.is_active:
            raise PermissionDenied
        form = PasswordChangeForm(account, request.POST if request.method == "POST" else None)
        if request.method == "POST" and form.is_valid():
            form.save()
            transaction.on_commit(lambda: logger.info("password_changed actor=%s target=%s", account.pk, account.pk))
            update_session_auth_hash(request, account)
            messages.success(request, "Đã đổi mật khẩu.")
            return redirect(get_home_path(account))
    return render(request, "accounts/customer/form.html", {"form": form, "title": "Đổi mật khẩu", "submit_label": "Đổi mật khẩu"})


@role_required("ADMIN", "CRM_MANAGER", "CUSTOMER_SERVICE")
@require_GET
def crm_home(request):
    return render(request, "accounts/customer/crm_home.html")


@method_decorator(sensitive_post_parameters("new_password1", "new_password2"), name="dispatch")
class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    def get_user(self, uidb64):
        account = super().get_user(uidb64)
        return account if account is not None and account.is_active else None

    def form_valid(self, form):
        with transaction.atomic():
            account = Account.objects.select_for_update().filter(pk=self.user.pk).first()
            token = self.request.session.get("_password_reset_token")
            if account is None or account.status != AccountStatus.ACTIVE or not self.token_generator.check_token(account, token):
                form.add_error(None, "Liên kết đã hết hạn hoặc không còn hợp lệ.")
                return self.form_invalid(form)
            form.user = account
            transaction.on_commit(lambda: logger.info("password_reset target=%s", account.pk))
            return super().form_valid(form)

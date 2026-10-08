"""Customer-owned profile operations; CRM management remains a separate module."""
import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.managers import AccountManager
from apps.accounts.models import Account
from .models import Customer, CustomerPreference
from .self_service_forms import CustomerPreferenceForm, CustomerProfileForm

logger = logging.getLogger(__name__)


def _profile_data(data):
    form = CustomerProfileForm(data)
    if not form.is_valid():
        raise ValidationError(form.errors)
    return form.cleaned_data


@transaction.atomic
def register_customer(*, email, password, profile_data):
    """Always create an ACTIVE CUSTOMER and its profile, or roll back both."""
    profile = _profile_data(profile_data)
    email = AccountManager.normalize_account_email(email)
    if Account.objects.filter(email=email).exists():
        raise ValidationError({"email": "Email đã được sử dụng."})
    try:
        with transaction.atomic():
            account = Account.objects.create_user(
                email, password, role=AccountRole.CUSTOMER, status=AccountStatus.ACTIVE,
            )
    except (IntegrityError, ValidationError) as exc:
        # Only classify a real duplicate; do not hide unrelated integrity failures.
        if Account.objects.filter(email=email).exists():
            raise ValidationError({"email": "Email đã được sử dụng."}) from exc
        raise
    Customer.objects.create(account=account, status="ACTIVE", **profile)
    transaction.on_commit(lambda: logger.info("customer_registered target=%s", account.pk))
    return account


def own_customer(actor, *, for_update=False):
    if not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Bạn cần đăng nhập.")
    accounts = Account.objects.filter(pk=actor.pk, role=AccountRole.CUSTOMER, status=AccountStatus.ACTIVE)
    if for_update:
        accounts = accounts.select_for_update()
    if accounts.first() is None:
        raise PermissionDenied("Tài khoản không có quyền sửa hồ sơ khách hàng.")
    customers = Customer.objects.filter(account_id=actor.pk, status="ACTIVE", deleted_at__isnull=True)
    if for_update:
        customers = customers.select_for_update()
    customer = customers.first()
    if customer is None:
        raise PermissionDenied("Hồ sơ chưa khả dụng. Vui lòng liên hệ quản lý.")
    return customer


@transaction.atomic
def update_own_profile(actor, *, profile_data, preferences):
    customer = own_customer(actor, for_update=True)
    profile = _profile_data(profile_data)
    existing = {item.pk: item for item in CustomerPreference.objects.select_for_update().filter(customer=customer)}
    seen = set()
    for data in preferences:
        preference_id = data.get("preference_id")
        if preference_id is not None:
            if preference_id not in existing or preference_id in seen:
                raise PermissionDenied("Sở thích không thuộc hồ sơ của bạn.")
            seen.add(preference_id)
        if data.get("DELETE"):
            if preference_id is not None:
                existing[preference_id].delete()
            continue
        form = CustomerPreferenceForm(data)
        if not form.is_valid():
            raise ValidationError(form.errors)
        preference = existing.get(preference_id) or CustomerPreference(customer=customer)
        for field, value in form.cleaned_data.items():
            setattr(preference, field, value)
        preference.save()
    for field, value in profile.items():
        setattr(customer, field, value)
    customer.save(update_fields=[*profile, "updated_at"])
    transaction.on_commit(lambda: logger.info("customer_profile_updated actor=%s target=%s", actor.pk, customer.pk))
    return customer

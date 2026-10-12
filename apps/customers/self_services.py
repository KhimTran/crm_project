"""Customer-owned profile operations; CRM management remains a separate module."""
import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.managers import AccountManager
from apps.accounts.models import Account
from apps.catalog.models import Category, Status
from .models import Customer, CustomerPreference
from .self_service_choices import CATEGORY_PREFERENCE_TYPE
from .self_service_forms import CustomerCategoryPreferencesForm, CustomerProfileForm

logger = logging.getLogger(__name__)


def _profile_data(data, *, instance=None):
    form = CustomerProfileForm(data, instance=instance)
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
def update_own_profile(actor, *, profile_data, category_ids=(), remove_preference_ids=()):
    """Sync only own CATEGORY names; preserve unmatched rows unless explicitly removed."""
    customer = own_customer(actor, for_update=True)
    profile = _profile_data(profile_data, instance=customer)
    existing = list(CustomerPreference.objects.select_for_update().filter(
        customer=customer, preference_type=CATEGORY_PREFERENCE_TYPE,
    ).order_by("preference_id"))
    # Validate again under locks: a category may have been disabled since GET/POST validation.
    active_categories = list(Category.objects.select_for_update().filter(status=Status.ACTIVE).order_by("category_id"))
    form = CustomerCategoryPreferencesForm(customer, {
        "categories": category_ids, "remove_preferences": remove_preference_ids,
    }, active_categories=active_categories, preferences=existing)
    if not form.is_valid():
        raise ValidationError(form.errors)
    selected_ids = set(form.cleaned_data["categories"])
    selected_names = {category.category_name for category in active_categories if category.pk in selected_ids}
    active_names = {category.category_name for category in active_categories}
    removed_ids = set(form.cleaned_data["remove_preferences"])
    retained_names = set()
    for preference in existing:
        value = preference.preference_value
        if preference.pk in removed_ids or (value in active_names and (
                value not in selected_names or value in retained_names)):
            preference.delete()
        elif value in selected_names:
            retained_names.add(value)
    CustomerPreference.objects.bulk_create([
        CustomerPreference(customer=customer, preference_type=CATEGORY_PREFERENCE_TYPE, preference_value=value)
        for value in sorted(selected_names - retained_names)
    ])
    for field, value in profile.items():
        setattr(customer, field, value)
    customer.save(update_fields=[*profile, "updated_at"])
    transaction.on_commit(lambda: logger.info("customer_profile_updated actor=%s target=%s", actor.pk, customer.pk))
    return customer

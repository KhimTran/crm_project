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
    """Always create an ACTIVE CUSTOMER, or roll back."""
    profile = _profile_data(profile_data)
    email = AccountManager.normalize_account_email(email)
    if Account.objects.filter(email=email).exists():
        raise ValidationError({"email": "Email is already in use."})
    try:
        with transaction.atomic():
            account = Account.objects.create_user(
                email, password, role=AccountRole.CUSTOMER, status=AccountStatus.ACTIVE,
                **profile,
            )
    except (IntegrityError, ValidationError) as exc:
        if Account.objects.filter(email=email).exists():
            raise ValidationError({"email": "Email is already in use."}) from exc
        raise
    transaction.on_commit(lambda: logger.info("customer_registered target=%s", account.pk))
    return account


def own_customer(actor, *, for_update=False):
    if not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Authentication required.")
    accounts = Customer.objects.filter(pk=actor.pk, status=AccountStatus.ACTIVE)
    if for_update:
        accounts = accounts.select_for_update()
    customer = accounts.first()
    if customer is None:
        raise PermissionDenied("Profile is not available or account does not have permission.")
    return customer


@transaction.atomic
def update_own_profile(actor, *, profile_data, category_ids=(), remove_preference_ids=()):
    """Sync only own CATEGORY names; preserve unmatched rows unless explicitly removed."""
    customer = own_customer(actor, for_update=True)
    profile = _profile_data(profile_data, instance=customer)
    existing = list(CustomerPreference.objects.select_for_update().filter(
        customer=customer, preference_type=CATEGORY_PREFERENCE_TYPE,
    ).order_by("preference_id"))

    for field, value in profile.items():
        setattr(customer, field, value)
    customer.save(update_fields=[*profile.keys(), "updated_at"])

    cleaned_preferences = CustomerCategoryPreferencesForm({
        "categories": category_ids,
        "remove_preferences": remove_preference_ids,
    }, existing=existing)
    if not cleaned_preferences.is_valid():
        raise ValidationError(cleaned_preferences.errors)

    if cleaned_preferences.cleaned_data["remove_preferences"]:
        CustomerPreference.objects.filter(
            customer=customer,
            preference_id__in=cleaned_preferences.cleaned_data["remove_preferences"],
        ).delete()

    requested = set(cleaned_preferences.cleaned_data["categories"])
    valid = set(Category.objects.filter(pk__in=requested, status=Status.ACTIVE).values_list("pk", flat=True))
    current = {pref.preference_value: pref for pref in existing}

    for category in Category.objects.filter(pk__in=valid).order_by("category_name"):
        if category.category_name not in current:
            CustomerPreference.objects.create(
                customer=customer,
                preference_type=CATEGORY_PREFERENCE_TYPE,
                preference_value=category.category_name,
            )

    for name, pref in current.items():
        if name not in {c.category_name for c in Category.objects.filter(pk__in=valid)}:
            pref.delete()

    transaction.on_commit(lambda: logger.info("customer_profile_updated target=%s", customer.pk))
    return customer

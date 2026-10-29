from django.core.exceptions import ValidationError
from apps.catalog.vocabulary import canonical_brand
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.managers import AccountManager
from apps.accounts.models import Account
from apps.feedback.models import Feedback
from apps.surveys.models import SurveyRecipient

from .constants import CustomerStatus, PreferenceType
from .errors import (
    CustomerAlreadyActive, CustomerAlreadyLocked, CustomerNotFound,
    CustomerServiceError, DuplicateCustomerEmail, DuplicateCustomerPhone,
)
from .models import Customer, CustomerPreference


@transaction.atomic
def create_customer(*, email, password, full_name, phone, date_of_birth=None, gender=None, address=None,
                    playing_level=None, play_styles=(), brands=()):
    """Create a CUSTOMER account atomically using Django password validation/hashing."""
    email = AccountManager.normalize_account_email(email)
    if Account.objects.filter(email=email).exists():
        raise DuplicateCustomerEmail("Email is already in use")
    if phone and Account.objects.filter(phone=phone).exists():
        raise DuplicateCustomerPhone("Phone number is already in use")

    try:
        with transaction.atomic():
            account = Account.objects.create_user(
                email, password, role=AccountRole.CUSTOMER, status=AccountStatus.ACTIVE,
                full_name=full_name, phone=phone or None, date_of_birth=date_of_birth,
                gender=gender or None, address=address or None, playing_level=playing_level or None,
            )
    except (IntegrityError, ValidationError) as exc:
        if Account.objects.filter(email=email).exists():
            raise DuplicateCustomerEmail("Email is already in use") from exc
        raise

    customer = Customer.objects.get(pk=account.pk)
    preferences = [CustomerPreference(customer=account, preference_type=PreferenceType.PLAY_STYLE, preference_value=v)
                   for v in play_styles]
    preferences += [CustomerPreference(customer=account, preference_type=PreferenceType.BRAND, preference_value=v)
                    for v in sorted({canonical_brand(value) for value in brands})]
    if preferences:
        CustomerPreference.objects.bulk_create(preferences)
    return customer


def _active_customer_for_update(customer_id):
    customer = Customer.objects.select_for_update().filter(pk=customer_id).first()
    if customer is None:
        raise CustomerNotFound("Customer not found")
    return customer


def _set_account_status(customer, status):
    Account.objects.filter(pk=customer.pk).update(status=status, updated_at=timezone.now())
    customer.refresh_from_db()


def customer_related_counts(customer):
    recipients = SurveyRecipient.objects.filter(customer=customer)
    return {
        "feedbacks": Feedback.objects.filter(customer=customer).count(),
        "surveys_sent": recipients.count(),
        "surveys_answered": recipients.filter(response__isnull=False).count(),
    }


@transaction.atomic
def update_customer(customer_id, *, email, full_name, phone=None, date_of_birth=None,
                    gender=None, address=None, playing_level=None):
    """Update customer profile fields atomically without altering password, role, status, or preferences."""
    customer = _active_customer_for_update(customer_id)
    if customer.role != AccountRole.CUSTOMER:
        raise CustomerServiceError("Only customer accounts can be edited here")

    email = AccountManager.normalize_account_email(email)
    if Account.objects.filter(email=email).exclude(pk=customer.pk).exists():
        raise DuplicateCustomerEmail("Email is already in use")
    if phone and Account.objects.filter(phone=phone).exclude(pk=customer.pk).exists():
        raise DuplicateCustomerPhone("Phone number is already in use")

    customer.email = email
    customer.full_name = full_name
    customer.phone = phone or None
    customer.date_of_birth = date_of_birth
    customer.gender = gender or None
    customer.address = address or None
    customer.playing_level = playing_level or None
    customer.save()
    return customer


@transaction.atomic
def lock_customer(customer_id):
    customer = _active_customer_for_update(customer_id)
    if customer.status == AccountStatus.LOCKED:
        raise CustomerAlreadyLocked("This customer account is already locked")
    _set_account_status(customer, AccountStatus.LOCKED)
    return customer


@transaction.atomic
def unlock_customer(customer_id):
    customer = _active_customer_for_update(customer_id)
    if customer.status == AccountStatus.ACTIVE:
        raise CustomerAlreadyActive("This customer account is already active")
    _set_account_status(customer, AccountStatus.ACTIVE)
    return customer


@transaction.atomic
def delete_customer(customer_id):
    customer = _active_customer_for_update(customer_id)
    counts = customer_related_counts(customer)
    if counts["feedbacks"] > 0 or counts["surveys_answered"] > 0:
        raise CustomerServiceError("Cannot delete customer with feedback or survey data. Please lock the account instead.")

    SurveyRecipient.objects.filter(customer=customer).delete()
    CustomerPreference.objects.filter(customer=customer).delete()
    customer.delete()
    return customer

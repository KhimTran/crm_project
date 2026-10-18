"""Provision missing customer profiles without changing existing profiles or credentials."""
from django.db import transaction

from apps.accounts.constants import AccountRole
from apps.accounts.models import Account

from .models import Customer


@transaction.atomic
def ensure_customer_profile(account_id):
    # Serialize with account changes; the OneToOne constraint also prevents duplicates.
    account = Account.objects.select_for_update().get(pk=account_id, role=AccountRole.CUSTOMER)
    return Customer.objects.get_or_create(
        account=account, defaults={"full_name": account.email[:150]},
    )

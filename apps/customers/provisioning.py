"""Provision missing customer profiles on Account."""
from django.db import transaction

from apps.accounts.constants import AccountRole
from apps.accounts.models import Account
from .models import Customer


@transaction.atomic
def ensure_customer_profile(account_id, *, full_name=None):
    account = Account.objects.select_for_update().get(pk=account_id, role=AccountRole.CUSTOMER)
    if full_name:
        account.full_name = full_name
    elif not account.full_name:
        account.full_name = account.email[:150]
    account.save(update_fields=["full_name", "updated_at"])
    return account, False

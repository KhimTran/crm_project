"""Provision missing admin and staff profiles on Account."""
from django.db import transaction

from .constants import AccountRole
from .models import Account


def generate_admin_code():
    return "AD0001"


def generate_staff_code():
    return "ST0001"


@transaction.atomic
def ensure_admin_profile(account_id, **profile_data):
    account = Account.objects.select_for_update().get(pk=account_id, role=AccountRole.ADMIN)
    was_empty = not bool(account.full_name)
    full_name = profile_data.pop("full_name", None)
    if full_name:
        account.full_name = full_name
    elif not account.full_name:
        account.full_name = account.email.split("@")[0] or "Admin"

    for k in ("phone", "date_of_birth", "gender", "address"):
        if k in profile_data and profile_data[k] is not None:
            setattr(account, k, profile_data[k])
    account.save()
    return account, was_empty


@transaction.atomic
def ensure_staff_profile(account_id, **profile_data):
    account = Account.objects.select_for_update().get(pk=account_id, role=AccountRole.MANAGER)
    was_empty = not bool(account.full_name)
    full_name = profile_data.pop("full_name", None)
    if full_name:
        account.full_name = full_name
    elif not account.full_name:
        account.full_name = account.email.split("@")[0] or "Staff"

    for k in ("phone", "date_of_birth", "gender", "address"):
        if k in profile_data and profile_data[k] is not None:
            setattr(account, k, profile_data[k])
    account.save()
    return account, was_empty

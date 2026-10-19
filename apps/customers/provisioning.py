"""Provision missing customer profiles without changing existing profiles or credentials."""
from django.db import transaction

from apps.accounts.constants import AccountRole
from apps.accounts.models import Account

from .models import Customer


# tv4: tạo hồ sơ Customer còn thiếu cho tài khoản CUSTOMER; full_name=None thì lấy email làm tên tạm
@transaction.atomic
def ensure_customer_profile(account_id, *, full_name=None):
    # Serialize with account changes; the OneToOne constraint also prevents duplicates.
    account = Account.objects.select_for_update().get(pk=account_id, role=AccountRole.CUSTOMER)
    if full_name is None:
        full_name = account.email[:150]
    return Customer.objects.get_or_create(account=account, defaults={"full_name": full_name})

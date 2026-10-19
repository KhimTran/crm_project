"""Provision missing admin and staff profiles without changing existing credentials."""
from django.db import transaction

from .constants import AccountRole
from .models import Account, Admin, Staff


def generate_admin_code():
    count = Admin.objects.count() + 1
    while True:
        code = f"AD{count:04d}"
        if not Admin.objects.filter(admin_code=code).exists():
            return code
        count += 1


def generate_staff_code():
    count = Staff.objects.count() + 1
    while True:
        code = f"ST{count:04d}"
        if not Staff.objects.filter(staff_code=code).exists():
            return code
        count += 1


@transaction.atomic
def ensure_admin_profile(account_id, **profile_data):
    account = Account.objects.select_for_update().get(pk=account_id, role=AccountRole.ADMIN)
    admin = Admin.objects.filter(account=account).first()
    if admin:
        if profile_data:
            for k, v in profile_data.items():
                if hasattr(admin, k) and v is not None:
                    setattr(admin, k, v)
            admin.save()
        return admin, False

    admin_code = profile_data.pop("admin_code", None) or generate_admin_code()
    full_name = profile_data.pop("full_name", None) or account.email.split("@")[0] or "Admin"
    defaults = {
        "admin_code": admin_code,
        "full_name": full_name,
        **{k: v for k, v in profile_data.items() if v is not None and hasattr(Admin, k)},
    }
    return Admin.objects.get_or_create(account=account, defaults=defaults)


@transaction.atomic
def ensure_staff_profile(account_id, **profile_data):
    account = Account.objects.select_for_update().get(pk=account_id, role=AccountRole.MANAGER)
    staff = Staff.objects.filter(account=account).first()
    if staff:
        if profile_data:
            for k, v in profile_data.items():
                if hasattr(staff, k) and v is not None:
                    setattr(staff, k, v)
            staff.save()
        return staff, False

    staff_code = profile_data.pop("staff_code", None) or generate_staff_code()
    full_name = profile_data.pop("full_name", None) or account.email.split("@")[0] or "Staff"
    defaults = {
        "staff_code": staff_code,
        "full_name": full_name,
        **{k: v for k, v in profile_data.items() if v is not None and hasattr(Staff, k)},
    }
    return Staff.objects.get_or_create(account=account, defaults=defaults)

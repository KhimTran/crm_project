from django.core.paginator import Paginator
from django.db.models import Q

from .constants import AccountRole, normalize_account_role, normalize_account_status
from .errors import AccountNotFound
from .models import Account
from .permissions import require_active_admin


ACCOUNT_PUBLIC_FIELDS = ("account_id", "email", "role", "status", "last_login", "created_at", "updated_at")


def account_data(account):
    data = {
        "account_id": account.account_id,
        "email": account.email,
        "role": account.role,
        "status": account.status,
        "last_login_at": account.last_login,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
        "profile": None,
        "full_name": "",
        "code": "",
    }
    if account.role == AccountRole.ADMIN:
        admin = getattr(account, "admin_profile", None)
        if admin:
            data["profile"] = {
                "type": "ADMIN",
                "admin_id": admin.admin_id,
                "code": admin.admin_code,
                "full_name": admin.full_name,
                "phone": admin.phone,
                "date_of_birth": admin.date_of_birth,
                "gender": admin.gender,
                "address": admin.address,
                "status": admin.status,
            }
            data["full_name"] = admin.full_name
            data["code"] = admin.admin_code
    elif account.role == AccountRole.MANAGER:
        staff = getattr(account, "staff_profile", None)
        if staff:
            data["profile"] = {
                "type": "MANAGER",
                "staff_id": staff.staff_id,
                "code": staff.staff_code,
                "full_name": staff.full_name,
                "phone": staff.phone,
                "date_of_birth": staff.date_of_birth,
                "gender": staff.gender,
                "address": staff.address,
                "position": staff.position,
                "hire_date": staff.hire_date,
                "status": staff.status,
            }
            data["full_name"] = staff.full_name
            data["code"] = staff.staff_code
    elif account.role == AccountRole.CUSTOMER:
        customer = getattr(account, "customer", None)
        if customer:
            data["profile"] = {
                "type": "CUSTOMER",
                "customer_id": customer.customer_id,
                "code": getattr(customer, "customer_code", f"KH{customer.customer_id:04d}"),
                "full_name": customer.full_name,
                "phone": customer.phone,
                "date_of_birth": customer.date_of_birth,
                "gender": customer.gender,
                "address": customer.address,
                "playing_level": customer.playing_level,
                "status": customer.status,
            }
            data["full_name"] = customer.full_name
            data["code"] = data["profile"]["code"]
    return data


def get_account(actor, account_id):
    require_active_admin(actor)
    account = (
        Account.objects.select_related("admin_profile", "staff_profile", "customer")
        .filter(pk=account_id)
        .first()
    )
    if account is None:
        raise AccountNotFound("Account not found")
    return account_data(account)


def list_accounts(actor):
    require_active_admin(actor)
    return [
        account_data(account)
        for account in Account.objects.select_related("admin_profile", "staff_profile", "customer").order_by("account_id")
    ]


def list_account_page(actor, *, page=1, q="", role=None, status=None, page_size=20):
    require_active_admin(actor)
    query = Account.objects.select_related("admin_profile", "staff_profile", "customer").order_by("-account_id")
    if q and q.strip():
        term = q.strip()
        query = query.filter(
            Q(email__icontains=term)
            | Q(admin_profile__full_name__icontains=term)
            | Q(admin_profile__admin_code__icontains=term)
            | Q(staff_profile__full_name__icontains=term)
            | Q(staff_profile__staff_code__icontains=term)
            | Q(customer__full_name__icontains=term)
        )
    if role:
        query = query.filter(role=normalize_account_role(role))
    if status:
        query = query.filter(status=normalize_account_status(status))
    result = Paginator(query, page_size).get_page(page)
    result.object_list = [account_data(account) for account in result.object_list]
    return result


def count_active_admins():
    from .constants import AccountRole, AccountStatus

    return Account.objects.filter(role=AccountRole.ADMIN, status=AccountStatus.ACTIVE).count()

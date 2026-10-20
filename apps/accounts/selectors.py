from django.core.paginator import Paginator
from django.db.models import Q

from .constants import AccountRole, normalize_account_role, normalize_account_status
from .errors import AccountNotFound
from .models import Account
from .permissions import require_active_admin


ACCOUNT_PUBLIC_FIELDS = ("account_id", "email", "role", "status", "last_login", "created_at", "updated_at")


def account_data(account):
    return {
        "account_id": account.account_id,
        "email": account.email,
        "role": account.role,
        "status": account.status,
        "last_login_at": account.last_login,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
        "profile": {
            "type": account.role,
            "code": account.code,
            "full_name": account.full_name,
            "phone": account.phone,
            "date_of_birth": account.date_of_birth,
            "gender": account.gender,
            "address": account.address,
            "playing_level": account.playing_level,
            "status": account.status,
        },
        "full_name": account.full_name,
        "code": account.code,
    }


def get_account(actor, account_id):
    require_active_admin(actor)
    account = Account.objects.filter(pk=account_id).first()
    if account is None:
        raise AccountNotFound("Account not found")
    return account_data(account)


def list_accounts(actor):
    require_active_admin(actor)
    return [
        account_data(account)
        for account in Account.objects.order_by("account_id")
    ]


def list_account_page(actor, *, page=1, q="", role=None, status=None, page_size=20):
    require_active_admin(actor)
    query = Account.objects.order_by("-account_id")
    if q and q.strip():
        term = q.strip()
        code_filter = Q()
        if term.upper().startswith(("AD", "ST", "KH")):
            try:
                code_id = int(term[2:])
                code_filter = Q(account_id=code_id)
            except ValueError:
                pass
        elif term.isdigit():
            code_filter = Q(account_id=int(term))

        query = query.filter(
            Q(email__icontains=term)
            | Q(full_name__icontains=term)
            | Q(phone__icontains=term)
            | code_filter
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

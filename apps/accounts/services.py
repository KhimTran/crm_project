from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError

from apps.customers.constants import CustomerStatus
from apps.customers.models import Customer
from .constants import AccountRole, AccountStatus, normalize_account_role, normalize_account_status
from .errors import (
    AccountAlreadyActive, AccountAlreadyLocked, AccountDeleteProtectedError,
    AccountNotFound, AccountPermissionDenied, CannotDeleteOwnAccount, CannotLockOwnAccount,
    CannotDemoteAdmin, CannotDemoteOwnAccount, CannotModifyOtherAdmin, CannotPromoteToAdmin,
    DuplicateAccountEmail, InvalidAccountRole, LastActiveAdminError, PasswordValidationError,
)
from .models import Account
from .permissions import require_active_admin
from .selectors import account_data
from .managers import AccountManager


def _locked_target(account_id):
    account = Account.objects.select_for_update().filter(pk=account_id).first()
    if account is None:
        raise AccountNotFound("Account not found")
    return account


def _lock_active_admins():
    # Lock in PK order so simultaneous demotions/deletions serialize on MySQL.
    return list(Account.objects.filter(role=AccountRole.ADMIN, status=AccountStatus.ACTIVE)
                .order_by("account_id").select_for_update().values_list("account_id", flat=True))


def _protect_final_admin(account, active_admin_ids):
    if account.account_id in active_admin_ids and len(active_admin_ids) <= 1:
        raise LastActiveAdminError("The final active admin must remain active")


def _has_protected_references(account_id):
    # The SQL schema uses RESTRICT for surveys and SET NULL for feedbacks.
    # Even SET NULL would erase handler attribution, so both block hard delete.
    references = (("feedbacks", "handled_by"),
                  ("surveys", "created_by"), ("django_admin_log", "user_id"))
    existing_tables = set(connection.introspection.table_names())
    with connection.cursor() as cursor:
        for table, column in references:
            if table in existing_tables:
                cursor.execute(f"SELECT 1 FROM `{table}` WHERE `{column}` = %s LIMIT 1", [account_id])
                if cursor.fetchone() is not None:
                    return True
    return False


@transaction.atomic
def create_account(actor, *, email, role, status, password):
    require_active_admin(actor, for_update=True)
    role = normalize_account_role(role)
    status = normalize_account_status(status)
    email = AccountManager.normalize_account_email(email)
    if Account.objects.filter(email=email).exists():
        raise DuplicateAccountEmail("Email is already in use")
    try:
        account = Account.objects.create_user(email, password, role=role, status=status)
    except IntegrityError as exc:
        raise DuplicateAccountEmail("Email is already in use") from exc
    if role == AccountRole.CUSTOMER:
        # Admin-created profiles start with an empty name; the CRM list shows "(Chưa cập nhật)".
        from apps.customers.provisioning import ensure_customer_profile
        ensure_customer_profile(account.pk, full_name="")
    return account_data(account)


@transaction.atomic
def lock_account(actor, account_id):
    require_active_admin(actor)
    active_admin_ids = _lock_active_admins()
    if actor.pk not in active_admin_ids:
        raise AccountPermissionDenied("An active admin account is required")
    account = _locked_target(account_id)
    if actor.pk == account.account_id:
        raise CannotLockOwnAccount("An admin cannot lock their own account")
    if account.role == AccountRole.ADMIN:
        raise CannotModifyOtherAdmin("Không thể khóa tài khoản của một ADMIN khác")
    if account.status == AccountStatus.LOCKED:
        raise AccountAlreadyLocked("Account is already locked")
    _protect_final_admin(account, active_admin_ids)
    Account.objects.filter(pk=account.pk).update(status=AccountStatus.LOCKED)
    account.refresh_from_db()
    return account_data(account)


@transaction.atomic
def unlock_account(actor, account_id):
    require_active_admin(actor, for_update=True)
    account = _locked_target(account_id)
    if account.status == AccountStatus.ACTIVE:
        raise AccountAlreadyActive("Account is already active")
    Account.objects.filter(pk=account.pk).update(status=AccountStatus.ACTIVE)
    account.refresh_from_db()
    return account_data(account)


@transaction.atomic
def change_account_role(actor, account_id, role):
    require_active_admin(actor)
    role = normalize_account_role(role)
    active_admin_ids = _lock_active_admins()
    if actor.pk not in active_admin_ids:
        raise AccountPermissionDenied("An active admin account is required")
    account = _locked_target(account_id)
    if account.role == role:
        return account_data(account)

    if account.role != AccountRole.ADMIN and role == AccountRole.ADMIN:
        raise CannotPromoteToAdmin("Không thể nâng quyền tài khoản thường thành ADMIN")

    if account.role == AccountRole.ADMIN and role != AccountRole.ADMIN:
        if actor.pk == account.account_id:
            raise CannotDemoteOwnAccount("Không thể tự hạ quyền ADMIN của chính mình")
        raise CannotDemoteAdmin("Không thể hạ quyền của một ADMIN khác")

    if role != AccountRole.ADMIN:
        _protect_final_admin(account, active_admin_ids)
    Account.objects.filter(pk=account.pk).update(role=role)
    account.refresh_from_db()

    if role == AccountRole.CUSTOMER:
        from apps.customers.provisioning import ensure_customer_profile
        ensure_customer_profile(account.pk, full_name="")

    return account_data(account)


@transaction.atomic
def reset_account_password(actor, account_id, new_password):
    require_active_admin(actor, for_update=True)
    account = _locked_target(account_id)
    if account.role == AccountRole.ADMIN and actor.pk != account.account_id:
        raise CannotModifyOtherAdmin("Không thể đặt lại mật khẩu của một ADMIN khác")
    try:
        validate_password(new_password, account)
    except (ValidationError, TypeError, ValueError) as exc:
        raise PasswordValidationError("Password does not meet validation requirements") from exc
    account.set_password(new_password)
    account.save(update_fields=["password", "updated_at"])
    return {"account_id": account.account_id}


@transaction.atomic
def delete_account(actor, account_id):
    require_active_admin(actor)
    active_admin_ids = _lock_active_admins()
    if actor.pk not in active_admin_ids:
        raise AccountPermissionDenied("An active admin account is required")
    account = _locked_target(account_id)
    if actor.pk == account.account_id:
        raise CannotDeleteOwnAccount("An admin cannot delete their own account")
    if account.role == AccountRole.ADMIN:
        raise CannotModifyOtherAdmin("Không thể xóa tài khoản của một ADMIN khác")
    _protect_final_admin(account, active_admin_ids)

    # Any account that owns a customer profile is soft-deleted: the profile becomes DELETED,
    # the account is locked and orders/feedbacks/surveys stay attached to it.
    customer = Customer.objects.select_for_update().filter(account_id=account.pk).first()
    if customer is not None:
        from apps.customers.services import delete_customer

        if customer.status != CustomerStatus.DELETED:
            delete_customer(customer.pk)
        elif account.status != AccountStatus.LOCKED:
            Account.objects.filter(pk=account.pk).update(status=AccountStatus.LOCKED)
        return {"account_id": account_id, "customer_deleted": True}

    if _has_protected_references(account.account_id):
        raise AccountDeleteProtectedError("Account has business records; lock it instead")

    try:
        account.delete()
    except (ProtectedError, IntegrityError) as exc:
        raise AccountDeleteProtectedError("Account has business records; lock it instead") from exc
    return {"account_id": account_id}

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError

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
    references = (
        ("feedbacks", "handled_by"),
        ("feedbacks", "customer_id"),
        ("surveys", "created_by"),
        ("django_admin_log", "user_id"),
    )
    existing_tables = set(connection.introspection.table_names())
    with connection.cursor() as cursor:
        for table, column in references:
            if table in existing_tables:
                cursor.execute(f"SELECT 1 FROM `{table}` WHERE `{column}` = %s LIMIT 1", [account_id])
                if cursor.fetchone() is not None:
                    return True
        if "survey_recipients" in existing_tables and "survey_responses" in existing_tables:
            cursor.execute(
                """SELECT 1 FROM `survey_recipients` r
                   JOIN `survey_responses` resp ON r.recipient_id = resp.recipient_id
                   WHERE r.customer_id = %s LIMIT 1""",
                [account_id],
            )
            if cursor.fetchone() is not None:
                return True
    return False


@transaction.atomic
def create_account(actor, *, email, role, status, password, profile_data=None):
    require_active_admin(actor, for_update=True)
    role = normalize_account_role(role)
    status = normalize_account_status(status)
    email = AccountManager.normalize_account_email(email)
    if Account.objects.filter(email=email).exists():
        raise DuplicateAccountEmail("Email is already in use")

    profile_kwargs = profile_data or {}
    fields_to_set = {
        "full_name": profile_kwargs.get("full_name") or "",
        "phone": profile_kwargs.get("phone") or None,
        "date_of_birth": profile_kwargs.get("date_of_birth") or None,
        "gender": profile_kwargs.get("gender") or None,
        "address": profile_kwargs.get("address") or None,
        "playing_level": profile_kwargs.get("playing_level") or None,
    }
    try:
        account = Account.objects.create_user(
            email, password, role=role, status=status,
            **{k: v for k, v in fields_to_set.items() if v is not None or k == "full_name"}
        )
    except IntegrityError as exc:
        raise DuplicateAccountEmail("Email is already in use") from exc
    return account_data(account)


@transaction.atomic
def update_account_profile(actor, account_id, profile_data):
    require_active_admin(actor)
    account = _locked_target(account_id)
    if "email" in profile_data and profile_data["email"]:
        new_email = AccountManager.normalize_account_email(profile_data["email"])
        if Account.objects.filter(email=new_email).exclude(pk=account.pk).exists():
            raise DuplicateAccountEmail("Email is already in use")
        account.email = new_email

    allowed_fields = ("full_name", "phone", "date_of_birth", "gender", "address", "playing_level")
    for k in allowed_fields:
        if k in profile_data:
            val = profile_data[k] or (None if k != "full_name" else "")
            setattr(account, k, val)
    account.save()
    return account


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
        raise CannotModifyOtherAdmin("Cannot lock another ADMIN account")
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
        raise CannotPromoteToAdmin("Cannot promote a standard account to ADMIN")

    if account.role == AccountRole.ADMIN and role != AccountRole.ADMIN:
        if actor.pk == account.account_id:
            raise CannotDemoteOwnAccount("Cannot demote your own ADMIN account")
        raise CannotDemoteAdmin("Cannot demote another ADMIN")

    if role != AccountRole.ADMIN:
        _protect_final_admin(account, active_admin_ids)
    Account.objects.filter(pk=account.pk).update(role=role)
    account.refresh_from_db()
    return account_data(account)


@transaction.atomic
def reset_account_password(actor, account_id, new_password):
    require_active_admin(actor, for_update=True)
    account = _locked_target(account_id)
    if account.role == AccountRole.ADMIN and actor.pk != account.account_id:
        raise CannotModifyOtherAdmin("Cannot reset password of another ADMIN")
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
        raise CannotModifyOtherAdmin("Cannot delete another ADMIN account")
    _protect_final_admin(account, active_admin_ids)

    if _has_protected_references(account.account_id):
        raise AccountDeleteProtectedError("Account has business records; lock it instead")

    try:
        account.delete()
    except (ProtectedError, IntegrityError) as exc:
        raise AccountDeleteProtectedError("Account has business records; lock it instead") from exc
    return {"account_id": account_id}

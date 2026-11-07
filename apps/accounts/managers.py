from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import models

from .constants import AccountRole, AccountStatus, normalize_account_role, normalize_account_status
from .errors import InvalidAccountRole


def resolve_account_role(code, *, using=None):
    from django.apps import apps
    try:
        code = normalize_account_role(code)
    except InvalidAccountRole as exc:
        raise ValidationError(str(exc)) from exc
    Role = apps.get_model("accounts", "Role")
    try:
        return Role.objects.db_manager(using).get(role_code=code)
    except Role.DoesNotExist as exc:
        raise ValidationError({"role": "Required role is missing. Run initialize_roles before creating accounts."},
                              code="missing_role") from exc


class AccountQuerySet(models.QuerySet):
    def update(self, **kwargs):
        if "email" in kwargs:
            raise ValidationError({"email": "Account email cannot be changed"})
        if "role" in kwargs and isinstance(kwargs["role"], str):
            kwargs["role"] = resolve_account_role(kwargs["role"], using=self.db)
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        if "email" in fields:
            raise ValidationError({"email": "Account email cannot be changed"})
        return super().bulk_update(objs, fields, batch_size=batch_size)


class AccountManager(BaseUserManager.from_queryset(AccountQuerySet)):
    def get(self, *args, **kwargs):
        # Django's ModelBackend uses this for both login and session reloads.
        # Join the current Role in that same fresh read; never cache across requests.
        return self.get_queryset().select_related("role").get(*args, **kwargs)

    @staticmethod
    def normalize_account_email(email):
        if not isinstance(email, str) or not email.strip():
            raise ValueError("An email address is required")
        return email.strip().lower()

    def create_user(self, email, password=None, **extra_fields):
        email = self.normalize_account_email(email)
        if not password:
            raise ValueError("A password is required")
        extra_fields.setdefault("role", AccountRole.CUSTOMER)
        extra_fields.setdefault("status", AccountStatus.ACTIVE)
        try:
            extra_fields["role"] = normalize_account_role(extra_fields["role"])
            extra_fields["status"] = normalize_account_status(extra_fields["status"])
        except (InvalidAccountRole, ValueError) as exc:
            raise ValidationError(str(exc)) from exc
        extra_fields["role"] = resolve_account_role(extra_fields["role"], using=self.db)
        account = self.model(email=email, **extra_fields)
        validate_password(password, account)
        account.set_password(password)
        account.save(using=self._db)
        return account

    def create_superuser(self, email, password=None, **extra_fields):
        try:
            if "role" in extra_fields:
                extra_fields["role"] = normalize_account_role(extra_fields["role"])
            if "status" in extra_fields:
                extra_fields["status"] = normalize_account_status(extra_fields["status"])
        except (InvalidAccountRole, ValueError) as exc:
            raise ValueError(str(exc)) from exc
        if extra_fields.get("role", AccountRole.ADMIN) != AccountRole.ADMIN:
            raise ValueError("An admin account must have the ADMIN role")
        if extra_fields.get("status", AccountStatus.ACTIVE) != AccountStatus.ACTIVE:
            raise ValueError("An admin account must be ACTIVE")
        extra_fields["role"] = AccountRole.ADMIN
        extra_fields["status"] = AccountStatus.ACTIVE
        return self.create_user(email, password, **extra_fields)

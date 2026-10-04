from django.db import models

from .errors import InvalidAccountRole


class AccountRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    CUSTOMER = "CUSTOMER", "Customer"


class AccountStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    LOCKED = "LOCKED", "Locked"


def normalize_account_choice(value):
    return value.strip().upper() if isinstance(value, str) else value


def normalize_account_role(value):
    role = normalize_account_choice(value)
    if role not in AccountRole.values:
        raise InvalidAccountRole("Role must be ADMIN or CUSTOMER")
    return role


def normalize_account_status(value):
    status = normalize_account_choice(value)
    if status not in AccountStatus.values:
        raise ValueError("Status must be ACTIVE or LOCKED")
    return status

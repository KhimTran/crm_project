from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.hashers import identify_hasher, is_password_usable
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .constants import AccountRole, AccountStatus, normalize_account_role, normalize_account_status
from .errors import InvalidAccountRole
from .managers import AccountManager


class Account(AbstractBaseUser, PermissionsMixin):
    account_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255)
    # Django's authentication attributes map to the official SQL columns.
    password = models.CharField(max_length=255, db_column="password_hash")
    role = models.CharField(max_length=20, choices=AccountRole.choices, default=AccountRole.CUSTOMER)
    status = models.CharField(max_length=20, choices=AccountStatus.choices, default=AccountStatus.ACTIVE)
    last_login = models.DateTimeField(db_column="last_login_at", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "accounts"
        constraints = [
            models.UniqueConstraint(fields=["email"], name="uq_accounts_email"),
            models.CheckConstraint(condition=models.Q(role__in=AccountRole.values), name="chk_accounts_role"),
            models.CheckConstraint(condition=models.Q(status__in=AccountStatus.values), name="chk_accounts_status"),
        ]

    @property
    def is_active(self):
        return self.status == AccountStatus.ACTIVE

    @property
    def is_staff(self):
        return self.is_active and self.role == AccountRole.ADMIN

    @property
    def is_superuser(self):
        return self.is_staff

    def save(self, *args, **kwargs):
        self.email = AccountManager.normalize_account_email(self.email)
        if self.pk is not None:
            saved_email = type(self).objects.filter(pk=self.pk).values_list("email", flat=True).first()
            if saved_email is not None and saved_email != self.email:
                raise ValidationError({"email": "Account email cannot be changed"})
        try:
            self.role = normalize_account_role(self.role)
            self.status = normalize_account_status(self.status)
        except (InvalidAccountRole, ValueError) as exc:
            raise ValidationError(str(exc)) from exc
        if is_password_usable(self.password):
            try:
                identify_hasher(self.password)
            except ValueError as exc:
                raise ValidationError({"password": "Use set_password() to assign a password"}) from exc
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email

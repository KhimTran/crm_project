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
    full_name = models.CharField(max_length=150, default="", blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    playing_level = models.CharField(max_length=30, null=True, blank=True)
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

    @property
    def role_id(self):
        return self.role

    @property
    def admin(self):
        return self if self.role == AccountRole.ADMIN else None

    @property
    def staff(self):
        return self if self.role == AccountRole.MANAGER else None

    @property
    def admin_profile(self):
        return self if self.role == AccountRole.ADMIN else None

    @property
    def staff_profile(self):
        return self if self.role == AccountRole.MANAGER else None

    @property
    def customer(self):
        return self if self.role == AccountRole.CUSTOMER else None

    @property
    def customer_id(self):
        return self.account_id

    @property
    def customer_code(self):
        return f"KH{self.account_id:04d}"

    @property
    def admin_code(self):
        return f"AD{self.account_id:04d}"

    @property
    def staff_code(self):
        return f"ST{self.account_id:04d}"


    @property
    def code(self):
        if self.role == AccountRole.ADMIN:
            return self.admin_code
        elif self.role == AccountRole.MANAGER:
            return self.staff_code
        return self.customer_code

    @property
    def profile(self):
        return self

    @property
    def account(self):
        return self

    @account.setter
    def account(self, value):
        if value is not None and hasattr(value, "pk") and value.pk:
            self.pk = value.pk
            if hasattr(value, "email") and value.email:
                self.email = value.email

    @property
    def display_name(self):
        return self.full_name or self.email

    def save(self, *args, **kwargs):
        self.email = AccountManager.normalize_account_email(self.email)
        if self.pk is not None:
            saved = type(self).objects.filter(pk=self.pk).values("email", "role").first()
            if saved is not None and saved["email"] != self.email:
                if saved["role"] != AccountRole.CUSTOMER:
                    raise ValidationError({"email": "Account email cannot be changed"})
                if type(self).objects.filter(email=self.email).exclude(pk=self.pk).exists():
                    raise ValidationError({"email": "Email is already in use"})
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


class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_code = models.CharField(max_length=20, unique=True)
    role_name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "roles"
        constraints = [
            models.UniqueConstraint(fields=["role_code"], name="uq_roles_code"),
            models.CheckConstraint(condition=models.Q(role_code__in=AccountRole.values), name="chk_roles_code"),
        ]

    def __str__(self):
        return f"{self.role_code} - {self.role_name}"


class Admin(Account):
    class Meta:
        proxy = True

    def __str__(self):
        return f"{self.admin_code} - {self.full_name}"


class Staff(Account):
    class Meta:
        proxy = True

    def __str__(self):
        return f"{self.staff_code} - {self.full_name}"

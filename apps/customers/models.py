from django.conf import settings
from django.db import models

from apps.accounts.models import Account
from .constants import Gender, PlayingLevel


class CustomerQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs):
        new_kwargs = {}
        for k, v in kwargs.items():
            if k.startswith("account__"):
                new_kwargs[k[len("account__"):]] = v
            elif k in ("account", "customer"):
                new_kwargs["account_id"] = getattr(v, "pk", v)
            elif k in ("account__in", "customer__in"):
                new_kwargs["account_id__in"] = [getattr(x, "pk", x) for x in v]
            elif k == "customer_id":
                new_kwargs["account_id"] = v
            elif k.startswith("customer_id__"):
                new_kwargs["account_id" + k[len("customer_id"):]] = v
            else:
                new_kwargs[k] = v
        return super().filter(*args, **new_kwargs)

    def exclude(self, *args, **kwargs):
        new_kwargs = {}
        for k, v in kwargs.items():
            if k.startswith("account__"):
                new_kwargs[k[len("account__"):]] = v
            elif k in ("account", "customer"):
                new_kwargs["account_id"] = getattr(v, "pk", v)
            elif k in ("account__in", "customer__in"):
                new_kwargs["account_id__in"] = [getattr(x, "pk", x) for x in v]
            elif k == "customer_id":
                new_kwargs["account_id"] = v
            elif k.startswith("customer_id__"):
                new_kwargs["account_id" + k[len("customer_id"):]] = v
            else:
                new_kwargs[k] = v
        return super().exclude(*args, **new_kwargs)

    def order_by(self, *field_names):
        new_field_names = [
            "account_id" if f == "customer_id" else ("-account_id" if f == "-customer_id" else f)
            for f in field_names
        ]
        return super().order_by(*new_field_names)

    def select_related(self, *fields):
        new_fields = [f for f in fields if f != "account"]
        if new_fields:
            return super().select_related(*new_fields)
        return self

    def values(self, *fields, **expressions):
        fields = ["account_id" if f == "customer_id" else f for f in fields]
        return super().values(*fields, **expressions)

    def values_list(self, *fields, **expressions):
        fields = ["account_id" if f == "customer_id" else f for f in fields]
        return super().values_list(*fields, **expressions)


class CustomerManager(models.Manager.from_queryset(CustomerQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(role="CUSTOMER")

    def create(self, **kwargs):
        account = kwargs.pop("account", None)
        if account is not None:
            account.refresh_from_db()
            for k, v in kwargs.items():
                setattr(account, k, v)
            account.role = "CUSTOMER"
            account.save()
            return self.get(pk=account.pk)
        kwargs.setdefault("role", "CUSTOMER")
        return super().create(**kwargs)


class Customer(Account):
    objects = CustomerManager()

    class Meta:
        proxy = True

    @property
    def customer_id(self):
        return self.account_id

    @property
    def customer_code(self):
        return f"KH{self.account_id:04d}"

    @property
    def account(self):
        return self

    @account.setter
    def account(self, value):
        if value is not None and hasattr(value, "pk") and value.pk:
            self.account_id = value.pk
            if hasattr(value, "email") and value.email:
                self.email = value.email

    @property
    def playing_level_label(self):
        return PlayingLevel(self.playing_level).label if self.playing_level in PlayingLevel.values else self.playing_level

    @property
    def gender_label(self):
        return Gender(self.gender).label if self.gender in Gender.values else self.gender


class CustomerPreference(models.Model):
    preference_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="customer_id",
        related_name="customerpreference_set",
    )
    preference_type = models.CharField(max_length=50)
    preference_value = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customer_preferences"

    @property
    def account(self):
        return self.customer

    @property
    def customer_preferences(self):
        return self.customerpreference_set

from django.conf import settings
from django.db import models


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    account = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, db_column="account_id")
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    playing_level = models.CharField(max_length=30, null=True, blank=True)
    status = models.CharField(max_length=20, default="ACTIVE")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "customers"


class CustomerPreference(models.Model):
    preference_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, db_column="customer_id")
    preference_type = models.CharField(max_length=50)
    preference_value = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customer_preferences"

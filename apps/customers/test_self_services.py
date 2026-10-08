from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Account
from .models import Customer, CustomerPreference
from .self_service_forms import CustomerProfileForm
from .self_services import register_customer, update_own_profile


class CustomerSelfServiceTests(TestCase):
    password = "StrongPass!2026"

    def register(self, email="owner@customer.test", **profile):
        return register_customer(email=email, password=self.password, profile_data={"full_name": "Khách hàng", **profile})

    def test_registration_normalizes_email_hashes_password_and_whitelists_profile(self):
        account = self.register(" Owner@Customer.TEST ", role="ADMIN", status="LOCKED", groups="CRM_MANAGER", account_id=123)
        self.assertEqual(account.email, "owner@customer.test")
        self.assertEqual((account.role, account.status), ("CUSTOMER", "ACTIVE"))
        self.assertTrue(account.check_password(self.password))
        self.assertFalse(account.groups.exists())
        self.assertFalse(account.user_permissions.exists())
        self.assertEqual(Customer.objects.get(account=account).status, "ACTIVE")

    def test_duplicate_and_invalid_password_leave_no_partial_rows(self):
        self.register()
        with self.assertRaises(ValidationError):
            self.register("OWNER@CUSTOMER.TEST")
        with self.assertRaises(ValidationError):
            register_customer(email="weak@customer.test", password="123", profile_data={"full_name": "Weak"})
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(Customer.objects.count(), 1)

    def test_profile_failure_rolls_back_account_creation(self):
        with patch("apps.customers.self_services.Customer.objects.create", side_effect=IntegrityError("profile failure")):
            with self.assertRaises(IntegrityError):
                self.register()
        self.assertEqual(Account.objects.count(), 0)
        self.assertEqual(Customer.objects.count(), 0)

    def test_profile_validation_phone_future_date_and_lengths(self):
        for fields, field in (({"phone": "abc"}, "phone"), ({"phone": "123"}, "phone"),
                              ({"date_of_birth": timezone.localdate() + timedelta(days=1)}, "date_of_birth"),
                              ({"gender": "x" * 21}, "gender"), ({"playing_level": "x" * 31}, "playing_level")):
            with self.subTest(fields=fields):
                form = CustomerProfileForm({"full_name": "Customer", **fields})
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)
        self.assertTrue(CustomerProfileForm({"full_name": "Customer", "phone": "+84 912-345-678"}).is_valid())

    def test_profile_and_preferences_never_modify_account_or_other_customer(self):
        owner = self.register()
        other = self.register("other@customer.test")
        other_customer = Customer.objects.get(account=other)
        update_own_profile(owner, profile_data={"full_name": "Updated", "account_id": other.pk,
                           "email": "changed@test.test", "role": "ADMIN", "status": "DELETED"},
                           preferences=[{"preference_type": "CATEGORY", "preference_value": "Badminton rackets"}])
        owner.refresh_from_db()
        self.assertEqual((owner.email, owner.role, owner.status), ("owner@customer.test", "CUSTOMER", "ACTIVE"))
        self.assertEqual(Customer.objects.get(account=owner).full_name, "Updated")
        other_customer.refresh_from_db()
        self.assertEqual(other_customer.full_name, "Khách hàng")
        self.assertEqual(CustomerPreference.objects.get().customer.account_id, owner.pk)

    def test_foreign_preference_and_invalid_preference_roll_back(self):
        owner = self.register()
        other = self.register("other@customer.test")
        preference = CustomerPreference.objects.create(customer=Customer.objects.get(account=other), preference_type="CATEGORY", preference_value="Other")
        with self.assertRaises(PermissionDenied):
            update_own_profile(owner, profile_data={"full_name": "Stolen"}, preferences=[{"preference_id": preference.pk, "DELETE": True}])
        self.assertTrue(CustomerPreference.objects.filter(pk=preference.pk).exists())
        with self.assertRaises(ValidationError):
            update_own_profile(owner, profile_data={"full_name": "Changed"}, preferences=[
                {"preference_type": "CATEGORY", "preference_value": "Valid"},
                {"preference_type": "CATEGORY", "preference_value": "x" * 151},
            ])
        self.assertFalse(CustomerPreference.objects.filter(customer__account=owner).exists())
        self.assertEqual(Customer.objects.get(account=owner).full_name, "Khách hàng")

    def test_locked_deleted_and_admin_cannot_update_customer_profile(self):
        owner = self.register()
        Account.objects.filter(pk=owner.pk).update(status="LOCKED")
        with self.assertRaises(PermissionDenied):
            update_own_profile(owner, profile_data={"full_name": "Locked"}, preferences=[])
        Account.objects.filter(pk=owner.pk).update(status="ACTIVE")
        Customer.objects.filter(account=owner).update(status="DELETED", deleted_at=timezone.now())
        with self.assertRaises(PermissionDenied):
            update_own_profile(owner, profile_data={"full_name": "Deleted"}, preferences=[])
        admin = Account.objects.create_superuser("admin@customer.test", self.password)
        with self.assertRaises(PermissionDenied):
            update_own_profile(admin, profile_data={"full_name": "Admin"}, preferences=[])

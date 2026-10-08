from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Account
from apps.catalog.models import Category
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
                           category_ids=[Category.objects.create(category_name="Badminton rackets").pk])
        owner.refresh_from_db()
        self.assertEqual((owner.email, owner.role, owner.status), ("owner@customer.test", "CUSTOMER", "ACTIVE"))
        self.assertEqual(Customer.objects.get(account=owner).full_name, "Updated")
        other_customer.refresh_from_db()
        self.assertEqual(other_customer.full_name, "Khách hàng")
        self.assertEqual(CustomerPreference.objects.get().customer.account_id, owner.pk)

    def test_foreign_preference_and_invalid_category_roll_back(self):
        owner = self.register()
        other = self.register("other@customer.test")
        preference = CustomerPreference.objects.create(customer=Customer.objects.get(account=other), preference_type="CATEGORY", preference_value="Other")
        with self.assertRaises(ValidationError):
            update_own_profile(owner, profile_data={"full_name": "Stolen"}, remove_preference_ids=[preference.pk])
        self.assertTrue(CustomerPreference.objects.filter(pk=preference.pk).exists())
        with self.assertRaises(ValidationError):
            update_own_profile(owner, profile_data={"full_name": "Changed"}, category_ids=[999999])
        self.assertFalse(CustomerPreference.objects.filter(customer__account=owner).exists())
        self.assertEqual(Customer.objects.get(account=owner).full_name, "Khách hàng")

    def test_locked_deleted_and_admin_cannot_update_customer_profile(self):
        owner = self.register()
        Account.objects.filter(pk=owner.pk).update(status="LOCKED")
        with self.assertRaises(PermissionDenied):
            update_own_profile(owner, profile_data={"full_name": "Locked"})
        Account.objects.filter(pk=owner.pk).update(status="ACTIVE")
        Customer.objects.filter(account=owner).update(status="DELETED", deleted_at=timezone.now())
        with self.assertRaises(PermissionDenied):
            update_own_profile(owner, profile_data={"full_name": "Deleted"})
        admin = Account.objects.create_superuser("admin@customer.test", self.password)
        with self.assertRaises(PermissionDenied):
            update_own_profile(admin, profile_data={"full_name": "Admin"})

    def test_category_sync_multiple_remove_and_repeat_without_duplicates(self):
        owner = self.register()
        customer = Customer.objects.get(account=owner)
        first = Category.objects.create(category_name="Rackets")
        second = Category.objects.create(category_name="Shoes")
        for _ in range(2):
            update_own_profile(owner, profile_data={"full_name": "Updated"}, category_ids=[first.pk, second.pk, first.pk])
        self.assertEqual(set(customer.customerpreference_set.values_list("preference_type", "preference_value")),
                         {("CATEGORY", "Rackets"), ("CATEGORY", "Shoes")})
        self.assertEqual(customer.customerpreference_set.count(), 2)
        update_own_profile(owner, profile_data={"full_name": "Updated"}, category_ids=[second.pk])
        self.assertEqual(list(customer.customerpreference_set.values_list("preference_value", flat=True)), ["Shoes"])
        update_own_profile(owner, profile_data={"full_name": "Updated"}, category_ids=[])
        self.assertFalse(customer.customerpreference_set.exists())

    def test_unmatched_inactive_and_other_types_preserved_and_explicit_removal_scoped(self):
        owner = self.register()
        customer = Customer.objects.get(account=owner)
        Category.objects.create(category_name="Old shoes", status="INACTIVE")
        legacy = CustomerPreference.objects.create(customer=customer, preference_type="CATEGORY", preference_value="Missing category")
        inactive = CustomerPreference.objects.create(customer=customer, preference_type="CATEGORY", preference_value="Old shoes")
        brand = CustomerPreference.objects.create(customer=customer, preference_type="BRAND", preference_value="Yonex")
        style = CustomerPreference.objects.create(customer=customer, preference_type="PLAY_STYLE", preference_value="Tấn công")
        update_own_profile(owner, profile_data={"full_name": "Updated"})
        self.assertEqual(customer.customerpreference_set.count(), 4)
        with self.assertRaises(ValidationError):
            update_own_profile(owner, profile_data={"full_name": "Must not save"}, remove_preference_ids=[brand.pk])
        update_own_profile(owner, profile_data={"full_name": "Updated"}, remove_preference_ids=[legacy.pk])
        self.assertFalse(CustomerPreference.objects.filter(pk=legacy.pk).exists())
        self.assertEqual(set(customer.customerpreference_set.values_list("pk", flat=True)), {inactive.pk, brand.pk, style.pk})

    def test_duplicate_existing_rows_and_duplicate_category_names_store_one_name(self):
        owner = self.register()
        customer = Customer.objects.get(account=owner)
        first = Category.objects.create(category_name="Rackets")
        second = Category.objects.create(category_name="Rackets")
        for _ in range(2):
            CustomerPreference.objects.create(customer=customer, preference_type="CATEGORY", preference_value="Rackets")
        update_own_profile(owner, profile_data={"full_name": "Updated"}, category_ids=[first.pk, second.pk])
        self.assertEqual(customer.customerpreference_set.count(), 1)

    def test_inactive_forged_category_rejected_and_create_failure_atomic(self):
        owner = self.register()
        customer = Customer.objects.get(account=owner)
        first = Category.objects.create(category_name="Rackets")
        second = Category.objects.create(category_name="Shoes")
        inactive = Category.objects.create(category_name="Inactive", status="INACTIVE")
        existing = CustomerPreference.objects.create(customer=customer, preference_type="CATEGORY", preference_value="Rackets")
        for invalid in (inactive.pk, 999999, "bad", -1):
            with self.subTest(category_id=invalid), self.assertRaises(ValidationError):
                update_own_profile(owner, profile_data={"full_name": "Invalid"}, category_ids=[first.pk, invalid])
        with patch("apps.customers.self_services.CustomerPreference.objects.bulk_create", side_effect=IntegrityError("failure")):
            with self.assertRaises(IntegrityError):
                update_own_profile(owner, profile_data={"full_name": "Changed"}, category_ids=[second.pk])
        self.assertTrue(CustomerPreference.objects.filter(pk=existing.pk).exists())
        customer.refresh_from_db()
        self.assertEqual(customer.full_name, "Khách hàng")

    def test_tv4_choices_reject_unknown_and_preserve_then_update_legacy(self):
        owner = self.register(gender="MALE", playing_level="RECREATIONAL")
        customer = Customer.objects.get(account=owner)
        for field, values in (("gender", ("MALE", "FEMALE", "OTHER")),
                              ("playing_level", ("BEGINNER", "RECREATIONAL", "COMPETITIVE"))):
            for value in values:
                update_own_profile(owner, profile_data={"full_name": "Updated", field: value})
                customer.refresh_from_db()
                self.assertEqual(getattr(customer, field), value)
            with self.assertRaises(ValidationError):
                update_own_profile(owner, profile_data={"full_name": "Invalid", field: "UNKNOWN"})
        Customer.objects.filter(pk=customer.pk).update(gender="Old gender", playing_level="INTERMEDIATE")
        update_own_profile(owner, profile_data={"full_name": "Legacy preserved"})
        customer.refresh_from_db()
        self.assertEqual((customer.gender, customer.playing_level), ("Old gender", "INTERMEDIATE"))
        update_own_profile(owner, profile_data={"full_name": "Legacy preserved", "gender": "Old gender", "playing_level": "INTERMEDIATE"})
        update_own_profile(owner, profile_data={"full_name": "Changed", "gender": "FEMALE", "playing_level": "COMPETITIVE"})
        customer.refresh_from_db()
        self.assertEqual((customer.gender, customer.playing_level), ("FEMALE", "COMPETITIVE"))
        update_own_profile(owner, profile_data={"full_name": "Cleared", "gender": "", "playing_level": ""})
        customer.refresh_from_db()
        self.assertEqual((customer.gender, customer.playing_level), (None, None))

    def test_registration_rejects_legacy_choices_not_owned_by_new_customer(self):
        for fields in ({"gender": "Old gender"}, {"playing_level": "INTERMEDIATE"}, {"playing_level": "ADVANCED"}):
            with self.subTest(fields=fields), self.assertRaises(ValidationError):
                self.register(**fields)
        self.assertFalse(Account.objects.exists())

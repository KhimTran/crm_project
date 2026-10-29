from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.models import Account, Admin, Role, Staff
from apps.accounts.provisioning import ensure_admin_profile, ensure_staff_profile
from apps.accounts.selectors import account_data, get_account, list_account_page
from apps.accounts.services import create_account, update_account_profile


class ProfileModelAndServiceTests(TestCase):
    password = "StrongPass!2026"

    def setUp(self):
        # Create roles
        Role.objects.get_or_create(role_code="ADMIN", defaults={"role_name": "Quản trị viên"})
        Role.objects.get_or_create(role_code="MANAGER", defaults={"role_name": "Quản lý"})
        Role.objects.get_or_create(role_code="CUSTOMER", defaults={"role_name": "Khách hàng"})

        self.admin = Account.objects.create_superuser("admin-test@example.com", self.password)
        self.manager = Account.objects.create_user("manager-test@example.com", self.password, role=AccountRole.MANAGER)
        self.customer = Account.objects.create_user("customer-test@example.com", self.password, role=AccountRole.CUSTOMER)

    def test_role_model_and_constraints(self):
        roles = set(Role.objects.values_list("role_code", flat=True))
        self.assertTrue({"ADMIN", "MANAGER", "CUSTOMER"}.issubset(roles))

    def test_admin_profile_provisioning_and_properties(self):
        admin_prof, created = ensure_admin_profile(
            self.admin.pk, admin_code="AD0001", full_name="Admin Boss", phone="0912345678"
        )
        self.assertTrue(created)
        self.assertEqual(admin_prof.admin_code, admin_prof.code)
        self.assertEqual(admin_prof.full_name, "Admin Boss")
        self.assertEqual(admin_prof.phone, "0912345678")

        self.admin.refresh_from_db()
        self.assertIsNotNone(self.admin.admin)
        self.assertEqual(self.admin.profile.full_name, "Admin Boss")
        self.assertEqual(self.admin.display_name, "Admin Boss")

    def test_staff_profile_provisioning_and_no_department(self):
        staff_prof, created = ensure_staff_profile(
            self.manager.pk, staff_code="ST0001", full_name="Staff One",
        )
        self.assertTrue(created)
        self.assertEqual(staff_prof.staff_code, staff_prof.code)
        self.assertEqual(staff_prof.full_name, "Staff One")
        self.assertFalse(hasattr(staff_prof, "position"))
        self.assertFalse(hasattr(staff_prof, "hire_date"))

        # Strictly NO department attribute
        self.assertFalse(hasattr(staff_prof, "department"))

        self.manager.refresh_from_db()
        self.assertIsNotNone(self.manager.staff)
        self.assertEqual(self.manager.profile.full_name, "Staff One")
        self.assertEqual(self.manager.display_name, "Staff One")

    def test_create_account_with_profile_data(self):
        # Admin creates another Manager with profile
        created_data = create_account(
            self.admin,
            email="new-manager@example.com",
            role="MANAGER",
            status="ACTIVE",
            password=self.password,
            profile_data={"full_name": "New Manager", "phone": "0987654321"},
        )
        new_account = Account.objects.get(email="new-manager@example.com")
        self.assertIsNotNone(new_account.staff)
        self.assertEqual(new_account.staff.full_name, "New Manager")
        self.assertFalse(hasattr(new_account.staff, "position"))
        self.assertTrue(new_account.staff.staff_code.startswith("ST"))

    def test_selectors_and_search_by_profile(self):
        ensure_admin_profile(self.admin.pk, admin_code="AD0001", full_name="Super Admin")
        ensure_staff_profile(self.manager.pk, staff_code="ST0001", full_name="Store Manager")

        # Get account data
        data = get_account(self.admin, self.admin.pk)
        self.assertEqual(data["full_name"], "Super Admin")
        self.assertEqual(data["code"], self.admin.code)

        # Search by profile name
        page = list_account_page(self.admin, q="Super Admin")
        self.assertEqual(len(page.object_list), 1)
        self.assertEqual(page.object_list[0]["email"], self.admin.email)

        # Search by profile code
        page2 = list_account_page(self.admin, q=self.manager.code)
        self.assertEqual(len(page2.object_list), 1)
        self.assertEqual(page2.object_list[0]["email"], self.manager.email)

    def test_profile_update_service_and_view(self):
        ensure_staff_profile(self.manager.pk, staff_code="ST0001", full_name="Old Name")
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("accounts_admin:profile_update", args=[self.manager.pk]),
            {
                "email": self.manager.email,
                "full_name": "Updated Staff Name",
                "phone": "0911223344",
                "gender": "MALE",
            },
            follow=True,
        )
        self.assertRedirects(response, reverse("accounts_admin:detail", args=[self.manager.pk]))
        self.assertContains(response, "Profile updated successfully")

        self.manager.refresh_from_db()
        self.assertEqual(self.manager.staff.full_name, "Updated Staff Name")
        self.assertEqual(self.manager.staff.phone, "0911223344")

    def test_account_detail_view_renders_profile_info(self):
        ensure_admin_profile(self.admin.pk, admin_code="AD0001", full_name="Admin Name")
        self.client.force_login(self.admin)

        response = self.client.get(reverse("accounts_admin:detail", args=[self.admin.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.admin.admin_code)
        self.assertContains(response, "Admin Name")
        self.assertContains(response, "Profile Information")

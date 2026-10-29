from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Account
from apps.customers import reports
from apps.customers.favorite_brand import get_favorite_brand, set_favorite_brand
from apps.customers.models import Customer, CustomerPreference
from apps.customers.services import create_customer, delete_customer

PASSWORD = "StrongPass!2026"
REGISTER = {"email": "new@brand.test", "password": PASSWORD, "password_confirm": PASSWORD, "full_name": "New Player"}


# tv4: lấy {nhãn: số khách} từ báo cáo thương hiệu yêu thích
def brand_counts():
    return {r["label"]: r["count"] for r in reports.favorite_brand_report()["rows"]}


# tv4: test đăng ký / cập nhật hồ sơ lưu thương hiệu yêu thích và báo cáo Pie Chart
class FavoriteBrandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from apps.catalog.models import Brand
        for name in ("Yonex", "Li-Ning", "Victor", "Mizuno"):
            Brand.objects.create(brand_name=name)

    def post_register(self, **extra):
        return self.client.post(reverse("customer_auth:register"), {**REGISTER, **extra})

    def test_register_without_brand_still_works(self):
        self.assertEqual(self.post_register().status_code, 302)
        customer = Customer.objects.get(account__email="new@brand.test")
        self.assertEqual(get_favorite_brand(customer), (None, ""))

    def test_register_with_brand_and_other_name(self):
        self.post_register(favorite_brand="Yonex")
        self.assertEqual(get_favorite_brand(Customer.objects.get(account__email="new@brand.test")), ("Yonex", ""))
        self.post_register(email="o@brand.test", favorite_brand="Other", favorite_brand_other="  Apacs  ")
        self.assertEqual(get_favorite_brand(Customer.objects.get(account__email="o@brand.test")), ("Other", "Apacs"))

    def test_other_requires_name_and_invalid_brand_rejected(self):
        self.assertEqual(self.post_register(favorite_brand="Other").status_code, 200)
        self.assertEqual(self.post_register(favorite_brand="Nike").status_code, 200)
        self.assertFalse(Account.objects.filter(email="new@brand.test").exists())

    def test_profile_update_changes_value_without_duplicates(self):
        self.post_register(favorite_brand="Yonex")
        account = Account.objects.get(email="new@brand.test")
        customer = account.customer
        self.client.force_login(account)
        data = {"full_name": "New Player", "favorite_brand": "Victor"}
        self.assertEqual(self.client.post(reverse("customers:profile"), data).status_code, 302)
        self.client.post(reverse("customers:profile"), {**data, "favorite_brand": "Other", "favorite_brand_other": "Apacs"})
        self.client.post(reverse("customers:profile"), {**data, "favorite_brand": "Li-Ning"})
        self.assertEqual(get_favorite_brand(customer), ("Li-Ning", ""))
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(CustomerPreference.objects.filter(customer=customer, preference_type="FAVORITE_BRAND").count(), 1)
        self.assertFalse(CustomerPreference.objects.filter(customer=customer, preference_type="FAVORITE_BRAND_OTHER").exists())
        page = self.client.get(reverse("customers:profile"))
        self.assertContains(page, 'value="Li-Ning" selected')
        self.assertContains(page, "Save Changes")
        # Omitting the field keeps the saved value; an explicit empty choice clears it.
        self.client.post(reverse("customers:profile"), {"full_name": "New Player"})
        self.assertEqual(get_favorite_brand(customer)[0], "Li-Ning")
        self.client.post(reverse("customers:profile"), {**data, "favorite_brand": ""})
        self.assertEqual(get_favorite_brand(customer), (None, ""))

    def test_report_counts_each_customer_once_current_value_only(self):
        manager = Account.objects.create_user("manager@brand.test", "Quanly@12345", role="MANAGER")
        manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        a, b, c, gone = (create_customer(password=PASSWORD, email=f"{n}@brand.test", full_name=n, phone=f"09000000{i}")
                         for i, n in enumerate(("a", "b", "c", "d"), start=10))
        set_favorite_brand(a, "Yonex")
        set_favorite_brand(a, "Victor")
        set_favorite_brand(b, "Other", "Apacs")
        set_favorite_brand(gone, "Yonex")
        delete_customer(gone.pk)
        CustomerPreference.objects.create(customer=c, preference_type="FAVORITE_BRAND", preference_value="")
        report = reports.favorite_brand_report()
        self.assertEqual(brand_counts(), {"Yonex": 0, "Li-Ning": 0, "Victor": 1, "Mizuno": 0, "Other": 1})
        self.assertEqual((report["answered"], report["unanswered"], report["total_customers"]), (2, 1, 3))
        self.assertEqual({r["label"]: r["pct"] for r in report["rows"]},
                         {"Yonex": 0.0, "Li-Ning": 0.0, "Victor": 50.0, "Mizuno": 0.0, "Other": 50.0})
        self.client.force_login(manager)
        page = self.client.get(reverse("customer_reports:customers"))
        self.assertContains(page, "Favorite Badminton Brand")
        self.assertContains(page, 'id="chart-brand"')

    def test_report_empty_state(self):
        manager = Account.objects.create_user("manager2@brand.test", "Quanly@12345", role="MANAGER")
        manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        self.client.force_login(manager)
        page = self.client.get(reverse("customer_reports:customers"))
        self.assertContains(page, "No customer has chosen a favorite brand yet.")
        self.assertNotContains(page, 'id="chart-brand"')

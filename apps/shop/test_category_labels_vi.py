"""Customer-facing Vietnamese category labels; stored names and Manager/Admin UI stay English."""
from decimal import Decimal

from django.test import SimpleTestCase

from apps.accounts.models import Account
from apps.accounts.testing import PortalTestCase as TestCase
from apps.catalog.models import Brand, Category, Product
from apps.catalog.vocabulary import category_label_vi
from apps.customers.models import Customer, CustomerPreference

LABELS = {
    "Accessories": "Phụ kiện cầu lông",
    "Badminton apparel": "Quần áo cầu lông",
    "Badminton bags": "Túi & balo cầu lông",
    "Badminton rackets": "Vợt cầu lông",
    "Badminton shoes": "Giày cầu lông",
    "Shuttlecocks": "Quả cầu lông",
}


class CategoryLabelHelperTests(SimpleTestCase):
    def test_six_known_names_map_to_vietnamese(self):
        for english, vietnamese in LABELS.items():
            with self.subTest(english=english):
                self.assertEqual(category_label_vi(english), vietnamese)

    def test_case_and_extra_spaces_are_ignored(self):
        self.assertEqual(category_label_vi("  badminton   RACKETS "), "Vợt cầu lông")

    def test_unknown_or_empty_names_are_returned_unchanged(self):
        self.assertEqual(category_label_vi("Strings"), "Strings")
        self.assertEqual(category_label_vi(""), "")
        self.assertIsNone(category_label_vi(None))


class CategoryLabelPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(category_name="Badminton rackets")
        cls.unknown = Category.objects.create(category_name="Strings")
        cls.brand = Brand.objects.create(brand_name="Yonex")
        cls.product = Product.objects.create(
            category=cls.category, brand=cls.brand, product_name="Racket X", price=Decimal("1000000"))
        cls.owner = Account.objects.create_user("vi-owner@labels.test", "StrongPass!2026", full_name="Owner")
        cls.manager = Account.objects.create_user("vi-manager@labels.test", "StrongPass!2026", role="MANAGER")
        cls.customer = Customer.objects.get(pk=cls.owner.pk)
        cls.brand_preference = CustomerPreference.objects.create(
            customer=cls.customer, preference_type="BRAND", preference_value="Yonex")
        cls.favorite_preference = CustomerPreference.objects.create(
            customer=cls.customer, preference_type="FAVORITE_BRAND", preference_value="Yonex")

    def test_home_menu_and_filter_show_vietnamese_but_keep_ids(self):
        for url in ("/", "/products/"):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, "Vợt cầu lông")
                self.assertContains(response, f"?category={self.category.pk}")
                self.assertContains(response, "Strings")
                self.assertNotContains(response, "Badminton rackets")
        select = self.client.get("/products/").content.decode()
        self.assertIn(f'<option value="{self.category.pk}">Vợt cầu lông</option>', select)

    def test_category_filter_still_filters_by_id(self):
        response = self.client.get(f"/products/?category={self.unknown.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Racket X")
        response = self.client.get(f"/products/?category={self.category.pk}")
        self.assertContains(response, "Racket X")

    def test_product_detail_shows_vietnamese_category(self):
        response = self.client.get(f"/products/{self.product.pk}/")
        self.assertContains(response, "Vợt cầu lông")
        self.assertNotContains(response, "Badminton rackets")

    def test_profile_checkboxes_use_vietnamese_but_save_english_value(self):
        self.client.force_login(self.owner)
        response = self.client.get("/account/profile/")
        self.assertContains(response, "Vợt cầu lông")
        self.assertNotContains(response, "Badminton rackets")
        self.client.post("/account/profile/", {
            "full_name": "Owner", "categories": [self.category.pk],
        })
        self.assertTrue(CustomerPreference.objects.filter(
            customer=self.customer, preference_type="CATEGORY", preference_value="Badminton rackets").exists())

    def test_manager_catalog_keeps_english_names(self):
        self.client.force_login(self.manager)
        response = self.client.get("/manager/catalog/categories/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Badminton rackets")
        self.assertNotContains(response, "Vợt cầu lông")


class ProfileCleanupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(category_name="Badminton rackets")
        cls.owner = Account.objects.create_user("cleanup@profile.test", "StrongPass!2026", full_name="Owner")
        cls.customer = Customer.objects.get(pk=cls.owner.pk)
        cls.brand = CustomerPreference.objects.create(
            customer=cls.customer, preference_type="BRAND", preference_value="Yonex")

    def test_profile_no_longer_shows_other_saved_choices_block(self):
        self.client.force_login(self.owner)
        response = self.client.get("/account/profile/")
        self.assertEqual(response.status_code, 200)
        for text in ("Lựa chọn khác đã lưu", "được giữ nguyên khi bạn lưu hồ sơ"):
            self.assertNotContains(response, text)
        self.assertNotIn("other_preferences", response.context)

    def test_saving_profile_succeeds_and_keeps_preferences_outside_the_form(self):
        self.client.force_login(self.owner)
        response = self.client.post("/account/profile/", {
            "full_name": "Owner", "categories": [self.category.pk],
        })
        self.assertRedirects(response, "/account/profile/", fetch_redirect_response=False)
        self.assertTrue(CustomerPreference.objects.filter(pk=self.brand.pk, preference_value="Yonex").exists())


class CustomerPagesVietnameseTests(TestCase):
    """Customer-facing profile/register pages must not show the old English UI strings."""
    ENGLISH = ("Favorite Badminton Brand", "Select your favorite brand", "Optional. Choose",
               "Other brand name", "Enter the brand name", "Save Changes", "Customer Registration")

    @classmethod
    def setUpTestData(cls):
        cls.owner = Account.objects.create_user("vi-pages@labels.test", "StrongPass!2026", full_name="Owner")

    def test_register_page_is_vietnamese(self):
        response = self.client.get("/register/")
        self.assertContains(response, "Đăng ký tài khoản khách hàng")
        self.assertContains(response, "Thương hiệu cầu lông yêu thích")
        self.assertContains(response, '<option value="Other">Khác</option>')
        for text in self.ENGLISH:
            self.assertNotContains(response, text)

    def test_profile_page_is_vietnamese_and_other_keeps_value(self):
        self.client.force_login(self.owner)
        response = self.client.get("/account/profile/")
        for text in ("Chọn thương hiệu yêu thích", "Tên thương hiệu khác", "Lưu thay đổi", "Hủy"):
            self.assertContains(response, text)
        self.assertContains(response, '<option value="Other">Khác</option>')
        for text in self.ENGLISH + ("Cancel",):
            self.assertNotContains(response, text)

    def test_saving_with_other_brand_still_works(self):
        self.client.force_login(self.owner)
        response = self.client.post("/account/profile/", {
            "full_name": "Owner", "favorite_brand": "Other", "favorite_brand_other": "Kumpoo",
        })
        self.assertRedirects(response, "/account/profile/", fetch_redirect_response=False)
        self.assertTrue(CustomerPreference.objects.filter(
            customer_id=self.owner.pk, preference_type="FAVORITE_BRAND_OTHER", preference_value="Kumpoo").exists())

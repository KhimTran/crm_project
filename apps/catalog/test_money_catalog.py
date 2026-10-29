from decimal import Decimal
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.accounts.models import Account
from apps.catalog.forms import BrandForm, ProductForm
from apps.catalog.models import Brand, Category, Product
from apps.catalog.money import MoneyField, format_money
from apps.catalog.normalization import normalize_catalog
from apps.catalog.selectors import list_product_page
from apps.catalog.vocabulary import brand_choices
from apps.customers.favorite_brand import get_favorite_brand
from apps.customers.models import CustomerPreference
from apps.customers.reports import favorite_brand_report, preference_report
from apps.customers.self_service_forms import CustomerProfileForm
from apps.customers.self_services import update_own_profile
from apps.customers.selectors import filter_customers, customer_queryset
from apps.shop.forms import ProductFilterForm
from apps.shop.selectors import filtered_products
from apps.surveys.forms import AudienceForm
from apps.surveys.services import preference_choices, filter_customers as survey_customers


class MoneyTests(SimpleTestCase):
    def test_decimal_parsing_and_grouping(self):
        field = MoneyField(max_digits=12, decimal_places=2, min_value=0)
        for text in ("1000", "1,000", "10000000", "100000000", "1,234.50", "9999999999.99", "0"):
            with self.subTest(text=text):
                value = field.clean(text)
                self.assertEqual(value, Decimal(text.replace(",", "")))
                self.assertEqual(field.clean(format_money(value)), value)
        self.assertEqual(format_money(Decimal("1234.50")), "1,234.50")
        self.assertEqual(format_money(Decimal("1234.00")), "1,234")

    def test_rejects_bad_groups_junk_precision_and_bounds(self):
        field = MoneyField(max_digits=12, decimal_places=2, min_value=0)
        for value in ("", "1,00", "1,23,456", "1,,000", "1.234,50", "1e3", "NaN", "Infinity",
                      "1 000", "abc1000", "-1", "10000000000", "1.001", "1,234."):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                field.clean(value)
        self.assertIsNone(MoneyField(required=False).clean(""))

    def test_widget_preserves_invalid_input_and_does_not_round(self):
        widget = MoneyField().widget
        self.assertEqual(widget.format_value("1,00"), "1,00")
        self.assertEqual(widget.format_value("1234.567"), "1,234.567")
        html = widget.render("price", Decimal("1234.50"))
        self.assertIn('type="text"', html)
        self.assertIn('value="1,234.50"', html)
        self.assertIn('data-money', html)


class CatalogNormalizationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(category_name="Badminton rackets")
        cls.brand = Brand.objects.create(brand_id=4, brand_name="Lining")
        cls.product = Product.objects.create(brand=cls.brand, category=cls.category,
                                             product_name="Lining Axforce 80 4U", price=Decimal("1234.50"))
        cls.customer = Account.objects.create_user("catalog-preference@test.example", "StrongPass!2026")
        cls.manager = Account.objects.create_user("money-manager@test.example", "StrongPass!2026", role="MANAGER")

    def legacy_preferences(self):
        # bulk_create deliberately models pre-existing storage, bypassing new-write normalization.
        CustomerPreference.objects.bulk_create([
            CustomerPreference(customer=self.customer, preference_type="BRAND", preference_value=value)
            for value in ("Lining", "Li-Ning", "Kumpoo", "VNB")
        ])

    def test_preview_apply_preserves_ids_fks_prices_and_unknowns(self):
        self.legacy_preferences()
        Brand.objects.filter(pk=4).update(status="INACTIVE")
        Product.objects.filter(pk=self.product.pk).update(status="INACTIVE")
        before = self.product.price
        self.assertEqual(normalize_catalog(), {"brands": 1, "products": 1, "preferences": 1, "merged": 1})
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.brand_name, "Lining")
        output = StringIO()
        call_command("normalize_catalog", apply=True, stdout=output)
        self.product.refresh_from_db()
        self.brand.refresh_from_db()
        self.assertEqual((self.brand.pk, self.product.brand_id), (4, 4))
        self.assertEqual(self.product.price, before)
        self.assertEqual(self.product.product_name, "Li-Ning Axforce 80 4U")
        self.assertEqual(self.brand.brand_name, "Li-Ning")
        self.assertEqual((self.brand.status, self.product.status), ("INACTIVE", "INACTIVE"))
        self.assertEqual(set(CustomerPreference.objects.values_list("preference_value", flat=True)),
                         {"Li-Ning", "Kumpoo", "VNB"})
        self.assertEqual(normalize_catalog(apply=True), {"brands": 0, "products": 0, "preferences": 0, "merged": 0})

    def test_search_filters_and_reports_accept_both_aliases_before_and_after(self):
        self.legacy_preferences()
        for repaired in (False, True):
            if repaired:
                normalize_catalog(apply=True)
            for term in ("Lining", "Li-Ning", "Li-Ning Axforce"):
                self.assertEqual(list(filtered_products({"q": term})), [self.product])
                self.assertEqual(list(list_product_page(q=term)), [self.product])
            for term in ("Lining", "Li-Ning"):
                self.assertEqual(list(filter_customers(customer_queryset(), {"brand": term})), [self.customer.customer])
                self.assertEqual(list(survey_customers(audience="filtered", preferences=(term,))), [self.customer.customer])
                form = AudienceForm({"audience": "filter", "preferences": [term]})
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["preferences"], ["Li-Ning"])
            rows = next(group["rows"] for group in preference_report() if group["type"] == "BRAND")
            self.assertEqual({row["label"]: row["count"] for row in rows}, {"Li-Ning": 1, "Kumpoo": 1, "VNB": 1})
            self.assertIn(("Li-Ning", "Li-Ning"), preference_choices())
            self.assertNotIn(("Lining", "Lining"), preference_choices())

    def test_active_choices_saved_inactive_and_unmatched_values_survive(self):
        Brand.objects.create(brand_name="Disabled", status="INACTIVE")
        self.assertNotIn("Disabled", dict(brand_choices()))
        self.assertNotIn("Kumpoo", dict(brand_choices()))
        preference = CustomerPreference.objects.create(customer=self.customer, preference_type="FAVORITE_BRAND", preference_value="Kumpoo")
        category = Category.objects.create(category_name="Badminton bags", status="INACTIVE")
        CustomerPreference.objects.create(customer=self.customer, preference_type="CATEGORY", preference_value=category.category_name)
        CustomerPreference.objects.create(customer=self.customer, preference_type="BRAND", preference_value="VNB")
        form = CustomerProfileForm(instance=self.customer.customer)
        self.assertIn("Kumpoo", dict(form.fields["favorite_brand"].choices))
        update_own_profile(self.customer, profile_data={"full_name": "Updated", "favorite_brand": "Kumpoo"})
        self.assertEqual(get_favorite_brand(self.customer.customer), ("Kumpoo", ""))
        self.assertTrue(CustomerPreference.objects.filter(preference_value="Badminton bags").exists())
        self.assertTrue(CustomerPreference.objects.filter(preference_value="VNB").exists())
        self.assertFalse(CustomerProfileForm({"full_name": "New", "favorite_brand": "Kumpoo"}).is_valid())
        report = favorite_brand_report()
        self.assertEqual(report["answered"], 1)

    def test_new_brand_alias_and_preference_input_canonicalized(self):
        form = BrandForm({"brand_name": "Li-Ning", "status": "ACTIVE"}, instance=self.brand)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        pref = CustomerPreference.objects.create(customer=self.customer, preference_type="BRAND", preference_value="Lining")
        self.assertEqual(pref.preference_value, "Li-Ning")
        form = CustomerProfileForm({"full_name": "Player", "favorite_brand": "Lining"}, instance=self.customer.customer)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["favorite_brand"], "Li-Ning")

    def test_product_price_roundtrip_error_redisplay_numeric_filter_sort(self):
        self.client.force_login(self.manager)
        url = reverse("catalog_admin:product_edit", args=[self.product.pk])
        data = {"brand": 4, "category": self.category.pk, "product_name": "Li-Ning Axforce 80 4U",
                "status": "ACTIVE", "price": "10,000,000.50"}
        self.assertEqual(self.client.post(url, data).status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal("10000000.50"))
        self.assertContains(self.client.get(url), 'value="10,000,000.50"')
        response = self.client.post(url, {**data, "product_name": ""})
        self.assertContains(response, 'value="10,000,000.50"')
        for invalid in ("0", "-1", "", "1,00", "10000000000", "1.001"):
            form = ProductForm({**data, "price": invalid}, instance=self.product)
            self.assertFalse(form.is_valid(), (invalid, form.errors))
        form = ProductFilterForm({"min_price": "10,000,000", "max_price": "10,000,000.50"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(list(filtered_products(form.cleaned_data)), [self.product])
        lower = Product.objects.create(brand=self.brand, category=self.category, product_name="Low", price="999.99")
        self.assertEqual([p.pk for p in list_product_page(sort="price", direction="asc")], [lower.pk, self.product.pk])
        self.assertEqual(ProductFilterForm({"min_price": "0"}).is_valid(), True)

    def test_repair_refuses_ambiguous_brand_ids_atomically(self):
        Brand.objects.create(brand_name="Li-Ning")
        with self.assertRaisesMessage(Exception, "Multiple Li-Ning/Lining"):
            normalize_catalog(apply=True)
        self.brand.refresh_from_db()
        self.assertEqual(self.brand.brand_name, "Lining")

    def test_seed_reuses_legacy_brand_and_product_ids(self):
        self.product.product_name = "Lining Axforce 80"
        self.product.save(update_fields=["product_name"])
        for _ in range(2):
            call_command("seed_catalog", stdout=StringIO())
        self.product.refresh_from_db()
        self.assertEqual(self.product.brand_id, 4)
        self.assertEqual(Brand.objects.filter(brand_name="Li-Ning").count(), 1)
        self.assertEqual(Product.objects.filter(product_name="Li-Ning Axforce 80").count(), 1)

    def test_favorite_merge_preserves_latest_choice_with_interleaved_history(self):
        CustomerPreference.objects.bulk_create([
            CustomerPreference(customer=self.customer, preference_type="FAVORITE_BRAND", preference_value=value)
            for value in ("Lining", "Yonex", "Li-Ning")
        ])
        self.assertEqual(get_favorite_brand(self.customer)[0], "Li-Ning")
        counts = normalize_catalog(apply=True)
        self.assertEqual(counts["merged"], 1)
        self.assertEqual(get_favorite_brand(self.customer)[0], "Li-Ning")

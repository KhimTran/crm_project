from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.core.management import call_command
from django import forms
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import localize

from .models import Brand, Category, Product, Supplier


class CatalogTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("catalog-admin@example.com", "StrongPass!2026")
        self.client.force_login(self.admin)
        self.category = Category.objects.create(category_name="Rackets")
        self.brand = Brand.objects.create(brand_name="Brand")
        self.supplier = Supplier.objects.create(supplier_code="S001", supplier_name="Supplier")

    def test_supplier_create_and_product_requires_supplier(self):
        response = self.client.post(reverse("catalog_admin:supplier_create"), {"supplier_code": "S002", "supplier_name": "Second", "status": "ACTIVE"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Supplier.objects.filter(supplier_code="S002").exists())
        response = self.client.post(reverse("catalog_admin:product_create"), {"category": self.category.pk, "brand": self.brand.pk, "product_name": "Racket", "price": "100.00", "status": "ACTIVE"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.exists())
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.create(category=self.category, brand=self.brand, product_name="Invalid", price=Decimal("1.00"))

    def test_seed_is_repeatable_and_every_product_has_supplier(self):
        with patch.dict("os.environ", {"CRM_DEMO_PASSWORD": "DemoPass!2026"}):
            call_command("seed_data", verbosity=0)
            call_command("seed_data", verbosity=0)
        self.assertGreaterEqual(Supplier.objects.count(), 8)
        self.assertEqual(Product.objects.filter(supplier__isnull=True).count(), 0)
        self.assertEqual(Product.objects.count(), 8)

    def test_supplier_protected_and_product_crud(self):
        edit = self.client.post(reverse("catalog_admin:supplier_edit", args=[self.supplier.pk]), {"supplier_code": "S001", "supplier_name": "Updated supplier", "status": "ACTIVE"})
        self.assertEqual(edit.status_code, 302)
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.supplier_name, "Updated supplier")
        response = self.client.post(reverse("catalog_admin:product_create"), {"category": self.category.pk, "brand": self.brand.pk, "supplier": self.supplier.pk, "product_name": "Racket", "price": "100.00", "status": "ACTIVE"})
        self.assertEqual(response.status_code, 302)
        product = Product.objects.get()
        with self.assertRaises(ProtectedError):
            self.supplier.delete()
        response = self.client.post(reverse("catalog_admin:supplier_delete", args=[self.supplier.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Supplier.objects.filter(pk=self.supplier.pk).exists())
        response = self.client.get(reverse("catalog_admin:product_list"), {"supplier": self.supplier.pk})
        self.assertContains(response, "Racket")
        response = self.client.post(reverse("catalog_admin:product_edit", args=[product.pk]), {"category": self.category.pk, "brand": self.brand.pk, "supplier": self.supplier.pk, "product_name": "Racket 2", "price": "120.00", "status": "ACTIVE"})
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.product_name, "Racket 2")
        self.assertEqual(self.client.post(reverse("catalog_admin:product_delete", args=[product.pk])).status_code, 302)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())
        self.assertEqual(self.client.post(reverse("catalog_admin:supplier_delete", args=[self.supplier.pk])).status_code, 302)
        self.assertFalse(Supplier.objects.filter(pk=self.supplier.pk).exists())


class SupplierListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("supplier-admin@example.com", "StrongPass!2026")
        Supplier.objects.create(supplier_code="SUP001", supplier_name="Yonex Vietnam", status="ACTIVE", email="sales@yonex.example", phone="123456")
        Supplier.objects.create(supplier_code="SUP002", supplier_name="Yonex Europe", status="INACTIVE")
        Supplier.objects.create(supplier_code="SUP003", supplier_name="Victor Vietnam", status="ACTIVE")

    def setUp(self):
        self.client.force_login(self.admin)
        self.url = reverse("catalog_admin:supplier_list")

    def test_list_renders_controls_and_actions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Search suppliers")
        self.assertContains(response, "All statuses")
        self.assertContains(response, "Create Supplier")
        self.assertContains(response, "Edit")
        self.assertContains(response, "Delete")
        self.assertContains(response, "d-flex gap-2 flex-wrap")

    def test_search_code_name_case_and_empty_query(self):
        for query, expected in (("SUP001", "SUP001"), (" yonex viet ", "SUP001"), ("yOnEx", "SUP001")):
            with self.subTest(query=query):
                response = self.client.get(self.url, {"q": query})
                self.assertContains(response, expected)
                self.assertNotContains(response, "SUP003")
        response = self.client.get(self.url, {"q": "   "})
        self.assertEqual(response.context["page_obj"].paginator.count, 3)

    def test_search_email_and_phone(self):
        for query in ("sales@yonex", "12345"):
            with self.subTest(query=query):
                response = self.client.get(self.url, {"q": query})
                self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_status_filters_and_combination(self):
        for status, count in (("ACTIVE", 2), ("INACTIVE", 1)):
            with self.subTest(status=status):
                response = self.client.get(self.url, {"status": status.lower()})
                self.assertEqual(response.context["page_obj"].paginator.count, count)
                self.assertEqual(response.context["status_filter"], status)
        response = self.client.get(self.url, {"q": "yonex", "status": "inactive"})
        self.assertEqual([supplier.supplier_code for supplier in response.context["items"]], ["SUP002"])
        self.assertEqual(self.client.get(self.url, {"status": "UNKNOWN"}).status_code, 200)

    def test_no_result_state_and_clear(self):
        response = self.client.get(self.url, {"q": "missing"})
        self.assertContains(response, "No suppliers found.")
        self.assertNotContains(response, "<table")
        self.assertContains(response, "Create Supplier")
        self.assertContains(response, f'href="{self.url}">Clear</a>')

    def test_pagination_preserves_each_filter_and_combination(self):
        Supplier.objects.bulk_create([
            Supplier(supplier_code=f"PAGE{number:03}", supplier_name=f"Yonex page {number:03}", status="ACTIVE")
            for number in range(21)
        ])
        for params, expected in (
            ({"q": "yonex"}, "?page=2&amp;q=yonex"),
            ({"status": "active"}, "?page=2&amp;status=ACTIVE"),
            ({"q": " yonex ", "status": "active"}, "?page=2&amp;q=yonex&amp;status=ACTIVE"),
        ):
            with self.subTest(params=params):
                response = self.client.get(self.url, params)
                self.assertContains(response, expected)
                second = self.client.get(self.url, {**params, "page": "2"})
                self.assertEqual(second.context["page_obj"].number, 2)
                self.assertContains(second, "Previous")

    def test_sql_columns_nullable_values_and_form_fields(self):
        supplier = Supplier.objects.get(supplier_code="SUP001")
        supplier.address = "Hanoi, Vietnam"
        supplier.save(update_fields=["address"])
        response = self.client.get(self.url, {"q": "SUP001"})
        for heading in ("Supplier ID", "Supplier Code", "Supplier Name", "Address", "Phone", "Email", "Status", "Created At", "Updated At", "Actions"):
            self.assertContains(response, heading)
        for value in (f"<td>{supplier.pk}</td>", "SUP001", "Yonex Vietnam", "Hanoi, Vietnam", "123456", "sales@yonex.example", "ACTIVE"):
            self.assertContains(response, value)
        for value in (supplier.created_at, supplier.updated_at):
            self.assertContains(response, timezone.localtime(value).strftime("%Y-%m-%d %H:%M"))
        self.assertContains(response, "Edit")
        self.assertContains(response, "Delete")
        nullable = self.client.get(self.url, {"q": "SUP002"})
        self.assertContains(nullable, "<td>—</td>", count=3)
        self.assertNotContains(nullable, "<td>None</td>")
        for path in (reverse("catalog_admin:supplier_create"), reverse("catalog_admin:supplier_edit", args=[supplier.pk])):
            with self.subTest(path=path):
                form = self.client.get(path).context["form"]
                self.assertEqual(set(form.fields), {"supplier_code", "supplier_name", "address", "phone", "email", "status"})
                self.assertIsInstance(form.fields["status"].widget, forms.Select)


class ProductListUiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("product-admin@example.com", "StrongPass!2026")
        cls.category = Category.objects.create(category_name="Rackets")
        cls.brand = Brand.objects.create(brand_name="Yonex")
        cls.supplier = Supplier.objects.create(supplier_code="SUP100", supplier_name="Yonex Vietnam")
        cls.other_supplier = Supplier.objects.create(supplier_code="SUP101", supplier_name="Other Supplier")
        cls.product = Product.objects.create(
            category=cls.category, brand=cls.brand, supplier=cls.supplier,
            product_name="Astrox 100", description="Full racket description with specifications.",
            price=Decimal("125000.50"), status="ACTIVE",
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_product_list_shows_all_sql_fields_and_readable_relationships(self):
        response = self.client.get(reverse("catalog_admin:product_list"))
        for heading in ("Product ID", "Product Name", "Category", "Brand", "Supplier", "Description", "Price", "Status", "Created At", "Updated At", "Actions"):
            self.assertContains(response, heading)
        for value in (f"<td>{self.product.pk}</td>", "Astrox 100", "Rackets", "Yonex", "Yonex Vietnam", "Full racket description with specifications.", localize(self.product.price), "ACTIVE"):
            self.assertContains(response, value)
        for value in (self.product.created_at, self.product.updated_at):
            self.assertContains(response, timezone.localtime(value).strftime("%Y-%m-%d %H:%M"))
        self.assertContains(response, "table-responsive")
        self.assertContains(response, "portal-description")
        self.assertContains(response, "d-flex gap-2 flex-wrap")
        self.assertContains(response, "Edit")
        self.assertContains(response, "Delete")

    def test_product_forms_have_only_editable_fields_and_readable_selects(self):
        for path in (reverse("catalog_admin:product_create"), reverse("catalog_admin:product_edit", args=[self.product.pk])):
            with self.subTest(path=path):
                response = self.client.get(path)
                form = response.context["form"]
                self.assertEqual(set(form.fields), {"category", "brand", "supplier", "product_name", "description", "price", "status"})
                for field in ("category", "brand", "supplier", "status"):
                    self.assertIsInstance(form.fields[field].widget, forms.Select)
                for name in ("Rackets", "Yonex", "Yonex Vietnam"):
                    self.assertContains(response, name)

    def test_product_search_and_supplier_filter_still_combine(self):
        url = reverse("catalog_admin:product_list")
        self.assertContains(self.client.get(url, {"q": "astrox"}), "Astrox 100")
        self.assertContains(self.client.get(url, {"supplier": self.supplier.pk}), "Astrox 100")
        self.assertContains(self.client.get(url, {"q": "Yonex Vietnam", "supplier": self.supplier.pk}), "Astrox 100")
        self.assertNotContains(self.client.get(url, {"q": "Astrox", "supplier": self.other_supplier.pk}), "Astrox 100")

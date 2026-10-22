from decimal import Decimal
from unittest.mock import patch

from django import forms
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import localize

from .models import Brand, Category, Product


class CatalogTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user("catalog-manager@example.com", "StrongPass!2026", role="MANAGER")
        self.client.force_login(self.admin)
        self.category = Category.objects.create(category_name="Rackets")
        self.brand = Brand.objects.create(brand_name="Brand")

    def test_product_create_and_validation(self):
        response = self.client.post(reverse("catalog_admin:product_create"), {
            "category": self.category.pk,
            "brand": self.brand.pk,
            "product_name": "Racket",
            "price": "100.00",
            "status": "ACTIVE",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Product.objects.filter(product_name="Racket").exists())

    def test_seed_is_repeatable(self):
        with patch.dict("os.environ", {"CRM_DEMO_PASSWORD": "DemoPass!2026"}):
            call_command("seed_data", verbosity=0)
            call_command("seed_data", verbosity=0)
        self.assertEqual(Product.objects.count(), 8)

    def test_category_protected_and_product_crud(self):
        response = self.client.post(reverse("catalog_admin:product_create"), {
            "category": self.category.pk,
            "brand": self.brand.pk,
            "product_name": "Racket",
            "price": "100.00",
            "status": "ACTIVE",
        })
        self.assertEqual(response.status_code, 302)
        product = Product.objects.get()
        with self.assertRaises(ProtectedError):
            self.category.delete()

        response = self.client.get(reverse("catalog_admin:product_list"), {"category": self.category.pk})
        self.assertContains(response, "Racket")

        response = self.client.post(reverse("catalog_admin:product_edit", args=[product.pk]), {
            "category": self.category.pk,
            "brand": self.brand.pk,
            "product_name": "Racket 2",
            "price": "120.00",
            "status": "ACTIVE",
        })
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.product_name, "Racket 2")

        self.assertEqual(self.client.post(reverse("catalog_admin:product_delete", args=[product.pk])).status_code, 302)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())


class ProductListUiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_user("product-manager@example.com", "StrongPass!2026", role="MANAGER")
        cls.category = Category.objects.create(category_name="Rackets")
        cls.brand = Brand.objects.create(brand_name="Yonex")
        cls.other_brand = Brand.objects.create(brand_name="Lining")
        cls.product = Product.objects.create(
            category=cls.category, brand=cls.brand,
            product_name="Astrox 100", description="Full racket description with specifications.",
            price=Decimal("125000.50"), status="ACTIVE",
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_product_list_shows_all_sql_fields_and_readable_relationships(self):
        response = self.client.get(reverse("catalog_admin:product_list"))
        for heading in ("Product ID", "Product Name", "Category", "Brand", "Description", "Price", "Status", "Created At", "Updated At", "Actions"):
            self.assertContains(response, heading)
        for value in (f"<td>{self.product.pk}</td>", "Astrox 100", "Rackets", "Yonex", "Full racket description with specifications.", localize(self.product.price), "ACTIVE"):
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
                self.assertEqual(set(form.fields), {"category", "brand", "product_name", "description", "image_url", "price", "status"})
                for field in ("category", "brand", "status"):
                    self.assertIsInstance(form.fields[field].widget, forms.Select)
                for name in ("Rackets", "Yonex"):
                    self.assertContains(response, name)

    def test_product_search_and_brand_filter(self):
        url = reverse("catalog_admin:product_list")
        self.assertContains(self.client.get(url, {"q": "astrox"}), "Astrox 100")
        self.assertContains(self.client.get(url, {"brand": self.brand.pk}), "Astrox 100")
        self.assertNotContains(self.client.get(url, {"brand": self.other_brand.pk}), "Astrox 100")

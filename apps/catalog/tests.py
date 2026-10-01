from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

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

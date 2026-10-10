from decimal import Decimal

from django.contrib.staticfiles import finders
from django.test import TestCase

from apps.catalog.models import Brand, Category, Product, Supplier


class ShopTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(category_name="Rackets")
        cls.other_category = Category.objects.create(category_name="Shoes")
        cls.brand = Brand.objects.create(brand_name="Brand A")
        cls.other_brand = Brand.objects.create(brand_name="Brand B")
        cls.supplier = Supplier.objects.create(supplier_code="TV1-TEST", supplier_name="Supplier")
        cls.products = [Product.objects.create(category=cls.category, brand=cls.brand, supplier=cls.supplier,
                        product_name=f"Racket {index:02d}", price=Decimal(index * 100)) for index in range(1, 15)]
        cls.other = Product.objects.create(category=cls.other_category, brand=cls.other_brand, supplier=cls.supplier,
                        product_name="Shoes", price=Decimal("1000"))
        cls.inactive = Product.objects.create(category=cls.category, brand=cls.brand, supplier=cls.supplier,
                        product_name="Inactive product", price=Decimal("10"), status="INACTIVE")

    def test_home_and_list_are_public_show_only_active_products_and_local_assets(self):
        for path in ("/", "/products/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "layouts/base_customer.html")
            self.assertNotContains(response, "Inactive product")
            self.assertNotContains(response, "https://cdn")
            self.assertContains(response, "/static/images/product-placeholder.svg")
        for asset in ("vendor/bootstrap.min.css", "css/tv1.css", "images/product-placeholder.svg"):
            self.assertTrue(finders.find(asset))

    def test_combined_filters_use_decimal_price_and_match_category_brand(self):
        response = self.client.get("/products/", {"category": self.category.pk, "brand": self.brand.pk, "min_price": "300.00", "max_price": "500.00"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p.price for p in response.context["page"].object_list], [Decimal("300"), Decimal("400"), Decimal("500")])
        response = self.client.get("/products/", {"q": "  shoes  ", "brand": self.other_brand.pk})
        self.assertEqual(list(response.context["page"].object_list), [self.other])

    def test_invalid_filters_are_field_errors_instead_of_unfiltered_results(self):
        for query in ({"category": "bad"}, {"brand": "999999"}, {"min_price": "-1"}, {"max_price": "nan"},
                      {"min_price": "100", "max_price": "10"}, {"min_price": "0.001"}, {"max_price": "10000000000"}):
            with self.subTest(query=query):
                response = self.client.get("/products/", query)
                self.assertEqual(response.status_code, 400)
                self.assertTrue(response.context["form"].errors)
                self.assertEqual(response.context["page"].paginator.count, 0)

    def test_pagination_preserves_filters_and_stable_order(self):
        response = self.client.get("/products/", {"category": self.category.pk, "brand": self.brand.pk, "min_price": "0", "q": "Racket"})
        self.assertEqual(len(response.context["page"].object_list), 12)
        self.assertContains(response, f"category={self.category.pk}&amp;brand={self.brand.pk}&amp;min_price=0&amp;q=Racket&amp;page=2")
        response = self.client.get("/products/", {"page": "2", "category": self.category.pk})
        self.assertEqual([p.pk for p in response.context["page"].object_list], [p.pk for p in self.products[12:]])
        self.assertEqual(self.client.get("/products/?page=bad").context["page"].number, 1)
        self.assertEqual(self.client.get("/products/?page=999").context["page"].number, 2)

    def test_detail_missing_inactive_and_unavailable_modules(self):
        response = self.client.get(f"/products/{self.products[0].pk}/")
        self.assertContains(response, self.products[0].product_name)
        self.assertContains(response, "Sắp có")
        self.assertNotContains(response, 'href="#"')
        self.assertEqual(self.client.get("/products/999999/").status_code, 404)
        self.assertEqual(self.client.get(f"/products/{self.inactive.pk}/").status_code, 404)
        self.assertEqual(self.client.post("/products/", {}).status_code, 405)
        self.assertEqual(self.client.post("/", {}).status_code, 405)

"""Storefront presentation contracts, using only the isolated Django test DB."""

from decimal import Decimal
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.catalog.models import Brand, Category, Product, Supplier
from .templatetags.shop_ui import vnd_price


class StorefrontHTML(HTMLParser):
    """Read links and form controls without depending on layout classes."""

    def __init__(self, html):
        super().__init__()
        self.links = []
        self.forms = []
        self.selects = {}
        self._link = None
        self._form = None
        self._select = None
        self._option = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self._link = [attrs.get("href", ""), []]
        elif tag == "form":
            self._form = {"action": attrs.get("action", ""), "method": attrs.get("method", "get").lower(), "fields": set()}
            self.forms.append(self._form)
        elif tag in ("input", "select", "textarea"):
            if self._form is not None:
                self._form["fields"].add(attrs.get("name"))
            if tag == "select":
                self._select = attrs.get("name")
                self.selects[self._select] = []
        elif tag == "option" and self._select is not None:
            self._option = [attrs.get("value", ""), []]

    def handle_data(self, text):
        if self._link is not None:
            self._link[1].append(text)
        if self._option is not None:
            self._option[1].append(text)

    def handle_endtag(self, tag):
        if tag == "a" and self._link is not None:
            self.links.append((self._link[0], " ".join("".join(self._link[1]).split())))
            self._link = None
        elif tag == "form":
            self._form = None
        elif tag == "option" and self._option is not None:
            self.selects[self._select].append((self._option[0], "".join(self._option[1]).strip()))
            self._option = None
        elif tag == "select":
            self._select = None

    def category_links(self):
        result = []
        for href, text in self.links:
            parts = urlsplit(href)
            category = parse_qs(parts.query).get("category")
            if parts.path == reverse("shop:products") and category:
                result.append((category[0], text))
        return result


class ShopDisplayFilterTests(SimpleTestCase):
    def test_vnd_price_preserves_decimal_precision_independent_of_language(self):
        values = {
            Decimal("0.00"): "0 ₫",
            Decimal("1250000.00"): "1.250.000 ₫",
            Decimal("1250000.50"): "1.250.000,50 ₫",
            Decimal("9999999999.99"): "9.999.999.999,99 ₫",
        }
        for language in ("vi", "en-us"):
            with override_settings(LANGUAGE_CODE=language):
                for value, expected in values.items():
                    with self.subTest(language=language, value=value):
                        self.assertEqual(vnd_price(value), expected)



class ShopNavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Deliberately insert in reverse order to catch unsorted navigation.
        cls.shoes = Category.objects.create(category_name="Shoes")
        cls.rackets = Category.objects.create(category_name="Rackets")
        cls.inactive = Category.objects.create(category_name="Hidden category", status="INACTIVE")
        cls.brand = Brand.objects.create(brand_name="Brand only label")
        cls.inactive_brand = Brand.objects.create(brand_name="Hidden brand", status="INACTIVE")
        cls.supplier = Supplier.objects.create(supplier_code="SHOP-UI", supplier_name="Test supplier")
        cls.product = Product.objects.create(
            category=cls.rackets, brand=cls.brand, supplier=cls.supplier,
            product_name="Decimal price racket", price=Decimal("1250000.50"),
        )

    def page_html(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return response, StorefrontHTML(response.content.decode())

    def test_active_categories_appear_on_store_auth_and_detail_pages_without_brand_links(self):
        expected = [(str(self.rackets.pk), self.rackets.category_name), (str(self.shoes.pk), self.shoes.category_name)]
        for path in ("/", "/products/", "/login/", "/register/", "/password/reset/", reverse("shop:product_detail", args=[self.product.pk])):
            with self.subTest(path=path):
                response, html = self.page_html(path)
                # Home category tiles and the detail breadcrumb can repeat links;
                # their first occurrences still follow the shared DB navigation.
                self.assertEqual(html.category_links()[:2], expected)
                self.assertNotContains(response, self.inactive.category_name)
                self.assertNotIn(self.brand.brand_name, [text for _, text in html.category_links()])

    def test_category_navigation_updates_between_requests_and_handles_empty_database(self):
        _, before = self.page_html("/login/")
        self.assertEqual(len(before.category_links()), 2)
        Category.objects.update(status="INACTIVE")
        response, after = self.page_html("/login/")
        self.assertEqual(after.category_links(), [])
        self.assertNotContains(response, self.rackets.category_name)
        self.assertNotContains(response, self.shoes.category_name)
        # The full catalogue remains accessible even without category links.
        self.assertIn(reverse("shop:products"), [href for href, _ in after.links])

    def test_category_and_brand_filter_choices_remain_separate_and_search_form_has_real_target(self):
        _, html = self.page_html("/products/")
        self.assertEqual([option for option in html.selects["category"] if option[0]], [
            (str(self.rackets.pk), "Rackets"), (str(self.shoes.pk), "Shoes"),
        ])
        self.assertEqual([option for option in html.selects["brand"] if option[0]], [(str(self.brand.pk), self.brand.brand_name)])
        self.assertTrue(any(form["method"] == "get" and form["action"] == reverse("shop:products") and "q" in form["fields"] for form in html.forms))
        response = self.client.get(reverse("shop:products"), {"q": "Decimal price"})
        self.assertEqual(list(response.context["page"].object_list), [self.product])

    def test_price_and_honest_missing_image_label_match_on_cards_and_detail(self):
        for path in ("/", "/products/", reverse("shop:product_detail", args=[self.product.pk])):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertContains(response, "1.250.000,50 ₫")
                self.assertContains(response, "/static/images/product-image-unavailable.svg")
                self.assertContains(response, "Chưa có ảnh")

    def test_active_product_with_inactive_category_does_not_link_to_invalid_filter(self):
        Category.objects.filter(pk=self.rackets.pk).update(status="INACTIVE")
        response, html = self.page_html(reverse("shop:product_detail", args=[self.product.pk]))
        self.assertContains(response, self.product.product_name)
        self.assertContains(response, self.rackets.category_name)
        self.assertNotIn(str(self.rackets.pk), [category_id for category_id, _ in html.category_links()])
        self.assertIn(reverse("shop:products"), [href for href, _ in html.links])
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, "ACTIVE")

    def test_demo_labels_are_preserved_and_searchable(self):
        self.rackets.category_name = "Demo Rackets"
        self.rackets.save(update_fields=["category_name"])
        self.brand.brand_name = "PR2 kiểm thử thương hiệu"
        self.brand.save(update_fields=["brand_name"])
        self.product.product_name = "Demo Racket 01"
        self.product.save(update_fields=["product_name"])
        for path in ("/", "/products/", reverse("shop:product_detail", args=[self.product.pk])):
            response = self.client.get(path)
            for label in (self.rackets.category_name, self.brand.brand_name, self.product.product_name):
                self.assertContains(response, label)
        response = self.client.get("/products/", {"q": "Demo Racket"})
        self.assertEqual(list(response.context["page"].object_list), [self.product])

    def test_admin_login_remains_outside_customer_styles(self):
        for path in ("/admin/login/", "/manager/login/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, "/static/css/customer.css")
            self.assertNotContains(response, "/static/css/tv1.css")
            self.assertNotContains(response, 'class="customer-layout"')

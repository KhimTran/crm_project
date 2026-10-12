"""Catalog validation, CRUD, filtering and authorization regressions for PR #4."""
from decimal import Decimal
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from .forms import SupplierForm
from .models import Brand, Category, Product, Supplier


class SupplierPhoneTests(TestCase):
    def payload(self, phone, code="PHONE01"):
        return {"supplier_code": code, "supplier_name": "Phone supplier", "status": "ACTIVE", "phone": phone}

    def test_optional_phone_is_stored_as_null(self):
        for index, phone in enumerate((None, "", "   ")):
            with self.subTest(phone=phone):
                data = self.payload(phone, code=f"EMPTY{index}")
                if phone is None:
                    data.pop("phone")
                form = SupplierForm(data)
                self.assertTrue(form.is_valid(), form.errors)
                self.assertIsNone(form.save().phone)

    def test_valid_digit_counts_and_separators_are_preserved(self):
        for phone in ("0901234567", "123456789", "+123456789012345", "+84 912 345 678",
                      "(090) 123-4567", "090.123.4567", "+1 (202) 555-0123", "  090-123-4567  "):
            with self.subTest(phone=phone):
                form = SupplierForm(self.payload(phone))
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["phone"], phone.strip())

    def test_punctuation_only_and_invalid_digit_counts_are_rejected(self):
        for phone in ("........", "----------", "( . - . )", "+........", "12345678",
                      "1234567890123456", "+84 (1) --", "123456789012345678901"):
            with self.subTest(phone=phone):
                form = SupplierForm(self.payload(phone))
                self.assertFalse(form.is_valid())
                self.assertIn("phone", form.errors)

    def test_plus_must_be_single_and_leading_and_characters_are_limited(self):
        for phone in ("090+1234567", "0901234567+", "++84912345678", "+84+912345678",
                      "(+84) 912345678", "090123456a", "090/123/4567", "０９０１２３４５６７"):
            with self.subTest(phone=phone):
                form = SupplierForm(self.payload(phone))
                self.assertFalse(form.is_valid())
                self.assertIn("phone", form.errors)


class CatalogFixtures(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser("pr4-admin@example.test", "StrongPass!2026")
        cls.category = Category.objects.create(category_name="Rackets")
        cls.brand = Brand.objects.create(brand_name="Yonex")
        cls.supplier = Supplier.objects.create(supplier_code="SUP001", supplier_name="Supplier")
        cls.product = Product.objects.create(category=cls.category, brand=cls.brand, supplier=cls.supplier,
                                            product_name="Racket", price=Decimal("100.00"))

    def setUp(self):
        self.client.force_login(self.admin)

    def product_payload(self, **changes):
        return {"product_name": "New racket", "price": "100.50", "status": "ACTIVE",
                "category": self.category.pk, "brand": self.brand.pk, "supplier": self.supplier.pk,
                **changes}


class CatalogManagementTests(CatalogFixtures):
    def assert_simple_crud(self, kind, model, name_field):
        create_url = reverse(f"catalog_admin:{kind}_create")
        list_url = reverse(f"catalog_admin:{kind}_list")
        self.assertEqual(self.client.get(create_url).status_code, 200)
        response = self.client.post(create_url, {name_field: "  New record  ", "description": "First", "status": "ACTIVE"})
        self.assertRedirects(response, list_url)
        record = model.objects.get(**{name_field: "New record"})
        self.assertContains(self.client.get(list_url), "New record")
        edit_url = reverse(f"catalog_admin:{kind}_edit", args=[record.pk])
        self.assertEqual(self.client.get(edit_url).status_code, 200)
        self.assertRedirects(self.client.post(edit_url, {name_field: "Renamed", "description": "Updated", "status": "INACTIVE"}), list_url)
        record.refresh_from_db()
        self.assertEqual((getattr(record, name_field), record.description, record.status), ("Renamed", "Updated", "INACTIVE"))
        # Keeping one's own name on edit must not be treated as a duplicate.
        self.assertRedirects(self.client.post(edit_url, {name_field: "Renamed", "status": "INACTIVE"}), list_url)
        self.assertRedirects(self.client.post(reverse(f"catalog_admin:{kind}_delete", args=[record.pk])), list_url)
        self.assertFalse(model.objects.filter(pk=record.pk).exists())

    def test_category_crud(self):
        self.assert_simple_crud("category", Category, "category_name")

    def test_brand_crud(self):
        self.assert_simple_crud("brand", Brand, "brand_name")

    def test_duplicate_names_rejected_on_create_and_edit(self):
        for kind, model, field, existing in (("category", Category, "category_name", self.category),
                                              ("brand", Brand, "brand_name", self.brand)):
            with self.subTest(kind=kind):
                before = model.objects.count()
                duplicate_name = "  " + getattr(existing, field).swapcase() + "  "
                response = self.client.post(reverse(f"catalog_admin:{kind}_create"), {field: duplicate_name, "status": "ACTIVE"})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertEqual(model.objects.count(), before)
                other = model.objects.create(**{field: "Other"})
                response = self.client.post(reverse(f"catalog_admin:{kind}_edit", args=[other.pk]), {field: duplicate_name, "status": "ACTIVE"})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                other.refresh_from_db()
                self.assertEqual(getattr(other, field), "Other")

    def test_categories_and_brands_with_products_are_protected(self):
        for kind, model, record in (("category", Category, self.category), ("brand", Brand, self.brand)):
            with self.subTest(kind=kind):
                response = self.client.post(reverse(f"catalog_admin:{kind}_delete", args=[record.pk]), follow=True)
                self.assertContains(response, "đang có sản phẩm")
                self.assertTrue(model.objects.filter(pk=record.pk).exists())
                self.product.refresh_from_db()
                self.assertEqual(getattr(self.product, f"{kind}_id"), record.pk)

    def test_supplier_code_duplicate_rejected_and_own_code_edit_allowed(self):
        payload = {"supplier_code": "  sup001  ", "supplier_name": "Duplicate", "status": "ACTIVE"}
        response = self.client.post(reverse("catalog_admin:supplier_create"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("supplier_code", response.context["form"].errors)
        self.assertEqual(Supplier.objects.count(), 1)
        other = Supplier.objects.create(supplier_code="SUP002", supplier_name="Other")
        response = self.client.post(reverse("catalog_admin:supplier_edit", args=[other.pk]), payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("supplier_code", response.context["form"].errors)
        other.refresh_from_db()
        self.assertEqual(other.supplier_code, "SUP002")
        payload.update(supplier_code=" SUP001 ", supplier_name="Updated")
        self.assertRedirects(self.client.post(reverse("catalog_admin:supplier_edit", args=[self.supplier.pk]), payload), reverse("catalog_admin:supplier_list"))

    def test_supplier_phone_validation_on_create_and_edit(self):
        data = {"supplier_code": "SUP002", "supplier_name": "Other", "status": "ACTIVE", "phone": "........"}
        response = self.client.post(reverse("catalog_admin:supplier_create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("phone", response.context["form"].errors)
        self.assertFalse(Supplier.objects.filter(supplier_code="SUP002").exists())
        data["supplier_code"] = self.supplier.supplier_code
        response = self.client.post(reverse("catalog_admin:supplier_edit", args=[self.supplier.pk]), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("phone", response.context["form"].errors)
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.supplier_name, "Supplier")
        self.assertIsNone(self.supplier.phone)


class ProductValidationTests(CatalogFixtures):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.inactive = {
            "category": Category.objects.create(category_name="Inactive category", status="INACTIVE"),
            "brand": Brand.objects.create(brand_name="Inactive brand", status="INACTIVE"),
            "supplier": Supplier.objects.create(supplier_code="OFF001", supplier_name="Inactive supplier", status="INACTIVE"),
        }

    def test_product_price_must_be_strictly_positive_on_create_and_edit(self):
        for price in ("0", "0.00", "-0.01", "-100.00"):
            for route, args in (("product_create", []), ("product_edit", [self.product.pk])):
                with self.subTest(price=price, route=route):
                    response = self.client.post(reverse("catalog_admin:" + route, args=args), self.product_payload(price=price))
                    self.assertEqual(response.status_code, 200)
                    self.assertIn("price", response.context["form"].errors)
                    self.product.refresh_from_db()
                    self.assertEqual(self.product.price, Decimal("100.00"))
                    self.assertEqual(Product.objects.count(), 1)
        response = self.client.post(reverse("catalog_admin:product_create"), self.product_payload(price="0.01"))
        self.assertRedirects(response, reverse("catalog_admin:product_list"))
        self.assertEqual(Product.objects.get(product_name="New racket").price, Decimal("0.01"))

    def test_product_create_choices_exclude_all_inactive_relationships(self):
        form = self.client.get(reverse("catalog_admin:product_create")).context["form"]
        for field, record in self.inactive.items():
            with self.subTest(field=field):
                self.assertNotIn(record.pk, form.fields[field].queryset.values_list("pk", flat=True))
                self.assertIn(getattr(self, field).pk, form.fields[field].queryset.values_list("pk", flat=True))

    def test_forged_inactive_relationships_on_create_are_rejected(self):
        for field, record in self.inactive.items():
            with self.subTest(field=field):
                response = self.client.post(reverse("catalog_admin:product_create"), self.product_payload(**{field: record.pk}))
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.assertEqual(Product.objects.count(), 1)

    def test_product_edit_retains_current_inactive_relationships(self):
        for field in self.inactive:
            record = getattr(self, field)
            record.status = "INACTIVE"
            record.save(update_fields=["status"])
        url = reverse("catalog_admin:product_edit", args=[self.product.pk])
        form = self.client.get(url).context["form"]
        for field, other in self.inactive.items():
            with self.subTest(field=field):
                self.assertIn(getattr(self, field).pk, form.fields[field].queryset.values_list("pk", flat=True))
                self.assertNotIn(other.pk, form.fields[field].queryset.values_list("pk", flat=True))
        self.assertRedirects(self.client.post(url, self.product_payload(product_name="Kept relationships")), reverse("catalog_admin:product_list"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.product_name, "Kept relationships")
        self.assertEqual((self.product.category_id, self.product.brand_id, self.product.supplier_id),
                         (self.category.pk, self.brand.pk, self.supplier.pk))

    def test_product_edit_cannot_switch_to_other_inactive_relationships(self):
        for field, record in self.inactive.items():
            with self.subTest(field=field):
                response = self.client.post(reverse("catalog_admin:product_edit", args=[self.product.pk]), self.product_payload(**{field: record.pk}))
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context["form"].errors)
                self.product.refresh_from_db()
                self.assertEqual(getattr(self.product, field + "_id"), getattr(self, field).pk)

    def test_inactive_relation_is_revalidated_if_disabled_after_form_display(self):
        self.client.get(reverse("catalog_admin:product_create"))
        self.category.status = "INACTIVE"
        self.category.save(update_fields=["status"])
        response = self.client.post(reverse("catalog_admin:product_create"), self.product_payload())
        self.assertEqual(response.status_code, 200)
        self.assertIn("category", response.context["form"].errors)
        self.assertEqual(Product.objects.count(), 1)


class LinkParser(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.links = []
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            self.links.append((href, parse_qs(urlsplit(href).query)))


class CatalogQueryTests(CatalogFixtures):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.other_category = Category.objects.create(category_name="Shoes")
        cls.other_brand = Brand.objects.create(brand_name="Victor")
        cls.other_supplier = Supplier.objects.create(supplier_code="SUP002", supplier_name="Other Supplier")

    def test_product_combined_filters_intersect_all_fields(self):
        # Each decoy fails exactly one filter; dropping any filter exposes it.
        Product.objects.create(category=self.category, brand=self.brand, supplier=self.supplier,
                               product_name="Target B", price="200.00")
        for changes in ({"category": self.other_category}, {"brand": self.other_brand},
                        {"supplier": self.other_supplier}, {"status": "INACTIVE"}, {"product_name": "Different"}):
            Product.objects.create(**{"category": self.category, "brand": self.brand, "supplier": self.supplier,
                                      "product_name": "Target decoy", "price": "300.00", **changes})
        params = {"q": " target ", "status": "active", "category": self.category.pk,
                  "brand": self.brand.pk, "supplier": self.supplier.pk}
        response = self.client.get(reverse("catalog_admin:product_list"), params)
        self.assertEqual([p.product_name for p in response.context["items"]], ["Target B"])
        self.assertEqual(response.context["query"], "target")
        self.assertEqual(response.context["status_filter"], "ACTIVE")

    def test_product_price_sort_asc_desc_and_stable_ties(self):
        cheap = Product.objects.create(category=self.category, brand=self.brand, supplier=self.supplier, product_name="Cheap", price="2.00")
        equal = Product.objects.create(category=self.category, brand=self.brand, supplier=self.supplier, product_name="Equal", price="100.00")
        expensive = Product.objects.create(category=self.category, brand=self.brand, supplier=self.supplier, product_name="Expensive", price="1000.00")
        for direction, expected in (("asc", [cheap.pk, self.product.pk, equal.pk, expensive.pk]),
                                     ("desc", [expensive.pk, self.product.pk, equal.pk, cheap.pk])):
            with self.subTest(direction=direction):
                response = self.client.get(reverse("catalog_admin:product_list"), {"sort": "price", "dir": direction})
                self.assertEqual([p.pk for p in response.context["items"]], expected)

    def test_related_column_sorts_follow_names_in_both_directions(self):
        other = Product.objects.create(category=self.other_category, brand=self.other_brand, supplier=self.other_supplier,
                                       product_name="Other", price="50.00")
        for key, ascending in (("category", [self.product.pk, other.pk]), ("brand", [other.pk, self.product.pk]),
                                ("supplier", [other.pk, self.product.pk])):
            for direction, expected in (("asc", ascending), ("desc", list(reversed(ascending)))):
                with self.subTest(key=key, direction=direction):
                    response = self.client.get(reverse("catalog_admin:product_list"), {"sort": key, "dir": direction})
                    self.assertEqual([p.pk for p in response.context["items"]], expected)

    def test_supplier_and_simple_lists_combine_filters_and_sort_both_ways(self):
        for kind, model, field, extra in (("supplier", Supplier, "supplier_name", {"supplier_code": "MATCH01"}),
                                        ("category", Category, "category_name", {}), ("brand", Brand, "brand_name", {})):
            with self.subTest(kind=kind):
                first = model.objects.create(**{field: "Match Alpha", **extra})
                second_extra = {"supplier_code": "MATCH02"} if kind == "supplier" else {}
                second = model.objects.create(**{field: "Match Zulu", **second_extra})
                inactive_extra = {"supplier_code": "MATCH03"} if kind == "supplier" else {}
                model.objects.create(**{field: "Match Inactive", "status": "INACTIVE", **inactive_extra})
                for direction, expected in (("asc", [first.pk, second.pk]), ("desc", [second.pk, first.pk])):
                    response = self.client.get(reverse(f"catalog_admin:{kind}_list"), {"q": " match ", "status": "active", "sort": "name", "dir": direction})
                    self.assertEqual([row.pk for row in response.context["items"]], expected)

    def assert_page_links(self, response, expected_params, target_page):
        links = LinkParser(response.content.decode()).links
        paging = [(href, params) for href, params in links if params.get("page") == [str(target_page)]]
        self.assertTrue(paging, "Missing page link")
        for _, params in paging:
            self.assertEqual(params, {**{key: [str(value)] for key, value in expected_params.items()}, "page": [str(target_page)]})
        return paging[0][0]

    def test_product_pagination_and_sort_links_preserve_combined_filters(self):
        Product.objects.bulk_create([Product(category=self.category, brand=self.brand, supplier=self.supplier,
            product_name=f"Match {index:02}", price=Decimal(index + 1)) for index in range(12)])
        params = {"q": "Match", "status": "ACTIVE", "category": self.category.pk, "brand": self.brand.pk,
                  "supplier": self.supplier.pk, "sort": "price", "dir": "desc"}
        url = reverse("catalog_admin:product_list")
        first = self.client.get(url, params)
        self.assertEqual(len(first.context["items"]), 10)
        next_link = self.assert_page_links(first, params, 2)
        second = self.client.get(url + next_link)
        self.assertEqual(second.context["page_obj"].number, 2)
        self.assertEqual(len(second.context["items"]), 2)
        self.assert_page_links(second, params, 1)
        self.assertFalse({p.pk for p in first.context["items"]} & {p.pk for p in second.context["items"]})
        self.assertEqual([p.price for p in first.context["items"]] + [p.price for p in second.context["items"]],
                         [Decimal(i) for i in range(12, 0, -1)])
        price_links = [(href, data) for href, data in LinkParser(first.content.decode()).links
                       if data.get("sort") == ["price"] and "page" not in data]
        self.assertTrue(price_links)
        expected = {**params, "dir": "asc"}
        self.assertEqual(price_links[0][1], {k: [str(v)] for k, v in expected.items()})

    def test_supplier_category_and_brand_pagination_preserves_filter_and_sort(self):
        for kind, model, field, total in (("supplier", Supplier, "supplier_name", 22),
                                        ("category", Category, "category_name", 12), ("brand", Brand, "brand_name", 12)):
            with self.subTest(kind=kind):
                model.objects.bulk_create([model(**{field: f"Page Match {index:02}",
                    **({"supplier_code": f"PAGE{index:03}"} if kind == "supplier" else {})}) for index in range(total)])
                params = {"q": "Page Match", "status": "ACTIVE", "sort": "name", "dir": "desc"}
                url = reverse(f"catalog_admin:{kind}_list")
                first = self.client.get(url, params)
                next_link = self.assert_page_links(first, params, 2)
                second = self.client.get(url + next_link)
                self.assert_page_links(second, params, 1)
                rows = [*first.context["items"], *second.context["items"]]
                self.assertEqual(len(rows), total)
                self.assertEqual(len({row.pk for row in rows}), total)
                self.assertEqual([getattr(row, field) for row in rows], [f"Page Match {index:02}" for index in range(total - 1, -1, -1)])

    def test_invalid_sort_direction_and_filter_ids_do_not_break_lists(self):
        for kind in ("supplier", "category", "brand", "product"):
            with self.subTest(kind=kind):
                response = self.client.get(reverse(f"catalog_admin:{kind}_list"), {"sort": "price; DROP TABLE products", "dir": "bad",
                    "category": "bad", "brand": "-1", "supplier": "bad", "status": "unknown", "page": "bad"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["direction"], "asc")
                self.assertEqual(response.context["status_filter"], "")
                self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())


class CatalogAuthorizationTests(CatalogFixtures):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.customer = get_user_model().objects.create_user("pr4-customer@example.test", "StrongPass!2026")
        cls.customer.groups.add(Group.objects.create(name="CRM_MANAGER"), Group.objects.create(name="CUSTOMER_SERVICE"))

    def routes(self):
        for kind, record, field in (("category", self.category, "category_name"), ("brand", self.brand, "brand_name"),
                                     ("supplier", self.supplier, "supplier_name"), ("product", self.product, "product_name")):
            payload = self.product_payload() if kind == "product" else {field: "Unauthorized", "status": "ACTIVE"}
            if kind == "supplier":
                payload["supplier_code"] = "UNAUTHORIZED"
            yield kind, "list", reverse(f"catalog_admin:{kind}_list"), {}
            yield kind, "create", reverse(f"catalog_admin:{kind}_create"), payload
            yield kind, "edit", reverse(f"catalog_admin:{kind}_edit", args=[record.pk]), payload
            yield kind, "delete", reverse(f"catalog_admin:{kind}_delete", args=[record.pk]), {}

    def snapshot(self):
        return {model._meta.label: list(model.objects.order_by("pk").values()) for model in (Category, Brand, Supplier, Product)}

    def test_anonymous_get_and_post_are_redirected_without_mutation(self):
        self.client.logout()
        before = self.snapshot()
        for kind, action, url, payload in self.routes():
            for method in ("get", "post"):
                with self.subTest(kind=kind, action=action, method=method):
                    response = getattr(self.client, method)(url, payload)
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(urlsplit(response.url).path, reverse("login"))
        self.assertEqual(self.snapshot(), before)

    def test_customer_with_crm_groups_cannot_manage_catalog(self):
        self.client.force_login(self.customer)
        before = self.snapshot()
        for kind, action, url, payload in self.routes():
            for method in ("get", "post"):
                with self.subTest(kind=kind, action=action, method=method):
                    self.assertEqual(getattr(self.client, method)(url, payload).status_code, 403)
        self.assertEqual(self.snapshot(), before)

    def test_locked_and_demoted_admin_existing_sessions_are_rejected(self):
        for update in ({"status": "LOCKED"}, {"role": "CUSTOMER"}):
            with self.subTest(update=update):
                get_user_model().objects.filter(pk=self.admin.pk).update(role="ADMIN", status="ACTIVE")
                self.admin.refresh_from_db()
                self.client.force_login(self.admin)
                get_user_model().objects.filter(pk=self.admin.pk).update(**update)
                before = self.snapshot()
                for _, action, url, payload in self.routes():
                    response = self.client.get(url) if action == "list" else self.client.post(url, payload)
                    self.assertIn(response.status_code, (302, 403))
                self.assertEqual(self.snapshot(), before)

    def test_active_admin_can_open_every_list_create_and_edit_page(self):
        for kind, action, url, _ in self.routes():
            if action != "delete":
                with self.subTest(kind=kind, action=action):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_delete_only_accepts_post_and_csrf_is_required(self):
        before = self.snapshot()
        for kind, action, url, _ in self.routes():
            if action == "delete":
                for method in ("get", "head", "put", "patch", "delete"):
                    with self.subTest(kind=kind, method=method):
                        self.assertEqual(getattr(self.client, method)(url).status_code, 405)
        self.assertEqual(self.snapshot(), before)
        protected = Client(enforce_csrf_checks=True)
        protected.force_login(self.admin)
        for kind, action, url, _ in self.routes():
            if action == "delete":
                with self.subTest(kind=kind):
                    self.assertEqual(protected.post(url).status_code, 403)
        self.assertEqual(self.snapshot(), before)
        # A valid POST is permitted, after CSRF issuance by the list page.
        protected.get(reverse("catalog_admin:product_list"))
        response = protected.post(reverse("catalog_admin:product_delete", args=[self.product.pk]),
                                  HTTP_X_CSRFTOKEN=protected.cookies["csrftoken"].value)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

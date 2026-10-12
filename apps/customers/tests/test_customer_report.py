from datetime import date, datetime

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.catalog.models import Brand, Category, Product, Supplier
from apps.customers import reports
from apps.customers.models import Customer
from apps.customers.services import create_customer, delete_customer, lock_customer
from apps.feedback.models import Feedback

TODAY = date(2026, 10, 5)


# tv4: lấy số đếm theo nhãn từ danh sách {label, count}
def counts(rows):
    return {r["label"]: r["count"] for r in rows}


# tv4: test 4.1.5 số liệu báo cáo khách hàng và trang biểu đồ
class CustomerReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@example.com", "Quanly@12345")
        cls.manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        cls.an, _ = create_customer(email="an@example.com", full_name="An", phone="0900000001",
                                    date_of_birth=date(2008, 10, 5), gender="MALE", playing_level="BEGINNER",
                                    play_styles=["Tấn công"], brands=["Yonex"])
        cls.binh, _ = create_customer(email="binh@example.com", full_name="Bình", phone="0900000002",
                                      date_of_birth=date(1995, 3, 1), gender="FEMALE", playing_level="BEGINNER",
                                      brands=["Yonex", "Victor"])
        cls.cuong, _ = create_customer(email="cuong@example.com", full_name="Cường", phone="0900000003")
        cls.deleted, _ = create_customer(email="xoa@example.com", full_name="Đã xóa", phone="0900000004",
                                         date_of_birth=date(1990, 1, 1), gender="MALE", brands=["Yonex"])
        delete_customer(cls.deleted.pk)
        lock_customer(cls.cuong.pk)
        # Bình đăng ký từ 3 tháng trước.
        Customer.objects.filter(pk=cls.binh.pk).update(
            created_at=timezone.make_aware(datetime(2026, 7, 15, 10, 0)))

        category = Category.objects.create(category_name="Vợt")
        brand = Brand.objects.create(brand_name="Yonex")
        supplier = Supplier.objects.create(supplier_code="NCC01", supplier_name="NCC 1")
        racket = Product.objects.create(category=category, brand=brand, supplier=supplier,
                                        product_name="Astrox 88D", price=3500000)
        shoe = Product.objects.create(category=category, brand=brand, supplier=supplier,
                                      product_name="Giày SHB", price=2000000)
        for product, rating in ((racket, 5), (racket, 4), (shoe, 2)):
            Feedback.objects.create(customer=cls.an, product=product, rating=rating, content="x", status="NEW")

    def test_age_gender_level_exclude_deleted_and_count_unknown(self):
        age = counts(reports.age_group_report(today=TODAY))
        self.assertEqual(age["18–24"], 1)
        self.assertEqual(age["25–34"], 1)
        self.assertEqual(age["35–44"], 0)
        self.assertEqual(age[reports.UNKNOWN_LABEL], 1)
        self.assertEqual(counts(reports.gender_report()), {"Nam": 1, "Nữ": 1, "Khác": 0, reports.UNKNOWN_LABEL: 1})
        level = counts(reports.playing_level_report())
        self.assertEqual((level["Mới chơi"], level["Thi đấu"], level[reports.UNKNOWN_LABEL]), (2, 0, 1))

    def test_preferences_grouped_by_type(self):
        groups = {g["type"]: counts(g["rows"]) for g in reports.preference_report()}
        self.assertEqual(groups["BRAND"], {"Yonex": 2, "Victor": 1})
        self.assertEqual(groups["PLAY_STYLE"], {"Tấn công": 1})
        self.assertNotIn("CATEGORY", groups)

    def test_new_customers_by_month_fills_empty_months(self):
        Customer.objects.filter(pk=self.an.pk).update(created_at=timezone.make_aware(datetime(2026, 10, 1, 8, 0)))
        Customer.objects.filter(pk=self.cuong.pk).update(created_at=timezone.make_aware(datetime(2025, 9, 30, 8, 0)))
        rows = reports.new_customers_by_month(months=12, today=TODAY)
        self.assertEqual([r["label"] for r in rows][:2], ["11/2025", "12/2025"])
        self.assertEqual(rows[-1], {"label": "10/2026", "count": 1})
        self.assertEqual(counts(rows)["07/2026"], 1)
        self.assertEqual(counts(rows)["08/2026"], 0)
        self.assertEqual(sum(r["count"] for r in rows), 2)

    def test_satisfaction_and_summary(self):
        rows = reports.satisfaction_by_product()
        self.assertEqual([(r["label"], r["avg"], r["count"]) for r in rows],
                         [("Giày SHB", 2.0, 1), ("Astrox 88D", 4.5, 2)])
        summary = reports.summary()
        self.assertEqual((summary["total"], summary["locked"], summary["feedbacks"], summary["avg_rating"]),
                         (3, 1, 3, 3.67))

    # tv4: KH đã xóa chấm 1 sao không được tính vào điểm hài lòng và tổng phản hồi
    def test_deleted_customer_feedback_is_excluded(self):
        racket = Product.objects.get(product_name="Astrox 88D")
        Feedback.objects.create(customer=self.deleted, product=racket, rating=1, content="x", status="NEW")
        rows = {r["label"]: (r["avg"], r["count"]) for r in reports.satisfaction_by_product()}
        self.assertEqual(rows["Astrox 88D"], (4.5, 2))
        summary = reports.summary()
        self.assertEqual((summary["feedbacks"], summary["avg_rating"]), (3, 3.67))

    # tv4: hai sản phẩm trùng tên vẫn là hai dòng riêng (nhóm theo ID sản phẩm)
    def test_same_name_products_are_not_merged(self):
        racket = Product.objects.get(product_name="Astrox 88D")
        twin = Product.objects.create(category=racket.category, brand=racket.brand, supplier=racket.supplier,
                                      product_name="Astrox 88D", price=3600000)
        Feedback.objects.create(customer=self.an, product=twin, rating=3, content="x", status="NEW")
        rows = [(r["label"], r["avg"], r["count"]) for r in reports.satisfaction_by_product()]
        self.assertEqual(sorted(rows), sorted([("Giày SHB", 2.0, 1), ("Astrox 88D", 4.5, 2), ("Astrox 88D", 3.0, 1)]))

    def test_report_page_renders_charts_data_and_print_button(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("customer_reports:customers"))
        self.assertContains(response, "Báo cáo khách hàng")
        self.assertContains(response, 'id="report-data"')
        self.assertContains(response, "chart.umd.min.js")
        self.assertContains(response, "In báo cáo")
        self.assertContains(response, "Astrox 88D")

    def test_customer_cannot_open_report(self):
        Account.objects.create_user("shopper@example.com", "Khach@12345")
        self.client.login(email="shopper@example.com", password="Khach@12345")
        self.assertEqual(self.client.get(reverse("customer_reports:customers")).status_code, 302)

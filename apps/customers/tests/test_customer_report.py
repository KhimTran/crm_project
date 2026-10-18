from datetime import date, datetime, timedelta

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

PASSWORD = "CrmFixture!2026"

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
        cls.an = create_customer(password=PASSWORD, email="an@example.com", full_name="An", phone="0900000001",
                                    date_of_birth=date(2008, 10, 5), gender="MALE", playing_level="BEGINNER",
                                    play_styles=["Tấn công"], brands=["Yonex"])
        cls.binh = create_customer(password=PASSWORD, email="binh@example.com", full_name="Bình", phone="0900000002",
                                      date_of_birth=date(1995, 3, 1), gender="FEMALE", playing_level="BEGINNER",
                                      brands=["Yonex", "Victor"])
        cls.cuong = create_customer(password=PASSWORD, email="cuong@example.com", full_name="Cường", phone="0900000003")
        cls.deleted = create_customer(password=PASSWORD, email="xoa@example.com", full_name="Đã xóa", phone="0900000004",
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
        self.assertNotContains(response, 'id="report-data"')
        self.assertContains(response, "chart.umd.min.js")
        self.assertContains(response, "In báo cáo")
        # Kết quả khảo sát đã chuyển sang trang riêng surveys:results.
        self.assertContains(response, 'id="customer-report-data"')
        self.assertContains(response, "Khách hàng theo nhóm tuổi")
        # Đã gỡ khỏi trang: sở thích Nhóm sản phẩm, điểm hài lòng theo sản phẩm, phản hồi theo tháng.
        self.assertNotContains(response, "Astrox 88D")
        self.assertNotContains(response, 'id="chart-satisfaction"')
        self.assertNotContains(response, 'id="r-feedback"')
        self.assertNotContains(response, "Nhóm sản phẩm")
        self.assertNotContains(response, "Kết quả khảo sát")
        self.assertNotContains(response, "Tổng số khảo sát")
        survey_page = self.client.get(reverse("surveys:results"))
        self.assertContains(survey_page, 'id="report-survey"')

    def test_customer_cannot_open_report(self):
        Account.objects.create_user("shopper@example.com", "Khach@12345")
        self.client.login(email="shopper@example.com", password="Khach@12345")
        self.assertEqual(self.client.get(reverse("customer_reports:customers")).status_code, 302)

    # tv4: 4.1.5 mở rộng: tỷ lệ khóa/hoạt động, số KH đã xóa, phản hồi theo tháng/trạng thái, TG xử lý TB
    def test_extended_customer_metrics(self):
        accounts = reports.account_status_report()
        self.assertEqual((accounts["total"], accounts["active"], accounts["locked"]), (3, 2, 1))
        self.assertEqual((accounts["active_pct"], accounts["locked_pct"]), (66.7, 33.3))
        self.assertEqual(reports.deleted_count(), 1)
        feedback = list(Feedback.objects.filter(customer=self.an).order_by("feedback_id"))
        created = timezone.make_aware(datetime(2026, 10, 2, 8, 0))
        Feedback.objects.filter(pk=feedback[0].pk).update(
            status="RESOLVED", created_at=created, resolved_at=created + timedelta(hours=3))
        Feedback.objects.filter(pk=feedback[1].pk).update(
            status="RESOLVED", created_at=created, resolved_at=created + timedelta(hours=5))
        Feedback.objects.filter(pk=feedback[2].pk).update(status="IN_PROGRESS", created_at=created)
        self.assertEqual(reports.avg_resolution_hours(), 4.0)
        months = reports.feedback_by_month(months=6, today=TODAY)
        self.assertEqual(months[-1], {"label": "10/2026", "count": 3, "new": 0, "in_progress": 1, "resolved": 2})
        self.assertEqual(sum(r["count"] for r in months[:-1]), 0)
        status = {r["label"]: (r["count"], r["pct"]) for r in reports.feedback_status_report()}
        self.assertEqual(status, {"Mới": (0, 0.0), "Đang xử lý": (1, 33.3), "Đã xử lý": (2, 66.7)})


# tv4: 4.1.5 ranh giới nhóm tuổi, thiếu ngày sinh, KH đã xóa, sở thích lấy từ hồ sơ (không từ khảo sát)
class CustomerReportBoundaryTests(TestCase):
    def test_age_group_boundaries(self):
        births = {"16": date(2009, 10, 6), "18 hôm nay": date(2008, 10, 5), "24": date(2001, 10, 6),
                  "25 hôm nay": date(2001, 10, 5), "55": date(1971, 10, 5), "thiếu": None}
        for i, (name, dob) in enumerate(births.items()):
            create_customer(password=PASSWORD, email=f"age{i}@example.com", full_name=name,
                            phone=f"09100000{i:02d}", date_of_birth=dob)
        age = counts(reports.age_group_report(today=TODAY))
        self.assertEqual((age["Dưới 18"], age["18–24"], age["25–34"], age["Từ 55"], age[reports.UNKNOWN_LABEL]),
                         (1, 2, 1, 1, 1))

    def test_empty_report_has_no_fake_numbers(self):
        self.assertEqual(reports.account_status_report()["locked_pct"], None)
        self.assertIsNone(reports.avg_resolution_hours())
        self.assertEqual(reports.feedback_status_report()[0]["pct"], None)
        manager = Account.objects.create_user("empty-manager@example.com", "Quanly@12345", role="MANAGER")
        self.client.force_login(manager)
        page = self.client.get(reverse("customer_reports:customers")).content.decode()
        self.assertTrue("Chưa có dữ liệu" in page or "No data yet" in page)
        self.assertNotIn("NaN", page)
        self.assertNotIn("None%", page)

    def test_preferences_come_from_profile_not_survey_answers(self):
        from apps.surveys.models import Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyRecipient, SurveyResponse
        customer = create_customer(password=PASSWORD, email="pref@example.com", full_name="Pref", phone="0920000001",
                                   brands=["Lining"])
        survey = Survey.objects.create(title="KS", status="ACTIVE", created_by=customer.account)
        question = SurveyQuestion.objects.create(survey=survey, question_text="Hãng?", question_type="SINGLE_CHOICE")
        option = SurveyOption.objects.create(question=question, option_text="Yonex")
        recipient = SurveyRecipient.objects.create(survey=survey, customer=customer, status="COMPLETED")
        response = SurveyResponse.objects.create(recipient=recipient, status="SUBMITTED", submitted_at=timezone.now())
        SurveyAnswer.objects.create(response=response, question=question, option=option)
        groups = {g["type"]: counts(g["rows"]) for g in reports.preference_report()}
        self.assertEqual(groups, {"BRAND": {"Lining": 1}})

from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.accounts.constants import AccountStatus
from apps.accounts.models import Account
from apps.customers import reports
from apps.customers.models import Customer, CustomerPreference
from apps.customers.seed import DEMO_CUSTOMER_PASSWORD, demo_email
from apps.feedback.constants import FeedbackStatus
from apps.feedback.models import Feedback
from apps.feedback.seed import CONTENTS, DEMO_BRAND_NAME


# tv4: test seed 40 khách hàng + phản hồi demo, chạy lại không trùng
class SeedDemoDataTests(TestCase):
    # tv4: chạy seed_data hai lần để kiểm tra idempotent
    def seed_twice(self):
        with patch.dict("os.environ", {"CRM_DEMO_PASSWORD": "DemoPass!2026"}):
            call_command("seed_data", verbosity=0)
            call_command("seed_data", verbosity=0)

    def test_seed_creates_customers_and_feedbacks_without_duplicates(self):
        with patch.dict("os.environ", {"CRM_DEMO_PASSWORD": "DemoPass!2026"}):
            call_command("seed_data", verbosity=0)
            first = (Customer.objects.count(), CustomerPreference.objects.count(), Feedback.objects.count())
            call_command("seed_data", verbosity=0)
        self.assertEqual((Customer.objects.count(), CustomerPreference.objects.count(), Feedback.objects.count()),
                         first)
        demo = Customer.objects.filter(account__email__endswith="@example.test", account__email__startswith="kh")
        self.assertEqual(demo.count(), 40)
        self.assertEqual(CustomerPreference.objects.filter(customer__in=demo, preference_type="BRAND")
                         .values("customer").distinct().count(), 40)
        feedbacks = Feedback.objects.filter(customer__in=demo)
        self.assertGreaterEqual(feedbacks.count(), 30)
        self.assertEqual(set(feedbacks.values_list("status", flat=True)), set(FeedbackStatus.values))
        resolved = feedbacks.filter(status=FeedbackStatus.RESOLVED)
        self.assertFalse(resolved.filter(manager_note__isnull=True).exists())
        self.assertFalse(resolved.filter(resolved_at__isnull=True).exists())
        self.assertFalse(feedbacks.exclude(status=FeedbackStatus.NEW).filter(handled_by__isnull=True).exists())

    def test_demo_accounts_login_and_kh40_is_locked(self):
        self.seed_twice()
        self.assertTrue(self.client.login(email=demo_email(1), password=DEMO_CUSTOMER_PASSWORD))
        self.client.logout()
        self.assertEqual(Account.objects.get(email=demo_email(40)).status, AccountStatus.LOCKED)
        self.assertFalse(self.client.login(email=demo_email(40), password=DEMO_CUSTOMER_PASSWORD))

    # tv4: mở khóa kh40 rồi seed lại thì không bị khóa lại
    def test_reseed_does_not_relock_kh40(self):
        self.seed_twice()
        Account.objects.filter(email=demo_email(40)).update(status=AccountStatus.ACTIVE)
        with patch.dict("os.environ", {"CRM_DEMO_PASSWORD": "DemoPass!2026"}):
            call_command("seed_data", verbosity=0)
        self.assertEqual(Account.objects.get(email=demo_email(40)).status, AccountStatus.ACTIVE)

    def test_seed_covers_every_age_group_and_spreads_months(self):
        self.seed_twice()
        age_rows = reports.age_group_report()
        self.assertTrue(all(r["count"] > 0 for r in age_rows))
        months_with_customers = [r for r in reports.new_customers_by_month() if r["count"]]
        self.assertGreaterEqual(len(months_with_customers), 6)

    # tv4: chạy seed_catalog trước thì phản hồi demo gắn với sản phẩm thật, đủ 4 danh mục, nội dung đúng loại
    def test_feedbacks_use_real_catalog_products_when_available(self):
        call_command("seed_catalog", verbosity=0)
        self.seed_twice()
        feedbacks = Feedback.objects.select_related("product__brand", "product__category").filter(
            customer__account__email__in=[demo_email(i) for i in range(1, 41)])
        self.assertGreaterEqual(feedbacks.count(), 30)
        self.assertFalse(feedbacks.filter(product__brand__brand_name=DEMO_BRAND_NAME).exists())
        self.assertEqual(set(feedbacks.values_list("product__category__category_name", flat=True)),
                         {"Badminton rackets", "Badminton shoes", "Shuttlecocks", "Badminton apparel"})
        apparel_contents = {c for texts in CONTENTS["apparel"].values() for c in texts}
        apparel = feedbacks.filter(product__category__category_name="Badminton apparel")
        self.assertTrue(apparel.exists())
        self.assertTrue(all(f.content in apparel_contents for f in apparel))

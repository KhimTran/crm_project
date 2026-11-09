from apps.accounts.testing import PortalTestCase as TestCase
from unittest.mock import patch

from django.core.management import call_command


from apps.accounts.constants import AccountStatus
from apps.accounts.models import Account
from apps.customers import reports
from apps.customers.models import Customer, CustomerPreference
from apps.customers.seed import DEMO_CUSTOMER_PASSWORD, demo_email
from apps.feedback.constants import FeedbackStatus
from apps.feedback.models import Feedback
from apps.feedback.seed import CONTENTS, DEMO_BRAND_NAME


class FinalDemoContractTests(TestCase):
    def test_final_dataset_idempotence_real_logins_statistics_and_preservation(self):
        from django.test import Client
        from django.core.management.base import CommandError
        from django.db import connection, transaction, IntegrityError
        from apps.admin_portal.services.restore_service import database_fingerprint
        from apps.catalog.models import Product, Category, Brand
        from apps.catalog.management.commands.seed_demo import PASSWORD, TITLES
        from apps.surveys.models import Survey, SurveyRecipient, SurveyResponse, SurveyAnswer
        from apps.surveys.services import build_stats, _check_answer_shapes
        # Consume an identifier so the contract cannot accidentally rely on PK=1.
        Account.objects.create_user('discarded@fixture.test','StrongPass!2026').delete()
        call_command('seed_demo', verbosity=0)
        self.assertEqual(Account.objects.count(), 20)
        self.assertEqual(Customer.objects.count(), 15)
        self.assertEqual({r: Account.objects.filter(role__role_code=r).count() for r in ('ADMIN','MANAGER','CUSTOMER')},
                         {'ADMIN':2,'MANAGER':3,'CUSTOMER':15})
        self.assertEqual(Feedback.objects.count(), 20)
        self.assertEqual(Feedback.objects.filter(status='NEW', resolved_at__isnull=True, handled_by__isnull=True).count(),8)
        self.assertEqual(Feedback.objects.filter(status='RESOLVED', handled_by__role__role_code='MANAGER', resolved_at__isnull=False).count(),12)
        self.assertEqual(Survey.objects.count(),18)
        self.assertEqual(SurveyResponse.objects.filter(status='SUBMITTED').count(),61)
        self.assertEqual(SurveyRecipient.objects.count(),91)
        self.assertEqual(Product.objects.count(),61)
        self.assertEqual((Category.objects.count(),Brand.objects.count()),(6,5))
        self.assertEqual(set(Product.objects.filter(status='INACTIVE').values_list('product_name',flat=True)),
                         {'Mizuno Cầu tập luyện','Apacs Cầu lông vũ'})
        before=database_fingerprint(connection.connection)
        call_command('seed_demo', verbosity=0)
        self.assertEqual(database_fingerprint(connection.connection),before)
        for command in ('seed_data','seed_surveys','seed_survey_report_demo'):
            with self.assertRaises(CommandError):
                call_command(command, verbosity=0)
            self.assertEqual(database_fingerprint(connection.connection),before)
        for account in Account.objects.all():
            self.assertTrue(account.check_password(PASSWORD))
            client=Client(enforce_csrf_checks=True)
            url={'ADMIN':'/admin/login/','MANAGER':'/manager/login/','CUSTOMER':'/login/'}[account.role_code]
            client.get(url)
            response=client.post(url,{'email':account.email,'password':PASSWORD,
                                     'csrfmiddlewaretoken':client.cookies['csrftoken'].value})
            self.assertEqual(response.status_code,302,account.email)
            home={'ADMIN':'/admin/accounts/','MANAGER':'/manager/catalog/products/','CUSTOMER':'/account/profile/'}[account.role_code]
            self.assertEqual(client.get(home).status_code,200,account.email)
            if account.role_code!='ADMIN':
                self.assertNotEqual(client.get('/admin/database/').status_code,200)
            if account.role_code!='MANAGER':
                self.assertNotEqual(client.get('/manager/').status_code,200)
        for survey in Survey.objects.all():
            stats=build_stats(survey)
            expected=(0,0) if survey.status=='DRAFT' else (5,3) if survey.status=='ACTIVE' else (7,5)
            self.assertEqual((stats['sent'],stats['responses']),expected,survey.title)
            if survey.status=='DRAFT':
                continue
            self.assertEqual(stats['done'],expected[1])
            self.assertEqual(stats['rate'],round(100*expected[1]/expected[0],1))
            self.assertTrue(all(item['respondents']==expected[1] for item in stats['items']))
            questions={q.pk:q for q in survey.surveyquestion_set.all()}
            for response in SurveyResponse.objects.filter(recipient__survey=survey):
                payload=[]
                for answer in SurveyAnswer.objects.filter(response=response):
                    row={'question_id':answer.question_id}
                    row.update({k:v for k,v in {'option_id':answer.option_id,'rating_value':answer.rating_value,
                                               'answer_text':answer.answer_text}.items() if v is not None})
                    payload.append(row)
                _check_answer_shapes(questions,payload)
                self.assertTrue({q.pk for q in questions.values() if q.is_required}.issubset({a['question_id'] for a in payload}))
                recipient=response.recipient
                self.assertLessEqual(survey.created_at,recipient.sent_at)
                self.assertLessEqual(recipient.sent_at,recipient.opened_at)
                self.assertLessEqual(recipient.opened_at,response.started_at)
                self.assertLessEqual(response.started_at,response.submitted_at)
                self.assertEqual(response.submitted_at,recipient.completed_at)
        sample=SurveyAnswer.objects.filter(question__config__rating_max=10).first()
        with transaction.atomic():
            SurveyAnswer.objects.filter(pk=sample.pk).update(rating_value=10)
            with self.assertRaises(IntegrityError), transaction.atomic():
                SurveyAnswer.objects.filter(pk=sample.pk).update(rating_value=11)
            transaction.set_rollback(True)
        with transaction.atomic():
            SurveyAnswer.objects.filter(question__is_required=True, question__question_type='RATING').first().delete()
            incomplete=database_fingerprint(connection.connection)
            with self.assertRaises(CommandError):
                call_command('seed_demo',verbosity=0)
            self.assertEqual(database_fingerprint(connection.connection),incomplete)
            transaction.set_rollback(True)
        outsider=Account.objects.create_user('real-user@example.test','StrongPass!2026',full_name='Outside dataset')
        product=Product.objects.first()
        Product.objects.filter(pk=product.pk).update(price='123456.00',image_url='https://example.test/custom.jpg')
        preserved=database_fingerprint(connection.connection)
        call_command('seed_demo',verbosity=0)
        self.assertEqual(database_fingerprint(connection.connection),preserved)
        Account.objects.filter(email='cus1@demo.test').update(status='LOCKED')
        preserved=database_fingerprint(connection.connection)
        with self.assertRaises(CommandError):
            call_command('seed_demo',verbosity=0)
        self.assertEqual(database_fingerprint(connection.connection),preserved)


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
            customer__email__in=[demo_email(i) for i in range(1, 41)])
        self.assertGreaterEqual(feedbacks.count(), 30)
        self.assertFalse(feedbacks.filter(product__brand__brand_name=DEMO_BRAND_NAME).exists())
        self.assertEqual(set(feedbacks.values_list("product__category__category_name", flat=True)),
                         {"Badminton rackets", "Badminton shoes", "Shuttlecocks", "Badminton apparel"})
        apparel_contents = {c for texts in CONTENTS["apparel"].values() for c in texts}
        apparel = feedbacks.filter(product__category__category_name="Badminton apparel")
        self.assertTrue(apparel.exists())
        self.assertTrue(all(f.content in apparel_contents for f in apparel))

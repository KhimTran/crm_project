"""TEST DATA for the 8-question Customer Report demo. Never run against real data without the owner's approval.

    python manage.py seed_survey_report_demo --confirm          # create (repeatable: recreates only marked test data)
    python manage.py seed_survey_report_demo --clear --confirm  # remove all of it

Everything created is marked: survey titles start with "[DỮ LIỆU THỬ]", accounts use
the @survey-report-demo.test domain and customer names start with "[Thử]". --clear
deletes only rows carrying these marks; no other survey, customer or account is touched.
"""
import os
import random
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Account
from apps.customers.models import Customer
from apps.surveys.configuration import populate_questionnaire
from apps.surveys.models import Survey, SurveyAnswer, SurveyQuestion, SurveyOption, SurveyRecipient, SurveyResponse
from apps.customers.models import CustomerPreference
from apps.surveys.questionnaire import NOT_USED


TITLE_MARK = "[DỮ LIỆU THỬ]"
EMAIL_DOMAIN = "@survey-report-demo.test"
NAME_MARK = "[Thử]"
CUSTOMERS = 30
COMMENTS = ["Căng vợt chuẩn số kg, thợ đan rất khéo.", "Mong shop nhập thêm nhiều giày Yonex và Mizuno size lớn.",
            "Nhân viên tư vấn nhiệt tình, có hiểu biết sâu về vợt.", "Cần đan vợt lấy liền nhanh hơn vào cuối tuần.",
            "Giá hơi cao so với mặt bằng chung, mong có thêm khuyến mãi.", "Đóng gói cẩn thận hơn khi giao hàng."]
OTHER_BRANDS = ["Apacs", "Kumpoo nội địa Trung", "Fleet"]


# tv4: xóa dữ liệu thử đã đánh dấu
def clear_demo_data():
    """Delete only marked test rows. Survey deletion cascades to questions/options/recipients/responses/answers."""
    surveys = Survey.objects.filter(title__startswith=TITLE_MARK)
    survey_count = surveys.count()
    surveys.delete()
    customers = Customer.objects.filter(email__endswith=EMAIL_DOMAIN, full_name__startswith=NAME_MARK)
    customer_count = customers.count()
    customers.delete()
    return survey_count, customer_count


# tv4: lệnh seed/xóa dữ liệu thử cho báo cáo khảo sát
class Command(BaseCommand):
    help = "Seed or clear clearly marked TEST survey data for the Customer Report demo."

    # tv4: tham số --clear và --confirm
    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Only remove the marked test data.")
        parser.add_argument("--confirm", action="store_true",
                            help="Required: confirms the configured database may receive/lose this test data.")

    # tv4: tạo hoặc xóa dữ liệu thử
    @transaction.atomic
    def handle(self, *args, **options):
        database = settings.DATABASES["default"]["NAME"]
        if not options["confirm"]:
            raise CommandError(f"Refusing to write to database '{database}' without --confirm.")
        if options['clear']:
            surveys, customers = clear_demo_data()
            self.stdout.write(f'Removed {surveys} surveys and {customers} customers.')
            return
        clear_demo_data()
        password = os.environ.get("CRM_DEMO_PASSWORD")
        if not password:
            if not settings.DEBUG:
                raise CommandError("Set CRM_DEMO_PASSWORD before seeding accounts outside DEBUG mode.")
            password = "DemoPass!2026"  # local demo only
        creator = Account.objects.filter(role__in=["MANAGER", "ADMIN"]).order_by("account_id").first()
        if creator is None:
            raise CommandError("Create a MANAGER or ADMIN account first (it becomes the survey creator).")
        rng = random.Random(2026)
        now = timezone.now()
        customers = [Account.objects.create_user(
            f"khach{i:02d}{EMAIL_DOMAIN}", password,
            full_name=f"{NAME_MARK} Khách khảo sát {i:02d}",
        ) for i in range(1, CUSTOMERS + 1)]

        total = 0
        for title, days_ago, answered in ((f"{TITLE_MARK} Trải nghiệm mua sắm – đợt 1", 170, 14),
                                          (f"{TITLE_MARK} Trải nghiệm mua sắm – đợt 2", 60, 12)):
            survey = Survey.objects.create(title=title, status="DRAFT", created_by=creator,
                                           start_at=now - timedelta(days=days_ago), end_at=now + timedelta(days=20),
                                           objective='SATISFACTION', audience={'audience':'pick', 'customer_ids':[c.pk for c in customers]},
                                           description="Dữ liệu thử cho báo cáo – có thể xóa bằng --clear.")
            populate_questionnaire(survey)
            Survey.objects.filter(pk=survey.pk).update(status="ACTIVE")
            q = {x.config["key"]: x for x in survey.surveyquestion_set.all()}
            opt = {k: list(v.surveyoption_set.order_by("sort_order")) for k, v in q.items()}
            for customer in rng.sample(customers, answered):
                when = now - timedelta(days=rng.randint(0, days_ago), hours=rng.randint(0, 23))
                recipient = SurveyRecipient.objects.create(survey=survey, customer=customer, status="COMPLETED",
                                                           opened_at=when, completed_at=when)
                response = SurveyResponse.objects.create(recipient=recipient, status="SUBMITTED",
                                                         started_at=when, submitted_at=when)
                rows = [SurveyAnswer(response=response, question=q["purchases"], option=o)
                        for o in rng.sample(opt["purchases"], rng.randint(1, 3))]
                rows.append(SurveyAnswer(response=response, question=q["playing_frequency"],
                                         option=rng.choices(opt["playing_frequency"], [2, 6, 3, 1])[0]))
                csat = rng.choices([1, 2, 3, 4, 5], [1, 1, 2, 5, 6])[0]
                rows.append(SurveyAnswer(response=response, question=q["overall_satisfaction"], rating_value=csat))
                for o in opt["service_criteria"]:
                    if rng.random() < 0.15:
                        rows.append(SurveyAnswer(response=response, question=q["service_criteria"], option=o,
                                                 answer_text=NOT_USED))
                    else:
                        rows.append(SurveyAnswer(response=response, question=q["service_criteria"], option=o,
                                                 rating_value=rng.choices([2, 3, 4, 5], [1, 2, 5, 4])[0]))
                rows += [SurveyAnswer(response=response, question=q["highlights"], option=o)
                         for o in rng.sample(opt["highlights"], rng.randint(1, 3))]
                other_id = q["future_brands"].config["other_option_id"]
                for o in rng.sample(opt["future_brands"], rng.randint(1, 3)):
                    rows.append(SurveyAnswer(response=response, question=q["future_brands"], option=o,
                                             answer_text=rng.choice(OTHER_BRANDS) if o.pk == other_id else None))
                rows.append(SurveyAnswer(response=response, question=q["recommendation"],
                                         rating_value=rng.choices(range(1, 11), [1, 1, 1, 1, 2, 2, 4, 5, 6, 6])[0]))
                if rng.random() < 0.5:
                    rows.append(SurveyAnswer(response=response, question=q["suggestions"],
                                             answer_text=rng.choice(COMMENTS)))
                SurveyAnswer.objects.bulk_create(rows)
                total += 1

        # Allocate IDs through the ORM; snapshot IDs must never bind to unrelated existing rows.
        brand_names = ['Yonex', 'Li-Ning', 'Victor', 'Mizuno', 'Apacs', 'Kumpoo']
        CustomerPreference.objects.bulk_create([
            CustomerPreference(customer=customer, preference_type='BRAND', preference_value=brand_names[i % 6])
            for i, customer in enumerate(customers)
        ])
        plans = [
            ('NEW_PRODUCT', 'Thăm dò dòng vợt thiên công và giày giảm chấn mới', 'ACTIVE', 24, 20),
            ('SHOPPING_NEEDS', 'Nhu cầu ống cầu, phụ kiện và chu kỳ đan lại cước', 'ACTIVE', 24, 18),
            ('OTHER', 'Giải giao lưu khách hàng thân thiết và ưu đãi thành viên', 'CLOSED', 22, 17),
            ('OTHER', 'Bản nháp ý kiến hoạt động câu lạc bộ cầu lông', 'DRAFT', 0, 0),
        ]
        for objective, title, status, invited, submitted in plans:
            survey = Survey.objects.create(title=f'{TITLE_MARK} {title}', objective=objective, status=status,
                created_by=creator, start_at=now-timedelta(days=7), end_at=now+timedelta(days=20),
                audience={'audience':'pick','customer_ids':[c.pk for c in customers[:invited]]})
            definitions = [
                ('Nhóm sản phẩm bạn quan tâm nhất?', 'SINGLE_CHOICE', ['Vợt thiên công 4U', 'Giày giảm chấn', 'Ống cầu và cước']),
                ('Thương hiệu mong muốn và phụ kiện thường mua?', 'MULTI_CHOICE', brand_names),
                ('Mức giá phù hợp với nhu cầu của bạn?', 'SINGLE_CHOICE', ['Dưới 2.000.000đ', '2.000.000đ – 3.500.000đ', 'Trên 3.500.000đ']),
                ('Mức độ quan tâm ưu đãi tặng cước, quấn cán và đan miễn phí?', 'RATING', []),
                ('Bạn muốn shop cải thiện sản phẩm hoặc hoạt động nào?', 'TEXT', []),
            ]
            questions = []
            for order, (text, kind, choices) in enumerate(definitions, 1):
                question = SurveyQuestion.objects.create(survey=survey, question_text=text, question_type=kind,
                    is_required=True, sort_order=order, config={'rating_min':1,'rating_max':5} if kind=='RATING' else {})
                options = [SurveyOption.objects.create(question=question, option_text=text, sort_order=i)
                           for i, text in enumerate(choices, 1)]
                questions.append((question, options))
            for i, customer in enumerate(customers[:invited]):
                when = now-timedelta(days=i % 6)
                done = i < submitted
                recipient = SurveyRecipient.objects.create(survey=survey, customer=customer,
                    status='COMPLETED' if done else ('SENT' if i % 2 else 'OPENED'),
                    opened_at=when if done or not i % 2 else None, completed_at=when if done else None)
                if not done:
                    continue
                response = SurveyResponse.objects.create(recipient=recipient, status='SUBMITTED', started_at=when, submitted_at=when)
                for question, options in questions:
                    if options:
                        chosen = [options[i % len(options)]]
                        if question.question_type == 'MULTI_CHOICE':
                            chosen.append(options[(i+1) % len(options)])
                        for option in chosen:
                            SurveyAnswer.objects.create(response=response, question=question, option=option)
                    else:
                        SurveyAnswer.objects.create(response=response, question=question,
                            **({'rating_value':3+i % 3} if question.question_type=='RATING' else
                               {'answer_text':COMMENTS[i % len(COMMENTS)]}))
        self.stdout.write(self.style.SUCCESS(
            f'Created 6 marked surveys, {CUSTOMERS} customers; all four objectives. '
            'Remove only marked demo data with --clear --confirm.'))

"""Repeatable survey demo data (TV5). Run AFTER `seed_data`:

    python manage.py seed_surveys

Creates a CRM_MANAGER demo account, 24 demo customers and 3 surveys
(1 DRAFT, 1 ACTIVE with 8/20 answered, 1 CLOSED with 24 answered). Safe to run twice.
"""
import os
import random
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Account
from apps.customers.models import Customer, CustomerPreference
from apps.surveys.constants import MANAGER_GROUP, QuestionType as QT
from apps.surveys.models import (Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyRecipient,
                                 SurveyResponse)

LEVELS = ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
PREFS = ["Badminton rackets", "Shoes", "Strings", "Apparel"]
COMMENTS = ["Mong shop có thêm nhiều mẫu vợt nhẹ đầu.", "Giá hơi cao so với mặt bằng chung.",
            "Căng cước nhanh, nhân viên nhiệt tình.", "Muốn được thử vợt trước khi mua.",
            "Nên có ưu đãi cho học sinh, sinh viên."]


def make_questions(survey, spec):
    for order, (text, qtype, options, required) in enumerate(spec, start=1):
        q = SurveyQuestion.objects.create(survey=survey, question_text=text, question_type=qtype,
                                          is_required=required, sort_order=order)
        SurveyOption.objects.bulk_create([SurveyOption(question=q, option_text=t, sort_order=i)
                                          for i, t in enumerate(options, start=1)])


def answer_all(recipient, rng, when):
    response = SurveyResponse.objects.create(recipient=recipient, status="SUBMITTED",
                                             started_at=when, submitted_at=when)
    rows = []
    for q in SurveyQuestion.objects.filter(survey=recipient.survey):
        options = list(SurveyOption.objects.filter(question=q))
        if q.question_type == QT.SINGLE_CHOICE:
            rows.append(SurveyAnswer(response=response, question=q, option=rng.choice(options)))
        elif q.question_type == QT.MULTI_CHOICE:
            for o in rng.sample(options, rng.randint(1, min(3, len(options)))):
                rows.append(SurveyAnswer(response=response, question=q, option=o))
        elif q.question_type == QT.RATING:
            rows.append(SurveyAnswer(response=response, question=q,
                                     rating_value=rng.choices([1, 2, 3, 4, 5], [1, 1, 3, 5, 4])[0]))
        elif rng.random() < 0.6:
            rows.append(SurveyAnswer(response=response, question=q, answer_text=rng.choice(COMMENTS)))
    SurveyAnswer.objects.bulk_create(rows)
    recipient.status, recipient.opened_at, recipient.completed_at = "COMPLETED", when, when
    recipient.save(update_fields=["status", "opened_at", "completed_at"])


class Command(BaseCommand):
    help = "Create repeatable survey demo data (run after seed_data)."

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.environ.get("CRM_DEMO_PASSWORD")
        if not password:
            if not settings.DEBUG:
                raise CommandError("Set CRM_DEMO_PASSWORD before seeding accounts outside DEBUG mode.")
            password = "DemoPass!2026"  # local demo only
        rng = random.Random(2026)
        now = timezone.now()

        admin = Account.objects.filter(email="demo-admin@example.test").first()
        if admin is None:
            raise CommandError("Run `python manage.py seed_data` first (demo admin is missing).")
        group, _ = Group.objects.get_or_create(name=MANAGER_GROUP)
        manager = Account.objects.filter(email="demo-manager@example.test").first() \
            or Account.objects.create_user("demo-manager@example.test", password)
        manager.groups.add(group)

        customers = []
        for i in range(1, 25):
            account = Account.objects.filter(email=f"survey-customer-{i:02d}@example.test").first() \
                or Account.objects.create_user(f"survey-customer-{i:02d}@example.test", password)
            customer, created = Customer.objects.get_or_create(account=account, defaults={
                "full_name": f"Khách hàng mẫu {i:02d}",
                "date_of_birth": date.today() - timedelta(days=365 * rng.randint(16, 60)),
                "playing_level": LEVELS[i % 3]})
            if created:
                CustomerPreference.objects.get_or_create(customer=customer, preference_type="CATEGORY",
                                                         preference_value=PREFS[i % len(PREFS)])
            customers.append(customer)

        # 1) CLOSED, 24 completed
        s, new = Survey.objects.get_or_create(title="Hài lòng dịch vụ căng cước", defaults=dict(
            description="Giúp shop cải thiện dịch vụ căng cước vợt.", created_by=manager, status="CLOSED",
            start_at=now - timedelta(days=60), end_at=now - timedelta(days=30)))
        if new:
            make_questions(s, [
                ("Bạn thường căng cước vợt bao lâu một lần?", QT.SINGLE_CHOICE,
                 ["Mỗi tuần", "Mỗi tháng", "Vài tháng", "Khi đứt cước"], True),
                ("Bạn đánh giá tốc độ căng cước của shop?", QT.RATING, [], True),
                ("Bạn quan tâm yếu tố nào khi chọn dây cước?", QT.MULTI_CHOICE,
                 ["Độ bền", "Cảm giác đánh", "Giá", "Thương hiệu"], True),
                ("Góp ý thêm cho dịch vụ căng cước", QT.TEXT, [], False)])
            for c in customers:
                r = SurveyRecipient.objects.create(survey=s, customer=c, status="SENT")
                answer_all(r, rng, now - timedelta(days=rng.randint(31, 55)))

        # 2) ACTIVE, 8 of 20 answered
        s, new = Survey.objects.get_or_create(title="Mẫu vợt mới sắp về", defaults=dict(
            description="Bạn nghĩ gì về mẫu vợt sắp ra mắt?", created_by=manager, status="ACTIVE",
            start_at=now - timedelta(days=5), end_at=now + timedelta(days=25)))
        if new:
            make_questions(s, [
                ("Bạn có muốn mua mẫu vợt này không?", QT.SINGLE_CHOICE, ["Chắc chắn mua", "Có thể", "Không"], True),
                ("Mức giá nào bạn chấp nhận được?", QT.SINGLE_CHOICE,
                 ["Dưới 2 triệu", "2–3 triệu", "3–4 triệu", "Trên 4 triệu"], True),
                ("Bạn mong đợi điều gì ở mẫu vợt này?", QT.TEXT, [], False)])
            for i, c in enumerate(customers[:20]):
                r = SurveyRecipient.objects.create(survey=s, customer=c, status="SENT")
                if i < 8:
                    answer_all(r, rng, now - timedelta(days=rng.randint(0, 4)))

        # 3) DRAFT
        s, new = Survey.objects.get_or_create(title="Nên nhập giày hãng nào?", defaults=dict(
            description="Thăm dò nhu cầu giày cầu lông.", created_by=manager, status="DRAFT",
            start_at=now + timedelta(days=7), end_at=now + timedelta(days=37)))
        if new:
            make_questions(s, [("Bạn thích hãng giày nào?", QT.MULTI_CHOICE, ["Yonex", "Victor", "Li-Ning", "Mizuno"], True),
                               ("Bạn chơi mấy buổi mỗi tuần?", QT.RATING, [], False)])

        self.stdout.write(self.style.SUCCESS("Survey demo data ready (3 surveys, 24 demo customers)."))

"""TV5 tests: survey management, audience filter, multi-choice answers, statistics."""
from datetime import timedelta

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.errors import AccountPermissionDenied
from apps.accounts.models import Account
from apps.customers.models import Customer
from .constants import MANAGER_GROUP, QuestionType as QT, SurveyStatus
from .forms import QuestionForm
from .models import Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyRecipient
from .services import (build_stats, check_ready_to_send, close_expired, filter_customers, send_survey,
                       send_to_audience, submit_survey)

PW = "StrongPass!2026"


def make_customer(email, level=None, birth=None):
    account = Account.objects.create_user(email, PW)
    return Customer.objects.create(account=account, full_name=email.split("@")[0],
                                   playing_level=level, date_of_birth=birth)


class SurveyManageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Account.objects.create_superuser("admin@tv5.test", PW)
        cls.manager = Account.objects.create_user("manager@tv5.test", PW)
        cls.manager.groups.add(Group.objects.create(name=MANAGER_GROUP))
        cls.beginner = make_customer("beginner@tv5.test", "BEGINNER")
        cls.pro = make_customer("pro@tv5.test", "ADVANCED")
        now = timezone.now()
        cls.survey = Survey.objects.create(title="S", status=SurveyStatus.DRAFT, created_by=cls.admin,
                                           start_at=now, end_at=now + timedelta(days=5))
        cls.single = SurveyQuestion.objects.create(survey=cls.survey, question_text="Q1",
                                                   question_type=QT.SINGLE_CHOICE, is_required=True, sort_order=1)
        cls.yes = SurveyOption.objects.create(question=cls.single, option_text="Yes", sort_order=1)
        cls.no = SurveyOption.objects.create(question=cls.single, option_text="No", sort_order=2)
        cls.multi = SurveyQuestion.objects.create(survey=cls.survey, question_text="Q2",
                                                  question_type=QT.MULTI_CHOICE, sort_order=2)
        cls.m1 = SurveyOption.objects.create(question=cls.multi, option_text="A", sort_order=1)
        cls.m2 = SurveyOption.objects.create(question=cls.multi, option_text="B", sort_order=2)
        cls.rating = SurveyQuestion.objects.create(survey=cls.survey, question_text="Q3",
                                                   question_type=QT.RATING, sort_order=3)

    # --- access control ---
    def test_manager_and_admin_can_open_list_customer_cannot(self):
        url = reverse("surveys:manage_list")
        for user in (self.manager, self.admin):
            self.client.force_login(user)
            self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.beginner.account)
        self.assertNotEqual(self.client.get(url).status_code, 200)

    def test_service_rejects_plain_customer(self):
        with self.assertRaises(AccountPermissionDenied):
            send_survey(self.beginner.account, self.survey, [self.pro.pk])

    # --- create / draft rules ---
    def test_create_survey_as_draft(self):
        self.client.force_login(self.manager)
        start = (timezone.localtime() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        end = (timezone.localtime() + timedelta(days=9)).strftime("%Y-%m-%dT%H:%M")
        resp = self.client.post(reverse("surveys:manage_create"),
                                {"title": "New", "description": "", "start_at": start, "end_at": end})
        self.assertEqual(resp.status_code, 302)
        created = Survey.objects.get(title="New")
        self.assertEqual((created.status, created.created_by_id), (SurveyStatus.DRAFT, self.manager.pk))

    def test_cannot_edit_questions_after_survey_is_active(self):
        Survey.objects.filter(pk=self.survey.pk).update(status=SurveyStatus.ACTIVE)
        self.client.force_login(self.manager)
        resp = self.client.post(reverse("surveys:question_delete", args=[self.survey.pk, self.single.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(SurveyQuestion.objects.filter(pk=self.single.pk).exists())

    def test_choice_question_needs_two_distinct_options(self):
        form = QuestionForm({"question_text": "x", "question_type": QT.SINGLE_CHOICE,
                             "options_text": "Only\nOnly"})
        self.assertFalse(form.is_valid())
        ok = QuestionForm({"question_text": "x", "question_type": QT.TEXT, "options_text": ""})
        self.assertTrue(ok.is_valid())

    def test_question_move_renumbers(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("surveys:question_move", args=[self.survey.pk, self.multi.pk, "up"]))
        order = list(SurveyQuestion.objects.filter(survey=self.survey).order_by("sort_order")
                     .values_list("question_text", flat=True))
        self.assertEqual(order, ["Q2", "Q1", "Q3"])

    # --- audience + sending ---
    def test_filter_by_playing_level(self):
        ids = set(filter_customers("filter", playing_levels=["BEGINNER"]).values_list("pk", flat=True))
        self.assertEqual(ids, {self.beginner.pk})
        self.assertEqual(filter_customers("all").count(), 2)

    def test_send_opens_survey_and_skips_duplicates(self):
        self.assertEqual(check_ready_to_send(self.survey), [])
        first = send_to_audience(self.admin, self.survey, filter_customers("all"))
        self.assertEqual(first, {"created": 2, "skipped": 0})
        self.survey.refresh_from_db()
        self.assertEqual(self.survey.status, SurveyStatus.ACTIVE)
        again = send_to_audience(self.manager, self.survey, filter_customers("all"))
        self.assertEqual(again, {"created": 0, "skipped": 2})

    def test_not_ready_without_questions_or_with_one_option(self):
        empty = Survey.objects.create(title="E", status="DRAFT", created_by=self.admin,
                                      end_at=timezone.now() + timedelta(days=1))
        self.assertTrue(check_ready_to_send(empty))
        SurveyOption.objects.filter(pk=self.no.pk).delete()
        self.assertTrue(any("2 lựa chọn" in e for e in check_ready_to_send(self.survey)))

    def test_close_expired(self):
        Survey.objects.filter(pk=self.survey.pk).update(status="ACTIVE", end_at=timezone.now() - timedelta(hours=1))
        close_expired()
        self.survey.refresh_from_db()
        self.assertEqual(self.survey.status, SurveyStatus.CLOSED)

    # --- answering + stats ---
    def _open_and_send(self):
        Survey.objects.filter(pk=self.survey.pk).update(status="ACTIVE")
        send_survey(self.admin, self.survey, [self.beginner.pk, self.pro.pk])
        return (SurveyRecipient.objects.get(survey=self.survey, customer=self.beginner),
                SurveyRecipient.objects.get(survey=self.survey, customer=self.pro))

    def test_multi_choice_and_rating_answers_are_saved(self):
        r1, _ = self._open_and_send()
        ok = submit_survey(self.beginner.account, r1.pk, [
            {"question_id": self.single.pk, "option_id": self.yes.pk},
            {"question_id": self.multi.pk, "option_id": self.m1.pk},
            {"question_id": self.multi.pk, "option_id": self.m2.pk},
            {"question_id": self.rating.pk, "rating_value": 4}])
        self.assertTrue(ok)
        self.assertEqual(SurveyAnswer.objects.filter(question=self.multi).count(), 2)

    def test_single_choice_cannot_have_two_answers_and_rating_range(self):
        r1, _ = self._open_and_send()
        with self.assertRaises(ValidationError):
            submit_survey(self.beginner.account, r1.pk, [
                {"question_id": self.single.pk, "option_id": self.yes.pk},
                {"question_id": self.single.pk, "option_id": self.no.pk}])
        with self.assertRaises(ValidationError):
            submit_survey(self.beginner.account, r1.pk, [
                {"question_id": self.single.pk, "option_id": self.yes.pk},
                {"question_id": self.rating.pk, "rating_value": 9}])
        self.assertEqual(SurveyAnswer.objects.count(), 0)

    def test_stats_counts_and_rate(self):
        r1, r2 = self._open_and_send()
        submit_survey(self.beginner.account, r1.pk, [
            {"question_id": self.single.pk, "option_id": self.yes.pk},
            {"question_id": self.rating.pk, "rating_value": 5}])
        submit_survey(self.pro.account, r2.pk, [
            {"question_id": self.single.pk, "option_id": self.yes.pk},
            {"question_id": self.rating.pk, "rating_value": 3}])
        stats = build_stats(self.survey)
        self.assertEqual((stats["sent"], stats["done"], stats["rate"]), (2, 2, 100.0))
        by_text = {i["question"].question_text: i for i in stats["items"]}
        self.assertEqual(by_text["Q1"]["rows"][0]["n"], 2)
        self.assertEqual(by_text["Q3"]["avg"], 4.0)

    def test_my_surveys_groups_by_state(self):
        r1, _ = self._open_and_send()
        self.client.force_login(self.beginner.account)
        resp = self.client.get(reverse("surveys:my_surveys"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([r.pk for r in resp.context["todo"]], [r1.pk])

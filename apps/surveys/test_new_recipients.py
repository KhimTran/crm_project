from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone

from apps.accounts.errors import AccountPermissionDenied
from apps.accounts.models import Account
from apps.accounts.testing import PortalTestCase
from .models import Survey, SurveyAnswer, SurveyQuestion, SurveyRecipient, SurveyResponse
from .services import new_recipient_customers, send_saved_survey, submit_survey

PW = "StrongPass!2026"
EMPTY_MESSAGE = "No new eligible customers in the saved audience to invite."


def make_survey(manager, audience=None):
    survey = Survey.objects.create(
        title="New recipients", status="DRAFT", created_by=manager,
        start_at=timezone.now() - timedelta(minutes=1), end_at=timezone.now() + timedelta(days=7),
        audience=audience or {"audience": "filter", "playing_levels": ["BEGINNER"]})
    SurveyQuestion.objects.create(survey=survey, question_text="Comment", question_type="TEXT", is_required=True)
    return survey


class NewRecipientTests(PortalTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@new.test", PW, role="MANAGER")
        cls.first = Account.objects.create_user("first@new.test", PW, playing_level="BEGINNER")
        cls.outside = Account.objects.create_user("outside@new.test", PW, playing_level="COMPETITIVE")

    def setUp(self):
        # Exercise the production login path, without fixture cookie mirroring.
        self.assertEqual(self.client.post("/manager/login/", {
            "email": self.manager.email, "password": PW}).status_code, 302)
        self.survey = make_survey(self.manager)
        self.detail = reverse("surveys:manage_detail", args=[self.survey.pk])
        self.send = reverse("surveys:manage_send", args=[self.survey.pk])

    def new_customer(self, email="new@new.test", **fields):
        return Account.objects.create_user(email, PW, playing_level="BEGINNER", **fields)

    def publish(self):
        self.assertEqual(send_saved_survey(self.manager, self.survey)["created"], 1)

    def test_draft_first_send_publishes_and_hides_supplemental_action(self):
        self.assertContains(self.client.get(self.detail), "Publish Survey")
        page = self.client.get(self.send)
        self.assertContains(page, "Confirm Publish Survey")
        self.assertNotContains(page, "Confirm Send to New Recipients")
        self.assertEqual(page.context["preview"], 1)
        self.assertEqual(self.client.post(self.send, {"action": "send"}).status_code, 302)
        self.survey.refresh_from_db()
        self.assertEqual(self.survey.status, "ACTIVE")
        self.assertEqual(list(SurveyRecipient.objects.values_list("customer_id", flat=True)), [self.first.pk])
        page = self.client.get(self.detail)
        self.assertFalse(page.context["can_send_new"])
        self.assertNotContains(page, "Send to New Recipients")
        self.assertContains(self.client.get(self.send), EMPTY_MESSAGE)

    def test_new_matching_customer_enables_action_and_counts_only_uninvited(self):
        self.publish()
        new = self.new_customer()
        self.new_customer("locked@new.test", status="LOCKED")
        page = self.client.get(self.detail)
        self.assertTrue(page.context["can_send_new"])
        self.assertContains(page, "Send to New Recipients")
        page = self.client.get(self.send)
        self.assertEqual(page.context["preview"], 1)
        self.assertContains(page, "Only eligible customers in the saved audience who have not received this survey will be invited.")
        self.assertContains(page, "Confirm Send to New Recipients")
        for field in ("audience", "customer_ids", "playing_levels", "preview"):
            self.assertNotContains(page, f'name="{field}"')
        with self.assertNumQueries(1):
            self.assertEqual(new_recipient_customers(self.survey).count(), 1)
        self.client.post(self.send, {"action": "send", "audience": "pick", "customer_ids": [self.outside.pk]})
        self.assertEqual(set(SurveyRecipient.objects.values_list("customer_id", flat=True)), {self.first.pk, new.pk})
        self.assertNotContains(self.client.get(self.detail), "Send to New Recipients")

    def test_completed_invitation_and_answer_unchanged_on_additional_and_repeat_send(self):
        self.publish()
        recipient = SurveyRecipient.objects.get(survey=self.survey, customer=self.first)
        question = SurveyQuestion.objects.get(survey=self.survey)
        submit_survey(self.first, recipient.pk, [{"question_id": question.pk, "answer_text": "Keep my answer"}])
        before = (list(SurveyRecipient.objects.filter(pk=recipient.pk).values()),
                  list(SurveyResponse.objects.values()), list(SurveyAnswer.objects.values()))
        self.new_customer()
        self.client.post(self.send, {"action": "send"})
        repeated = self.client.post(self.send, {"action": "send"}, follow=True)
        self.assertContains(repeated, EMPTY_MESSAGE)
        self.assertEqual(SurveyRecipient.objects.count(), 2)
        self.assertEqual(before, (list(SurveyRecipient.objects.filter(pk=recipient.pk).values()),
                                 list(SurveyResponse.objects.values()), list(SurveyAnswer.objects.values())))

    def test_post_rechecks_lock_role_and_saved_audience_membership(self):
        self.publish()
        locked = self.new_customer("will-lock@new.test")
        changed = self.new_customer("will-change@new.test")
        promoted = self.new_customer("will-promote@new.test")
        remaining = self.new_customer("remaining@new.test")
        self.assertEqual(self.client.get(self.send).context["preview"], 4)
        Account.objects.filter(pk=locked.pk).update(status="LOCKED")
        Account.objects.filter(pk=changed.pk).update(playing_level="COMPETITIVE")
        Account.objects.filter(pk=promoted.pk).update(role="MANAGER")
        self.client.post(self.send, {"action": "send", "preview": 4})
        self.assertEqual(set(SurveyRecipient.objects.values_list("customer_id", flat=True)), {self.first.pk, remaining.pk})

    def test_no_new_customers_at_post_is_clear_and_creates_nothing(self):
        self.publish()
        new = self.new_customer()
        self.assertEqual(self.client.get(self.send).context["preview"], 1)
        Account.objects.filter(pk=new.pk).update(status="LOCKED")
        self.assertContains(self.client.post(self.send, {"action": "send"}, follow=True), EMPTY_MESSAGE)
        self.assertEqual(SurveyRecipient.objects.count(), 1)

    def test_closed_and_expired_direct_urls_cannot_send(self):
        self.publish()
        self.new_customer()
        for state, end in [("CLOSED", timezone.now() + timedelta(days=1)),
                           ("ACTIVE", timezone.now() - timedelta(minutes=1))]:
            with self.subTest(state=state):
                Survey.objects.filter(pk=self.survey.pk).update(status=state, end_at=end)
                for method in (self.client.get, self.client.post):
                    page = method(self.send, {"action": "send"})
                    self.assertTrue(page.context["errors"])
                    self.assertContains(page, "disabled")
                self.assertNotContains(self.client.get(self.detail), "Send to New Recipients")
                self.assertEqual(SurveyRecipient.objects.count(), 1)
                with self.assertRaises(ValidationError):
                    send_saved_survey(self.manager, self.survey)

    def test_customer_anonymous_and_locked_manager_cannot_send(self):
        for actor in (None, self.first, self.manager):
            with self.subTest(actor=actor):
                self.client.logout()
                if actor:
                    self.client.force_login(actor)
                if actor == self.manager:
                    Account.objects.filter(pk=actor.pk).update(status="LOCKED")
                for method in (self.client.get, self.client.post):
                    self.assertIn(method(self.send, {"action": "send"}).status_code, (302, 403))
                with self.assertRaises(AccountPermissionDenied):
                    send_saved_survey(actor, self.survey)
                self.assertFalse(SurveyRecipient.objects.exists())


class ConcurrentNewRecipientTests(TransactionTestCase):
    @skipUnlessDBFeature("has_select_for_update")
    def test_two_simultaneous_sends_create_one_invitation(self):
        manager = Account.objects.create_user("parallel-manager@new.test", PW, role="MANAGER")
        customer = Account.objects.create_user("parallel-customer@new.test", PW, playing_level="BEGINNER")
        survey = make_survey(manager)
        Survey.objects.filter(pk=survey.pk).update(status="ACTIVE")
        barrier = Barrier(2)

        def send():
            close_old_connections()
            try:
                actor = Account.objects.get(pk=manager.pk)
                current = Survey.objects.get(pk=survey.pk)
                barrier.wait(timeout=10)
                return send_saved_survey(actor, current)["created"]
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(lambda _: send(), range(2))), [0, 1])
        self.assertEqual(SurveyRecipient.objects.filter(survey=survey, customer=customer).count(), 1)

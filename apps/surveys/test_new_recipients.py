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
from .services import send_saved_survey, send_saved_surveys, submit_survey

PW = "StrongPass!2026"


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
        # Real login keeps production portal cookie isolation.
        self.assertEqual(self.client.post("/manager/login/", {
            "email": self.manager.email, "password": PW}).status_code, 302)
        self.survey = make_survey(self.manager)
        self.detail = reverse("surveys:manage_detail", args=[self.survey.pk])
        self.audience = reverse("surveys:manage_send", args=[self.survey.pk])
        self.send = reverse("surveys:manage_bulk_send")
        self.list_url = reverse("surveys:manage_list")

    def new_customer(self, email="new@new.test", **fields):
        return Account.objects.create_user(email, PW, playing_level="BEGINNER", **fields)

    def publish(self):
        self.assertEqual(send_saved_survey(self.manager, self.survey)["created"], 1)

    def post_send(self, ids=None, **fields):
        return self.client.post(self.send, {"survey_ids": ids or [self.survey.pk], **fields}, follow=True)

    def test_draft_publish_still_uses_audience_page(self):
        self.assertContains(self.client.get(self.detail), "Publish Survey")
        page = self.client.get(self.audience)
        self.assertContains(page, "Confirm Publish Survey")
        self.assertEqual(page.context["preview"], 1)
        self.assertEqual(self.client.post(self.audience, {"action": "send"}).status_code, 302)
        self.survey.refresh_from_db()
        self.assertEqual(self.survey.status, "ACTIVE")
        self.assertEqual(list(SurveyRecipient.objects.values_list("customer_id", flat=True)), [self.first.pk])

    def test_list_selection_is_based_on_readiness_not_new_recipient_count(self):
        self.assertFalse(self.client.get(self.list_url).context["items"][0].sendable)
        self.publish()
        page = self.client.get(self.list_url)
        self.assertTrue(page.context["items"][0].sendable)
        self.assertContains(page, 'id="survey-select-all"')
        self.assertContains(page, 'id="survey-send" class="btn btn-primary" type="submit" disabled')
        self.assertContains(page, 'form="survey-bulk-send"')
        self.assertContains(page, 'js/survey_list.js')
        self.assertNotContains(self.client.get(self.detail), "Send to New Recipients")

    def test_supplemental_audience_urls_redirect_without_sending(self):
        self.publish()
        self.new_customer()
        for method in (self.client.get, self.client.post):
            self.assertRedirects(method(self.audience, {"action": "send"}), self.list_url)
        self.assertEqual(SurveyRecipient.objects.count(), 1)
        self.assertNotContains(self.client.get(self.detail), self.audience)

    def test_multiple_surveys_use_their_own_saved_audiences_and_deduplicate_ids(self):
        self.publish()
        second = make_survey(self.manager, {"audience": "pick", "customer_ids": [self.outside.pk]})
        send_saved_survey(self.manager, second)
        new = self.new_customer()
        page = self.post_send([second.pk, self.survey.pk, second.pk], audience="all",
                              customer_ids=[self.outside.pk])
        self.assertContains(page, "Successfully processed 2 survey(s). Sent to 1 new recipient(s).")
        self.assertEqual(set(SurveyRecipient.objects.filter(survey=self.survey).values_list("customer_id", flat=True)),
                         {self.first.pk, new.pk})
        self.assertEqual(list(SurveyRecipient.objects.filter(survey=second).values_list("customer_id", flat=True)),
                         [self.outside.pk])

    def test_all_audience_includes_new_customer(self):
        self.survey.audience = {"audience": "all"}
        self.survey.save(update_fields=["audience"])
        send_saved_survey(self.manager, self.survey)
        new = self.new_customer()
        self.post_send()
        self.assertTrue(SurveyRecipient.objects.filter(survey=self.survey, customer=new).exists())
        self.assertEqual(SurveyRecipient.objects.count(), 3)

    def test_admin_and_crm_manager_keep_existing_send_permissions(self):
        from django.contrib.auth.models import Group
        self.publish()
        admin = Account.objects.create_superuser("admin@new.test", PW)
        grouped = Account.objects.create_user("grouped@new.test", PW)
        grouped.groups.add(Group.objects.create(name="CRM_MANAGER"))
        for actor in (admin, grouped):
            with self.subTest(role=actor.role_code):
                self.client.force_login(actor)
                self.assertContains(self.post_send(), "Successfully processed 1 survey(s).")

    def test_answers_and_all_invitation_states_survive_repeat_send(self):
        self.publish()
        recipient = SurveyRecipient.objects.get(survey=self.survey, customer=self.first)
        question = SurveyQuestion.objects.get(survey=self.survey)
        submit_survey(self.first, recipient.pk, [{"question_id": question.pk, "answer_text": "Keep my answer"}])
        for index, state in enumerate(("SENT", "OPENED", "OTHER")):
            customer = self.new_customer(f"state{index}@new.test")
            SurveyRecipient.objects.create(survey=self.survey, customer=customer, status=state)
        before = (list(SurveyRecipient.objects.order_by("pk").values()),
                  list(SurveyResponse.objects.values()), list(SurveyAnswer.objects.values()))
        for _ in range(2):
            page = self.post_send()
            self.assertContains(page, "Successfully processed 1 survey(s). Sent to 0 new recipient(s).")
            self.assertEqual(before, (list(SurveyRecipient.objects.order_by("pk").values()),
                                     list(SurveyResponse.objects.values()), list(SurveyAnswer.objects.values())))
        new = self.new_customer()
        self.post_send()
        self.assertTrue(SurveyRecipient.objects.filter(customer=new, survey=self.survey).exists())
        self.assertEqual(before[0], list(SurveyRecipient.objects.exclude(customer=new).order_by("pk").values()))
        self.assertEqual(before[1:], (list(SurveyResponse.objects.values()), list(SurveyAnswer.objects.values())))

    def test_post_rechecks_lock_role_and_saved_audience_membership(self):
        self.publish()
        locked = self.new_customer("will-lock@new.test")
        changed = self.new_customer("will-change@new.test")
        promoted = self.new_customer("will-promote@new.test")
        remaining = self.new_customer("remaining@new.test")
        self.client.get(self.list_url)
        Account.objects.filter(pk=locked.pk).update(status="LOCKED")
        Account.objects.filter(pk=changed.pk).update(playing_level="COMPETITIVE")
        Account.objects.filter(pk=promoted.pk).update(role="MANAGER")
        self.post_send(preview=4)
        self.assertEqual(set(SurveyRecipient.objects.values_list("customer_id", flat=True)), {self.first.pk, remaining.pk})

    def test_invalid_selection_is_atomic_and_not_selectable(self):
        self.publish()
        new = self.new_customer()
        invalid = make_survey(self.manager)
        cases = [{"status": "DRAFT"}, {"status": "CLOSED"}, {"status": "UNKNOWN"},
                 {"status": "ACTIVE", "end_at": timezone.now() - timedelta(minutes=1)},
                 {"status": "ACTIVE", "end_at": timezone.now() + timedelta(days=1), "audience": {}}]
        for fields in cases:
            with self.subTest(fields=fields):
                Survey.objects.filter(pk=invalid.pk).update(**fields)
                page = self.post_send([self.survey.pk, invalid.pk])
                self.assertNotContains(page, "Successfully processed")
                self.assertFalse(SurveyRecipient.objects.filter(customer=new).exists())
                self.assertFalse(next(item for item in page.context["items"] if item.pk == invalid.pk).sendable)
        Survey.objects.filter(pk=invalid.pk).update(audience={"audience": "all"})
        SurveyQuestion.objects.filter(survey=invalid).delete()
        self.assertNotContains(self.post_send([self.survey.pk, invalid.pk]), "Successfully processed")
        self.assertFalse(SurveyRecipient.objects.filter(customer=new).exists())

    def test_empty_invalid_and_missing_ids_cannot_send(self):
        self.publish()
        self.new_customer()
        for ids in ([], ["bad"], ["-1"], ["0"], ["1" * 100], ["2147483648"], [999999, self.survey.pk]):
            with self.subTest(ids=ids):
                page = self.client.post(self.send, {"survey_ids": ids}, follow=True)
                self.assertNotContains(page, "Successfully processed")
                self.assertEqual(SurveyRecipient.objects.count(), 1)

    def test_no_eligible_customers_is_success_for_published_survey(self):
        self.publish()
        Account.objects.filter(pk=self.first.pk).update(status="LOCKED")
        self.assertContains(self.post_send(), "Successfully processed 1 survey(s). Sent to 0 new recipient(s).")

    def test_customer_anonymous_locked_and_revoked_manager_cannot_send(self):
        self.publish()
        self.new_customer()
        for actor in (None, self.first, self.manager):
            with self.subTest(actor=actor):
                self.client.logout()
                if actor:
                    self.client.force_login(actor)
                if actor == self.manager:
                    Account.objects.filter(pk=actor.pk).update(status="LOCKED")
                self.assertIn(self.client.post(self.send, {"survey_ids": [self.survey.pk]}).status_code, (302, 403))
                with self.assertRaises(AccountPermissionDenied):
                    send_saved_surveys(actor, [self.survey.pk])
                self.assertEqual(SurveyRecipient.objects.count(), 1)
        Account.objects.filter(pk=self.manager.pk).update(status="ACTIVE", role="MANAGER")
        self.client.force_login(self.manager)
        Account.objects.filter(pk=self.manager.pk).update(role="CUSTOMER")
        self.client.post(self.send, {"survey_ids": [self.survey.pk]})
        self.assertEqual(SurveyRecipient.objects.count(), 1)

    def test_post_only_csrf_and_filter_preservation(self):
        from apps.accounts.testing import PortalClient
        self.assertEqual(self.client.get(self.send).status_code, 405)
        client = PortalClient(enforce_csrf_checks=True)
        client.force_login(self.manager)
        self.assertEqual(client.post(self.send, {"survey_ids": [self.survey.pk]}).status_code, 403)
        self.publish()
        client.get(self.list_url)
        response = client.post(self.send, {"survey_ids": [self.survey.pk], "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
                                          "q": "New", "status": "ACTIVE", "page": "1"})
        self.assertRedirects(response, self.list_url + "?q=New&status=ACTIVE")


class ConcurrentNewRecipientTests(TransactionTestCase):
    def setUp(self):
        from django.core.management import call_command
        call_command('initialize_roles', verbosity=0)

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
                return send_saved_surveys(actor, [current.pk])["created"]
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(lambda _: send(), range(2))), [0, 1])
        self.assertEqual(SurveyRecipient.objects.filter(survey=survey, customer=customer).count(), 1)

    @skipUnlessDBFeature("has_select_for_update")
    def test_overlapping_batches_in_reverse_order_do_not_duplicate(self):
        manager = Account.objects.create_user("batch-manager@new.test", PW, role="MANAGER")
        customer = Account.objects.create_user("batch-customer@new.test", PW, playing_level="BEGINNER")
        surveys = [make_survey(manager), make_survey(manager)]
        ids = [survey.pk for survey in surveys]
        Survey.objects.filter(pk__in=ids).update(status="ACTIVE")
        barrier = Barrier(2)

        def send(index):
            close_old_connections()
            try:
                actor = Account.objects.get(pk=manager.pk)
                barrier.wait(timeout=10)
                return send_saved_surveys(actor, ids if index else ids[::-1])["created"]
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(send, range(2))), [0, 2])
        self.assertEqual(SurveyRecipient.objects.filter(survey_id__in=ids, customer=customer).count(), 2)


from django.test import SimpleTestCase


class SavedAudienceDisplayTests(SimpleTestCase):
    def test_all_and_missing_audience_are_explicit(self):
        from types import SimpleNamespace
        from .views import saved_audience_details
        self.assertEqual(saved_audience_details(SimpleNamespace(audience={"audience": "all"}))["label"], "All customers")
        self.assertEqual(saved_audience_details(SimpleNamespace(audience={}))["label"], "Audience not configured")

    def test_group_displays_each_saved_rule(self):
        from types import SimpleNamespace
        from .views import saved_audience_details
        result = saved_audience_details(SimpleNamespace(audience={"audience": "filter", "age_groups": ["18_24"],
                                       "playing_levels": ["BEGINNER"], "preferences": ["Yonex"]}))
        self.assertEqual(result["label"], "Customer group")
        self.assertEqual(len(result["rules"]), 3)
        self.assertIn("18–24", result["rules"][0])
        self.assertIn("Yonex", result["rules"][2])

    def test_specific_customers_include_names_and_missing_accounts(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from .views import saved_audience_details
        with patch("apps.accounts.models.Account.objects.filter", return_value=[SimpleNamespace(pk=4, full_name="Alex", email="alex@example.test")]):
            result = saved_audience_details(SimpleNamespace(audience={"audience": "pick", "customer_ids": [4, 8, 4]}))
        self.assertEqual(len(result["customers"]), 2)
        self.assertIn("Alex", result["customers"][0])
        self.assertIn("no longer available", result["customers"][1])

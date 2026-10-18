"""Customer Report survey metrics (apps.surveys.survey_report)."""
import json
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.customers.models import Customer
from .configuration import populate_questionnaire
from .models import Survey, SurveyAnswer, SurveyQuestion, SurveyRecipient, SurveyResponse
from .questionnaire import NOT_USED
from .survey_report import build_report, compute_nps, round_half_up

NOW = timezone.make_aware(datetime(2026, 10, 15, 12, 0))
PASSWORD = "ReportFixture!2026"


# tv4: tạo tài khoản nhóm CRM_MANAGER cho test
def crm_manager(email):
    """CRM_MANAGER group user: opens the Vietnamese CRM layout (MANAGER role gets the English portal)."""
    account = Account.objects.create_user(email, PASSWORD)
    account.groups.add(Group.objects.get_or_create(name="CRM_MANAGER")[0])
    return account


# tv4: test tính số liệu báo cáo khảo sát
class SurveyReportTests(TestCase):
    # tv4: dữ liệu dùng chung: quản lý và khách
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@report.test", PASSWORD, role="MANAGER")
        cls.crm_manager = crm_manager("crm-manager@report.test")
        cls.customers = [Customer.objects.create(
            account=Account.objects.create_user(f"c{i}@report.test", PASSWORD), full_name=f"Khách {i}")
            for i in range(10)]

    # tv4: tạo khảo sát bộ 8 câu cho mỗi test
    def setUp(self):
        self.survey = self.make_survey("Bộ 8 câu")
        self.used = 0

    # tv4: tạo khảo sát bộ 8 câu đang mở
    def make_survey(self, title):
        survey = Survey.objects.create(title=title, status="DRAFT", created_by=self.manager,
                                       start_at=NOW - timedelta(days=200), end_at=NOW + timedelta(days=30))
        populate_questionnaire(survey)
        Survey.objects.filter(pk=survey.pk).update(status="ACTIVE")
        return survey

    # tv4: câu hỏi theo key
    def questions(self, survey):
        return {q.config["key"]: q for q in survey.surveyquestion_set.all()}

    # tv4: lưu 1 phản hồi đã nộp với câu trả lời cho trước
    def respond(self, when=NOW, survey=None, customer=None, purchases=(0,), segment=0, csat=5, criteria=(5, 5, 5, 5),
                brands=(0,), other_text="", nps=10, comment=""):
        """Store one submitted response; choice arguments are 0-based option positions."""
        survey = survey or self.survey
        customer = customer or self.customers[self.used]
        self.used += 1
        recipient = SurveyRecipient.objects.create(survey=survey, customer=customer, status="COMPLETED",
                                                   completed_at=when)
        response = SurveyResponse.objects.create(recipient=recipient, status="SUBMITTED", started_at=when,
                                                 submitted_at=when)
        q = self.questions(survey)
        options = {k: list(v.surveyoption_set.order_by("sort_order")) for k, v in q.items()}
        rows = [SurveyAnswer(response=response, question=q["purchases"], option=options["purchases"][i]) for i in purchases]
        rows.append(SurveyAnswer(response=response, question=q["playing_frequency"], option=options["playing_frequency"][segment]))
        if csat is not None:
            rows.append(SurveyAnswer(response=response, question=q["overall_satisfaction"], rating_value=csat))
        for option, value in zip(options["service_criteria"], criteria):
            if value == NOT_USED:
                rows.append(SurveyAnswer(response=response, question=q["service_criteria"], option=option, answer_text=NOT_USED))
            elif value is not None:
                rows.append(SurveyAnswer(response=response, question=q["service_criteria"], option=option, rating_value=value))
        for i in brands:
            option = options["future_brands"][i]
            text = other_text if option.pk == q["future_brands"].config["other_option_id"] else None
            rows.append(SurveyAnswer(response=response, question=q["future_brands"], option=option, answer_text=text))
        if nps is not None:
            rows.append(SurveyAnswer(response=response, question=q["recommendation"], rating_value=nps))
        if comment:
            rows.append(SurveyAnswer(response=response, question=q["suggestions"], answer_text=comment))
        SurveyAnswer.objects.bulk_create(rows)
        return response

    # ── NPS ───────────────────────────────────────────────────────────
    # tv4: test NPS ca biên 9, 8, 7, 6 và làm tròn
    def test_nps_boundaries_9_8_7_6(self):
        result = compute_nps([9, 8, 7, 6])
        self.assertEqual((result["promoters"], result["passives"], result["detractors"]), (1, 2, 1))
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["level"], "good")
        self.assertEqual(compute_nps([9])["score"], 100)
        self.assertEqual(compute_nps([8])["score"], 0)
        self.assertEqual(compute_nps([7])["score"], 0)
        self.assertEqual(compute_nps([6])["score"], -100)
        self.assertEqual(compute_nps([6])["level"], "poor")
        self.assertEqual(compute_nps([9, 7])["level"], "excellent")  # exactly 50
        self.assertEqual(compute_nps([10, 9, 6])["score"], 33)
        # 12.5 and -12.5 round half away from zero, within -100..100.
        self.assertEqual(compute_nps([9] + [7] * 7)["score"], 13)
        self.assertEqual(compute_nps([6] + [7] * 7)["score"], -13)
        self.assertEqual(compute_nps([0, 11, 9])["respondents"], 1)  # out-of-range scores ignored
        self.assertIsNone(compute_nps([])["score"])
        self.assertIsNone(compute_nps([])["level"])
        self.assertEqual(round_half_up(4.65, 1), 4.7)

    # tv4: test NPS từ câu trả lời đã lưu
    def test_nps_from_stored_answers(self):
        for score in (9, 8, 7, 6):
            self.respond(nps=score)
        nps = build_report(now=NOW)["nps"]
        self.assertEqual((nps["score"], nps["respondents"]), (0, 4))
        self.assertEqual([d["n"] for d in nps["distribution"]], [0, 0, 0, 0, 0, 1, 1, 1, 1, 0])

    # ── multiple choice ─────────────────────────────────────────────────
    # tv4: test câu 1 nhiều lựa chọn, sắp giảm dần
    def test_purchases_use_respondents_and_are_sorted(self):
        self.respond(purchases=(0, 4))
        self.respond(purchases=(0,))
        self.respond(purchases=(1, 4))
        rows = build_report(now=NOW)["purchases"]
        self.assertEqual(rows["respondents"], 3)
        self.assertEqual([(r["label"], r["n"], r["pct"]) for r in rows["rows"]],
                         [("Vợt cầu lông", 2, 66.7), ("Đan / căng cước", 2, 66.7), ("Giày cầu lông", 1, 33.3)])

    # tv4: test donut câu 6 và lát Khác
    def test_brands_donut_shares_other_slice_and_respondent_pct(self):
        self.respond(brands=(0, 1, 5), other_text="Kumpoo nội địa")
        self.respond(brands=(0,))
        self.respond(brands=(5,), other_text="  Apacs ")
        brands = build_report(now=NOW)["brands"]
        self.assertEqual((brands["respondents"], brands["selections"]), (3, 5))
        rows = {r["label"]: r for r in brands["rows"]}
        self.assertEqual((rows["Yonex"]["share_pct"], rows["Yonex"]["respondent_pct"]), (40.0, 66.7))
        self.assertEqual((rows["Khác"]["share_pct"], rows["Khác"]["respondent_pct"]), (40.0, 66.7))
        self.assertTrue(brands["rows"][-1]["is_other"])
        self.assertEqual(sum(1 for r in brands["rows"] if r["is_other"]), 1)
        self.assertEqual(sorted(o["text"] for o in brands["other_texts"]), ["Apacs", "Kumpoo nội địa"])
        self.assertAlmostEqual(sum(r["share_pct"] for r in brands["rows"]), 100.0)

    # tv4: test phân khúc phổ biến câu 2
    def test_segment_is_most_chosen_question_2_option(self):
        for segment in (1, 1, 0):
            self.respond(segment=segment)
        segment = build_report(now=NOW)["segment"]
        self.assertEqual((segment["label"], segment["n"], segment["pct"], segment["respondents"]),
                         ("Khách chơi phong trào", 2, 66.7, 3))

    # ── question 4 matrix ───────────────────────────────────────────────
    # tv4: test câu 4 loại Không sử dụng
    def test_matrix_excludes_not_used_and_unanswered(self):
        self.respond(criteria=(5, NOT_USED, 4, 2))
        self.respond(criteria=(3, 4, NOT_USED, None))
        criteria = build_report(now=NOW)["criteria"]
        self.assertEqual([c["label"] for c in criteria], ["Sản phẩm", "Tư vấn", "Dịch vụ đan vợt", "Giá cả"])
        self.assertEqual([(c["avg"], c["scored"], c["not_used"], c["unanswered"]) for c in criteria],
                         [(4.0, 2, 0, 0), (4.0, 1, 1, 0), (4.0, 1, 1, 0), (2.0, 1, 0, 1)])

    # ── empty data and month comparison ─────────────────────────────────
    # tv4: test không có dữ liệu
    def test_no_data_returns_none_not_zero_division(self):
        report = build_report(now=NOW)
        self.assertEqual(report["total"]["count"], 0)
        self.assertIsNone(report["total"]["pct"])
        self.assertIsNone(report["csat"]["avg"])
        self.assertIsNone(report["nps"]["score"])
        self.assertIsNone(report["segment"])
        self.assertEqual(report["purchases"]["rows"], [])
        self.assertEqual(report["brands"]["rows"], [])
        self.assertEqual(report["comments"], [])
        self.assertTrue(all(m["avg"] is None for m in report["csat_trend"]))
        self.client.force_login(self.crm_manager)
        response = self.client.get(reverse("surveys:results"))
        self.assertContains(response, "Chưa có dữ liệu so sánh")
        self.assertContains(response, "Chưa có dữ liệu")
        self.assertNotContains(response, "NaN")
        self.assertNotContains(response, "None")
        self.client.force_login(self.manager)  # Manager Portal renders the English labels
        response = self.client.get(reverse("surveys:results"))
        self.assertContains(response, "No comparison data")
        self.assertNotContains(response, "NaN")

    # tv4: test tháng trước = 0
    def test_previous_month_zero_shows_no_comparison(self):
        self.respond(when=NOW)
        total = build_report(now=NOW)["total"]
        self.assertEqual((total["count"], total["this_month"], total["last_month"]), (1, 1, 0))
        self.assertIsNone(total["pct"])
        self.assertIsNone(total["direction"])

    # tv4: test tăng/giảm so với tháng trước
    def test_month_change_up_down_and_flat(self):
        last = NOW - timedelta(days=30)
        for when in (last, last, NOW, NOW, NOW):
            self.respond(when=when)
        self.assertEqual((build_report(now=NOW)["total"]["pct"], build_report(now=NOW)["total"]["direction"]), (50, "up"))
        later = NOW + timedelta(days=31)  # November: 0 this month vs 3 in October
        self.assertEqual((build_report(now=later)["total"]["pct"], build_report(now=later)["total"]["direction"]), (100, "down"))

    # tv4: test CSAT theo tháng bỏ trống tháng không có dữ liệu
    def test_csat_trend_leaves_empty_months_blank(self):
        self.respond(when=NOW, csat=5)
        self.respond(when=NOW, csat=4)
        self.respond(when=NOW - timedelta(days=92), csat=3)
        self.respond(when=NOW - timedelta(days=400), csat=1)  # outside 6 months, still in overall CSAT
        report = build_report(now=NOW)
        trend = report["csat_trend"]
        self.assertEqual([m["label"] for m in trend], ["05/2026", "06/2026", "07/2026", "08/2026", "09/2026", "10/2026"])
        self.assertEqual([m["avg"] for m in trend], [None, None, 3.0, None, None, 4.5])
        self.assertEqual(report["csat"]["avg"], 3.3)
        self.assertEqual(report["csat"]["stars"], "★★★☆☆")

    # ── comments ────────────────────────────────────────────────────────
    # tv4: test bảng ý kiến, tag và khách ẩn danh
    def test_comments_tags_order_and_anonymous_customer(self):
        self.respond(when=NOW - timedelta(days=2), csat=5, purchases=(0, 4), comment="Căng vợt chuẩn kg")
        self.respond(when=NOW - timedelta(days=1), csat=3, purchases=(1,), comment="   ")
        deleted = self.respond(when=NOW, csat=2, purchases=(3,), comment="x" * 200)
        Customer.objects.filter(pk=deleted.recipient.customer_id).update(deleted_at=NOW)
        comments = build_report(now=NOW)["comments"]
        self.assertEqual(len(comments), 2)  # blank question 8 is skipped
        newest, oldest = comments
        self.assertIsNone(newest["customer"])
        self.assertEqual(newest["sentiment"], "negative")
        self.assertTrue(newest["is_long"])
        self.assertEqual(len(newest["preview"]), 120)
        self.assertEqual(newest["topics"], ["Phụ kiện"])
        self.assertEqual((oldest["customer"], oldest["sentiment"]), ("Khách 0", "positive"))
        self.assertEqual(oldest["topics"], ["Vợt cầu lông", "Đan / căng cước"])
        self.respond(when=NOW, csat=3, comment="Bình thường")
        self.assertEqual(build_report(now=NOW)["comments"][0]["sentiment"], "neutral")

    # ── scope ───────────────────────────────────────────────────────────
    # tv4: test không trộn khảo sát cũ
    def test_legacy_surveys_are_never_mixed_and_scope_filters_one_survey(self):
        legacy = Survey.objects.create(title="Cũ", status="ACTIVE", created_by=self.manager)
        question = SurveyQuestion.objects.create(survey=legacy, question_text="Old", question_type="RATING")
        recipient = SurveyRecipient.objects.create(survey=legacy, customer=self.customers[9], status="COMPLETED")
        response = SurveyResponse.objects.create(recipient=recipient, status="SUBMITTED", submitted_at=NOW)
        SurveyAnswer.objects.create(response=response, question=question, rating_value=1)
        other = self.make_survey("Đợt 2")
        self.respond(csat=5)
        self.respond(survey=other, csat=3)
        self.assertEqual(build_report(now=NOW)["total"]["count"], 2)
        self.assertEqual(build_report(now=NOW)["csat"]["avg"], 4.0)
        self.assertEqual(build_report(self.survey, now=NOW)["total"]["count"], 1)
        self.client.force_login(self.crm_manager)
        response = self.client.get(reverse("surveys:results"), {"survey_id": legacy.pk})
        self.assertContains(response, "không thuộc bộ 8 câu hỏi")
        self.assertIsNone(response.context["report"])

    # tv4: test bỏ qua phản hồi chưa nộp
    def test_in_progress_responses_are_not_counted(self):
        response = self.respond()
        SurveyResponse.objects.filter(pk=response.pk).update(status="IN_PROGRESS")
        self.assertEqual(build_report(now=NOW)["total"]["count"], 0)


# tv4: test lệnh seed dữ liệu thử
class SeedSurveyReportDemoTests(TestCase):
    # tv4: test seed cần --confirm, --clear chỉ xóa dữ liệu thử
    @patch.dict("os.environ", {"CRM_DEMO_PASSWORD": PASSWORD})
    def test_seed_requires_confirm_and_clear_removes_only_marked_rows(self):
        from io import StringIO
        from django.core.management import CommandError, call_command
        manager = Account.objects.create_user("seed-manager@report.test", PASSWORD, role="MANAGER")
        real = Customer.objects.create(account=Account.objects.create_user("real@report.test", PASSWORD), full_name="Thật")
        kept = Survey.objects.create(title="Khảo sát thật", status="DRAFT", created_by=manager)
        with self.assertRaises(CommandError):
            call_command("seed_survey_report_demo", stdout=StringIO())
        self.assertFalse(Survey.objects.filter(title__startswith="[DỮ LIỆU THỬ]").exists())
        call_command("seed_survey_report_demo", "--confirm", stdout=StringIO())
        call_command("seed_survey_report_demo", "--confirm", stdout=StringIO())  # repeatable
        self.assertEqual(Survey.objects.filter(title__startswith="[DỮ LIỆU THỬ]").count(), 2)
        self.assertEqual(build_report()["total"]["count"], 32)
        call_command("seed_survey_report_demo", "--clear", "--confirm", stdout=StringIO())
        self.assertEqual(list(Survey.objects.values_list("pk", flat=True)), [kept.pk])
        self.assertEqual(list(Customer.objects.values_list("pk", flat=True)), [real.pk])
        self.assertFalse(Account.objects.filter(email__endswith="@survey-report-demo.test").exists())


# tv4: test luồng cấu hình → trả lời → lưu → báo cáo
class SurveyReportFlowTests(TestCase):
    """Configuration → customer answers → stored rows → Customer Report."""

    # tv4: test số liệu báo cáo khớp dữ liệu đã lưu
    def test_end_to_end_numbers_match_stored_answers(self):
        manager = Account.objects.create_user("flow-manager@report.test", PASSWORD, role="MANAGER")
        self.client.force_login(manager)
        start = timezone.localtime() - timedelta(minutes=5)
        response = self.client.post(reverse("surveys:manage_create"), {
            "title": "Luồng đầy đủ", "start_at": start.strftime("%Y-%m-%dT%H:%M"),
            "end_at": (start + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M"), "use_template": "on",
            "objective": "SATISFACTION", "audience": "all"})
        self.assertEqual(response.status_code, 302)
        survey = Survey.objects.get(title="Luồng đầy đủ")
        Survey.objects.filter(pk=survey.pk).update(status="ACTIVE")
        q = {x.config["key"]: x for x in survey.surveyquestion_set.all()}
        opt = {k: list(v.surveyoption_set.order_by("sort_order")) for k, v in q.items()}
        plans = [  # (purchases, segment, csat, criteria, brands, other, nps, comment)
            ((0, 4), 1, 5, (5, NOT_USED, 4, 4), (0, 5), "Apacs", 10, "Đan vợt nhanh hơn"),
            ((0,), 1, 4, (4, 4, NOT_USED, 3), (1,), "", 8, ""),
            ((2,), 0, 2, (2, 3, 3, 2), (0, 2, 3), "", 5, "Giao hàng chậm"),
        ]
        for i, (purchases, segment, csat, criteria, brands, other, nps, comment) in enumerate(plans):
            account = Account.objects.create_user(f"flow{i}@report.test", PASSWORD)
            customer = Customer.objects.create(account=account, full_name=f"Khách luồng {i}")
            recipient = SurveyRecipient.objects.create(survey=survey, customer=customer, status="SENT")
            answers = [{"question_id": q["purchases"].pk, "option_id": opt["purchases"][j].pk} for j in purchases]
            answers.append({"question_id": q["playing_frequency"].pk, "option_id": opt["playing_frequency"][segment].pk})
            answers.append({"question_id": q["overall_satisfaction"].pk, "rating_value": csat})
            for o, value in zip(opt["service_criteria"], criteria):
                answers.append({"question_id": q["service_criteria"].pk, "option_id": o.pk,
                                **({"answer_text": NOT_USED} if value == NOT_USED else {"rating_value": value})})
            answers.append({"question_id": q["highlights"].pk, "option_id": opt["highlights"][0].pk})
            for j in brands:
                item = {"question_id": q["future_brands"].pk, "option_id": opt["future_brands"][j].pk}
                if j == 5:
                    item["answer_text"] = other
                answers.append(item)
            answers.append({"question_id": q["recommendation"].pk, "rating_value": nps})
            answers.append({"question_id": q["suggestions"].pk, "answer_text": comment})
            self.client.force_login(account)
            result = self.client.post(reverse("surveys:submit", args=[recipient.pk]),
                                      {"answers": json.dumps(answers)}, HTTP_ACCEPT="application/json")
            self.assertEqual(result.status_code, 200, result.content)

        self.assertEqual(SurveyResponse.objects.filter(recipient__survey=survey, status="SUBMITTED").count(), 3)
        self.client.force_login(crm_manager("flow-crm@report.test"))
        page = self.client.get(reverse("surveys:results"), {"survey_id": survey.pk})
        report = page.context["report"]
        stored_csat = list(SurveyAnswer.objects.filter(question=q["overall_satisfaction"]).values_list("rating_value", flat=True))
        self.assertEqual(report["total"]["count"], 3)
        self.assertEqual(report["csat"]["avg"], round_half_up(sum(stored_csat) / len(stored_csat), 1))  # 3.7
        self.assertEqual(report["nps"]["score"], 0)  # 1 promoter, 1 passive, 1 detractor
        self.assertEqual((report["segment"]["label"], report["segment"]["pct"]), ("Khách chơi phong trào", 66.7))
        self.assertEqual(report["purchases"]["rows"][0]["label"], "Vợt cầu lông")
        self.assertEqual(report["purchases"]["rows"][0]["pct"], 66.7)
        self.assertEqual(report["brands"]["selections"], 6)
        self.assertEqual([o["text"] for o in report["brands"]["other_texts"]], ["Apacs"])
        self.assertEqual(report["criteria"][1]["not_used"], 1)
        self.assertEqual(report["criteria"][1]["avg"], 3.5)
        self.assertEqual([c["text"] for c in report["comments"]], ["Giao hàng chậm", "Đan vợt nhanh hơn"])
        self.assertEqual(report["comments"][0]["sentiment"], "negative")
        # The Vietnamese CRM layout localizes decimals with a comma.
        self.assertContains(page, "3,7 / 5")
        self.assertContains(page, "0 điểm")
        self.assertContains(page, "Khách chơi phong trào (66,7%)")
        self.assertContains(page, 'id="report-data"')

from collections import Counter

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.errors import AccountPermissionDenied
from apps.accounts.models import Account
from apps.customers.models import Customer, CustomerPreference
from .constants import (AGE_GROUPS, CHOICE_TYPES, MANAGER_GROUP, QuestionType, RECIPIENT_COMPLETED,
                        RESPONSE_SUBMITTED, SurveyStatus)
from .models import Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyRecipient, SurveyResponse


COMPLETED_MESSAGE = "Bạn đã hoàn thành khảo sát này và không thể gửi lại."


def require_survey_manager(actor):
    """ACTIVE ADMIN or ACTIVE account in group CRM_MANAGER may manage surveys."""
    if not getattr(actor, "is_authenticated", False) or not getattr(actor, "pk", None):
        raise AccountPermissionDenied("Survey management requires an ADMIN or CRM_MANAGER account")
    account = Account.objects.filter(pk=actor.pk, status=AccountStatus.ACTIVE).first()
    if account is None or not (account.role == AccountRole.ADMIN
                               or account.groups.filter(name=MANAGER_GROUP).exists()):
        raise AccountPermissionDenied("Survey management requires an ADMIN or CRM_MANAGER account")
    return account


def send_survey(actor, survey, customer_ids):
    require_survey_manager(actor)
    ids = list(dict.fromkeys(int(value) for value in customer_ids))
    found = set(Customer.objects.filter(customer_id__in=ids, status="ACTIVE").values_list("customer_id", flat=True))
    if len(found) != len(ids):
        raise ValidationError("Danh sách khách hàng có ID không hợp lệ hoặc đã bị xóa.")
    created = 0
    with transaction.atomic():
        for customer_id in ids:
            _, was_created = SurveyRecipient.objects.get_or_create(
                survey=survey, customer_id=customer_id, defaults={"status": "SENT"}
            )
            created += was_created
    return {"created": created, "skipped": len(ids) - created}


def recipient_for_user(user, recipient_id, *, lock=False):
    if not getattr(user, "is_authenticated", False):
        raise PermissionDenied
    query = SurveyRecipient.objects.select_related("survey", "customer")
    if lock:
        query = query.select_for_update()
    recipient = query.get(pk=recipient_id)
    if recipient.customer.account_id != user.pk or recipient.customer.status != "ACTIVE":
        raise PermissionDenied
    return recipient


def assert_survey_open(survey):
    now = timezone.now()
    if survey.status not in ("ACTIVE", "PUBLISHED") or (survey.start_at and now < survey.start_at) or (survey.end_at and now > survey.end_at):
        raise ValidationError("Khảo sát hiện không mở để thực hiện.")


def start_survey(user, recipient_id):
    try:
        with transaction.atomic():
            recipient = recipient_for_user(user, recipient_id, lock=True)
            response = SurveyResponse.objects.filter(recipient=recipient).first()
            if response and (response.submitted_at or response.status == "SUBMITTED"):
                return response, False
            assert_survey_open(recipient.survey)
            if response is None:
                response = SurveyResponse.objects.create(recipient=recipient, status="IN_PROGRESS", started_at=timezone.now())
            if recipient.opened_at is None:
                recipient.opened_at = timezone.now()
                recipient.status = "OPENED"
                recipient.save(update_fields=["opened_at", "status"])
            return response, True
    except IntegrityError:
        # A competing request created the unique response. Read it after rollback.
        response = SurveyResponse.objects.get(recipient_id=recipient_id)
        return response, response.submitted_at is None


def submit_survey(user, recipient_id, answers):
    try:
        with transaction.atomic():
            recipient = recipient_for_user(user, recipient_id, lock=True)
            if SurveyResponse.objects.filter(recipient=recipient, status="SUBMITTED").exists() or SurveyResponse.objects.filter(recipient=recipient, submitted_at__isnull=False).exists():
                return False
            assert_survey_open(recipient.survey)
            response, _ = SurveyResponse.objects.get_or_create(
                recipient=recipient, defaults={"status": "IN_PROGRESS", "started_at": timezone.now()}
            )
            if response.submitted_at or response.status == "SUBMITTED":
                return False
            question_ids = [int(item["question_id"]) for item in answers]
            unique_ids = set(question_ids)
            questions = {q.pk: q for q in SurveyQuestion.objects.filter(survey=recipient.survey, pk__in=unique_ids)}
            if len(questions) != len(unique_ids):
                raise ValidationError("Câu hỏi không thuộc khảo sát này.")
            _check_answer_shapes(questions, answers)
            required = set(SurveyQuestion.objects.filter(survey=recipient.survey, is_required=True).values_list("pk", flat=True))
            if not required.issubset(question_ids):
                raise ValidationError("Vui lòng trả lời các câu hỏi bắt buộc.")
            for item in answers:
                question = questions[int(item["question_id"])]
                option_id = item.get("option_id")
                if option_id is not None and not question.surveyoption_set.filter(pk=option_id).exists():
                    raise ValidationError("Lựa chọn không thuộc câu hỏi này.")
                rating = item.get("rating_value")
                if rating is not None and not 1 <= int(rating) <= 5:
                    raise ValidationError("Điểm đánh giá phải từ 1 đến 5.")
                if question.is_required and not (option_id or item.get("answer_text") or rating is not None):
                    raise ValidationError("Vui lòng trả lời các câu hỏi bắt buộc.")
                SurveyAnswer.objects.create(response=response, question=question, option_id=option_id,
                                            answer_text=item.get("answer_text"), rating_value=rating)
            now = timezone.now()
            response.status = "SUBMITTED"
            response.submitted_at = now
            response.save(update_fields=["status", "submitted_at"])
            recipient.status = "COMPLETED"
            recipient.completed_at = now
            recipient.save(update_fields=["status", "completed_at"])
            return True
    except IntegrityError:
        # All answers in this request have rolled back with the transaction.
        if SurveyResponse.objects.filter(recipient_id=recipient_id, status="SUBMITTED").exists():
            return False
        raise


# ───────────────────────── TV5: answer shape rules ─────────────────────────
def _check_answer_shapes(questions, answers):
    """One answer per question, except MULTI_CHOICE (one row per distinct option).
    Choice types need option_id, RATING needs rating_value."""
    per_question = Counter()
    picked = set()
    for item in answers:
        question = questions[int(item["question_id"])]
        per_question[question.pk] += 1
        qtype = question.question_type
        if per_question[question.pk] > 1 and qtype != QuestionType.MULTI_CHOICE:
            raise ValidationError("Mỗi câu hỏi chỉ được trả lời một lần.")
        if qtype in CHOICE_TYPES:
            option_id = item.get("option_id")
            if option_id is None:
                raise ValidationError("Câu hỏi lựa chọn cần chọn một đáp án.")
            if (question.pk, int(option_id)) in picked:
                raise ValidationError("Không được chọn trùng một đáp án.")
            picked.add((question.pk, int(option_id)))
        elif qtype == QuestionType.RATING and item.get("rating_value") is None:
            raise ValidationError("Câu hỏi thang điểm cần có điểm từ 1 đến 5.")


# ───────────────────────── TV5: survey lifecycle ─────────────────────────
def is_survey_open(survey):
    now = timezone.now()
    return (survey.status in (SurveyStatus.ACTIVE, "PUBLISHED")
            and not (survey.start_at and now < survey.start_at)
            and not (survey.end_at and now > survey.end_at))


def close_expired():
    """Auto-close ACTIVE surveys past end_at (no cron needed)."""
    return Survey.objects.filter(status=SurveyStatus.ACTIVE, end_at__lt=timezone.now()
                                 ).update(status=SurveyStatus.CLOSED)


def check_ready_to_send(survey):
    """Return a list of Vietnamese error messages; empty list = ready."""
    errors = []
    questions = list(SurveyQuestion.objects.filter(survey=survey))
    if not questions:
        errors.append("Khảo sát chưa có câu hỏi nào.")
    for q in questions:
        if q.question_type in CHOICE_TYPES and SurveyOption.objects.filter(question=q).count() < 2:
            errors.append(f"Câu \"{q.question_text}\" cần ít nhất 2 lựa chọn.")
    if survey.status == SurveyStatus.CLOSED:
        errors.append("Khảo sát đã đóng, không thể gửi.")
    if survey.end_at is None or survey.end_at <= timezone.now():
        errors.append("Ngày đóng đã qua hoặc chưa đặt, hãy sửa lại thời gian.")
    return errors


def send_to_audience(actor, survey, customers):
    """Send to a queryset of customers and open the survey on first send."""
    ids = list(customers.values_list("customer_id", flat=True))
    with transaction.atomic():
        result = send_survey(actor, survey, ids)
        if survey.status == SurveyStatus.DRAFT:
            survey.status = SurveyStatus.ACTIVE
            survey.save(update_fields=["status", "updated_at"])
    return result


def close_survey(actor, survey):
    require_survey_manager(actor)
    survey.status = SurveyStatus.CLOSED
    survey.save(update_fields=["status", "updated_at"])


# ───────────────────────── TV5: audience filter ─────────────────────────
def _years_ago(today, n):
    try:
        return today.replace(year=today.year - n)
    except ValueError:  # 29/02
        return today.replace(year=today.year - n, day=28)


def playing_level_choices():
    values = (Customer.objects.exclude(playing_level__isnull=True).exclude(playing_level="")
              .order_by("playing_level").values_list("playing_level", flat=True).distinct())
    return [(v, v) for v in values]


def preference_choices():
    values = (CustomerPreference.objects.order_by("preference_value")
              .values_list("preference_value", flat=True).distinct()[:60])
    return [(v, v) for v in values]


def filter_customers(audience="all", age_groups=(), playing_levels=(), preferences=()):
    """ACTIVE customers with an ACTIVE account. Different filters combine with AND,
    several values inside one filter combine with OR."""
    qs = Customer.objects.filter(status="ACTIVE", account__status=AccountStatus.ACTIVE)
    if audience == "all":
        return qs
    today = timezone.localdate()
    if age_groups:
        cond = Q()
        for key, _label, low, high in AGE_GROUPS:
            if key in age_groups:
                cond |= Q(date_of_birth__lte=_years_ago(today, low),
                          date_of_birth__gt=_years_ago(today, high + 1))
        qs = qs.filter(cond)
    if playing_levels:
        qs = qs.filter(playing_level__in=playing_levels)
    if preferences:
        qs = qs.filter(customerpreference__preference_value__in=preferences)
    return qs.distinct()


# ───────────────────────── TV5: statistics ─────────────────────────
def build_stats(survey):
    sent = SurveyRecipient.objects.filter(survey=survey).count()
    done = SurveyRecipient.objects.filter(survey=survey, status=RECIPIENT_COMPLETED).count()
    submitted = SurveyAnswer.objects.filter(response__status=RESPONSE_SUBMITTED)
    items = []
    for q in SurveyQuestion.objects.filter(survey=survey).order_by("sort_order", "question_id"):
        answers = submitted.filter(question=q)
        respondents = answers.values("response").distinct().count()
        item = {"question": q, "respondents": respondents, "rows": [], "texts": [], "avg": None}
        if q.question_type in CHOICE_TYPES:
            for option in SurveyOption.objects.filter(question=q).order_by("sort_order", "option_id"):
                n = answers.filter(option=option).count()
                item["rows"].append({"label": option.option_text, "n": n,
                                     "pct": round(n * 100 / respondents, 1) if respondents else 0})
        elif q.question_type == QuestionType.RATING:
            counts = {i: 0 for i in range(1, 6)}
            for row in answers.exclude(rating_value__isnull=True).values("rating_value").annotate(n=Count("answer_id")):
                if row["rating_value"] in counts:
                    counts[row["rating_value"]] = row["n"]
            avg = answers.aggregate(a=Avg("rating_value"))["a"]
            item["avg"] = round(avg, 2) if avg is not None else None
            item["rows"] = [{"label": f"{k} sao", "n": v,
                             "pct": round(v * 100 / respondents, 1) if respondents else 0}
                            for k, v in counts.items()]
        else:
            item["texts"] = list(answers.exclude(answer_text__isnull=True).exclude(answer_text="")
                                 .select_related("response__recipient__customer").order_by("-answer_id")[:200])
        items.append(item)
    return {"sent": sent, "done": done, "pending": sent - done,
            "rate": round(done * 100 / sent, 1) if sent else 0, "items": items}

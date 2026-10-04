from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.permissions import require_active_admin
from apps.customers.models import Customer
from .models import Survey, SurveyAnswer, SurveyQuestion, SurveyRecipient, SurveyResponse


COMPLETED_MESSAGE = "Bạn đã hoàn thành khảo sát này và không thể gửi lại."


def send_survey(actor, survey, customer_ids):
    require_active_admin(actor)
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
            if len(question_ids) != len(set(question_ids)):
                raise ValidationError("Mỗi câu hỏi chỉ được trả lời một lần.")
            questions = {q.pk: q for q in SurveyQuestion.objects.filter(survey=recipient.survey, pk__in=question_ids)}
            if len(questions) != len(question_ids):
                raise ValidationError("Câu hỏi không thuộc khảo sát này.")
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

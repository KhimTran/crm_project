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
from .configuration import rating_bounds
from .questionnaire import NOT_USED


COMPLETED_MESSAGE = "Bạn đã hoàn thành khảo sát này và không thể gửi lại."


def require_survey_manager(actor):
    """ACTIVE ADMIN, ACTIVE MANAGER, or ACTIVE account in group CRM_MANAGER may manage surveys."""
    if not getattr(actor, "is_authenticated", False) or not getattr(actor, "pk", None):
        raise AccountPermissionDenied("Survey management requires an ADMIN, MANAGER, or CRM_MANAGER account")
    account = Account.objects.filter(pk=actor.pk, status=AccountStatus.ACTIVE).first()
    if account is None or not (account.role in (AccountRole.ADMIN, AccountRole.MANAGER)
                               or account.groups.filter(name=MANAGER_GROUP).exists()):
        raise AccountPermissionDenied("Survey management requires an ADMIN, MANAGER, or CRM_MANAGER account")
    return account


# tv4: khách được mời khảo sát: hồ sơ chưa bị xóa mềm và tài khoản đang hoạt động (không khóa)
def eligible_customers():
    return Customer.objects.filter(status="ACTIVE", account__status=AccountStatus.ACTIVE)


def send_survey(actor, survey, customer_ids):
    """Mời khách hàng và phát hành khảo sát (Nháp → Đang mở) trong cùng một transaction.

    Chỉ phát hành khi khảo sát sẵn sàng (``check_ready_to_send``) và có ít nhất một người nhận
    hợp lệ. Khách bị khóa/đã xóa bị từ chối; khách đã được mời được bỏ qua (không tạo lời mời trùng).
    """
    require_survey_manager(actor)
    ids = list(dict.fromkeys(int(value) for value in customer_ids))
    if not ids:
        raise ValidationError("Chưa có khách hàng nào phù hợp để nhận khảo sát.")
    with transaction.atomic():
        locked = Survey.objects.select_for_update().get(pk=survey.pk)
        errors = check_ready_to_send(locked)
        if errors:
            raise ValidationError(errors)
        found = set(eligible_customers().filter(customer_id__in=ids).values_list("customer_id", flat=True))
        if len(found) != len(ids):
            raise ValidationError("Danh sách khách hàng có ID không hợp lệ, đã bị xóa hoặc bị khóa.")
        created = 0
        for customer_id in ids:
            _, was_created = SurveyRecipient.objects.get_or_create(
                survey=locked, customer_id=customer_id, defaults={"status": "SENT"}
            )
            created += was_created
        if locked.status == SurveyStatus.DRAFT:
            locked.status = SurveyStatus.ACTIVE
            locked.save(update_fields=["status", "updated_at"])
        survey.status = locked.status
    return {"created": created, "skipped": len(ids) - created}


def recipient_for_user(user, recipient_id, *, lock=False):
    """Lời mời của chính khách đang đăng nhập; tài khoản phải là CUSTOMER đang hoạt động (đọc lại DB)."""
    if not getattr(user, "is_authenticated", False):
        raise PermissionDenied
    if not Account.objects.filter(pk=user.pk, role=AccountRole.CUSTOMER, status=AccountStatus.ACTIVE).exists():
        raise PermissionDenied
    query = SurveyRecipient.objects.select_related("survey", "customer")
    if lock:
        query = query.select_for_update()
    recipient = query.get(pk=recipient_id)
    if recipient.customer.account_id != user.pk or recipient.customer.status != "ACTIVE":
        raise PermissionDenied
    if recipient.survey.status == SurveyStatus.DRAFT:
        raise PermissionDenied  # bản nháp không bao giờ lộ cho khách
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
            _check_payload(answers)
            question_ids = [item["question_id"] for item in answers]
            unique_ids = set(question_ids)
            questions = {q.pk: q for q in SurveyQuestion.objects.filter(survey=recipient.survey, pk__in=unique_ids)}
            if len(questions) != len(unique_ids):
                raise ValidationError("Câu hỏi không thuộc khảo sát này.")
            answers = _check_answer_shapes(questions, answers)
            required = set(SurveyQuestion.objects.filter(survey=recipient.survey, is_required=True).values_list("pk", flat=True))
            if not required.issubset(question_ids):
                raise ValidationError("Vui lòng trả lời các câu hỏi bắt buộc.")
            for item in answers:
                question = questions[item["question_id"]]
                option_id = item.get("option_id")
                rating = item.get("rating_value")
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
def _valid_identifier(value):
    return type(value) is int and 1 <= value <= 2147483647


def _check_payload(answers):
    """Validate JSON types before ORM lookups; bool is not an integer answer."""
    if not isinstance(answers, list):
        raise ValidationError("Câu trả lời phải là một danh sách.")
    for item in answers:
        if not isinstance(item, dict) or not _valid_identifier(item.get("question_id")):
            raise ValidationError("Câu trả lời cần có mã câu hỏi là số nguyên hợp lệ.")


def _check_answer_shapes(questions, answers):
    """Validate each type and return normalized copies before saving any answer.

    Optional questions may be omitted. Every supplied answer must be meaningful;
    MULTI_CHOICE keeps the existing one-row-per-distinct-option contract.
    """
    per_question = Counter()
    picked = set()
    normalized = []
    for item in answers:
        question = questions[item["question_id"]]
        per_question[question.pk] += 1
        qtype = question.question_type
        if per_question[question.pk] > 1 and qtype not in (QuestionType.MULTI_CHOICE, QuestionType.MATRIX):
            raise ValidationError("Mỗi câu hỏi chỉ được trả lời một lần.")
        if qtype in CHOICE_TYPES:
            field = "option_id"
            option_id = item.get("option_id")
            if not _valid_identifier(option_id) or not question.surveyoption_set.filter(pk=option_id).exists():
                raise ValidationError("Lựa chọn phải là mã số nguyên thuộc câu hỏi này.")
            if (question.pk, option_id) in picked:
                raise ValidationError("Không được chọn trùng một đáp án.")
            picked.add((question.pk, option_id))
            value = option_id
            if option_id == (question.config or {}).get("other_option_id"):
                other = item.get("answer_text")
                if not isinstance(other, str) or not other.strip() or len(other.strip()) > 200:
                    raise ValidationError("Vui lòng nhập nội dung Khác (tối đa 200 ký tự).")
                if set(item) != {"question_id", "option_id", "answer_text"}:
                    raise ValidationError("Câu trả lời Khác chứa trường không phù hợp.")
                normalized.append({"question_id": question.pk, "option_id": value, "answer_text": other.strip()})
                continue
        elif qtype == QuestionType.RATING:
            field = "rating_value"
            value = item.get(field)
            low, high = rating_bounds(question)
            if type(value) is not int or not low <= value <= high:
                raise ValidationError(f"Điểm đánh giá phải là số nguyên từ {low} đến {high}.")
        elif qtype == QuestionType.MATRIX:
            criterion = item.get("option_id")
            if not _valid_identifier(criterion) or not question.surveyoption_set.filter(pk=criterion).exists():
                raise ValidationError("Tiêu chí phải thuộc câu hỏi đánh giá này.")
            if (question.pk, criterion) in picked:
                raise ValidationError("Mỗi tiêu chí chỉ được trả lời một lần.")
            picked.add((question.pk, criterion))
            if set(item) == {"question_id", "option_id", "rating_value"}:
                score = item["rating_value"]
                if type(score) is not int or not 1 <= score <= 5:
                    raise ValidationError("Điểm từng tiêu chí phải là số nguyên từ 1 đến 5.")
                normalized.append({"question_id": question.pk, "option_id": criterion, "rating_value": score})
            elif set(item) == {"question_id", "option_id", "answer_text"} and item["answer_text"] == NOT_USED:
                normalized.append({"question_id": question.pk, "option_id": criterion, "answer_text": NOT_USED})
            else:
                raise ValidationError("Tiêu chí cần điểm 1–5 hoặc Không sử dụng, không phải cả hai.")
            continue
        elif qtype == QuestionType.TEXT:
            field = "answer_text"
            value = item.get(field)
            if isinstance(value, str) and not value.strip() and not question.is_required and (question.config or {}).get("key") == "suggestions":
                if set(item) != {"question_id", field}:
                    raise ValidationError("Câu trả lời chứa trường không phù hợp với loại câu hỏi.")
                continue
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > 2000:
                raise ValidationError("Câu trả lời tự do phải có nội dung sau khi bỏ khoảng trắng.")
            value = value.strip()
        else:
            raise ValidationError("Loại câu hỏi không được hỗ trợ.")
        if set(item) != {"question_id", field}:
            raise ValidationError("Câu trả lời chứa trường không phù hợp với loại câu hỏi.")
        normalized.append({"question_id": question.pk, field: value})
    for question in questions.values():
        maximum = (question.config or {}).get("max_selections")
        if question.question_type == QuestionType.MULTI_CHOICE and maximum is not None:
            if type(maximum) is not int or maximum < 1 or per_question[question.pk] > maximum:
                raise ValidationError(f"Câu hỏi này chỉ được chọn tối đa {maximum} đáp án.")
        if question.question_type == QuestionType.MATRIX and question.is_required:
            if per_question[question.pk] != question.surveyoption_set.count():
                raise ValidationError("Vui lòng đánh giá hoặc chọn Không sử dụng cho từng tiêu chí bắt buộc.")
    return normalized


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
        if q.question_type == QuestionType.MATRIX and not q.surveyoption_set.exists():
            errors.append(f'Câu "{q.question_text}" cần có tiêu chí đánh giá.')
        if q.question_type == QuestionType.RATING:
            try:
                rating_bounds(q)
            except ValidationError as exc:
                errors.extend(exc.messages)
    if survey.status == SurveyStatus.CLOSED:
        errors.append("Khảo sát đã đóng, không thể gửi.")
    if survey.end_at is None or survey.end_at <= timezone.now():
        errors.append("Ngày đóng đã qua hoặc chưa đặt, hãy sửa lại thời gian.")
    return errors


def send_to_audience(actor, survey, customers):
    """Send to a queryset of customers and open the survey on first send."""
    return send_survey(actor, survey, customers.values_list("customer_id", flat=True))


def close_survey(actor, survey):
    """Đóng thủ công khảo sát đang mở; bản Nháp thì xóa thay vì đóng, đã đóng thì giữ nguyên."""
    require_survey_manager(actor)
    with transaction.atomic():
        locked = Survey.objects.select_for_update().get(pk=survey.pk)
        if locked.status == SurveyStatus.DRAFT:
            raise ValidationError("Khảo sát Nháp chưa phát hành nên không cần đóng.")
        if locked.status != SurveyStatus.CLOSED:
            locked.status = SurveyStatus.CLOSED
            locked.save(update_fields=["status", "updated_at"])
        survey.status = locked.status


# tv4: nhân bản khảo sát thành bản Nháp mới (chép câu hỏi/phương án/cấu hình, không chép người nhận/câu trả lời)
@transaction.atomic
def clone_survey(actor, survey):
    account = require_survey_manager(actor)
    suffix = " (bản sao)"
    copy = Survey.objects.create(
        title=survey.title[:200 - len(suffix)] + suffix, template_key=survey.template_key,
        description=survey.description, start_at=survey.start_at, end_at=survey.end_at,
        status=SurveyStatus.DRAFT, created_by=account)
    for question in SurveyQuestion.objects.filter(survey=survey).order_by("sort_order", "question_id"):
        config = dict(question.config or {})
        new_question = SurveyQuestion.objects.create(
            survey=copy, question_text=question.question_text, question_type=question.question_type,
            is_required=question.is_required, sort_order=question.sort_order, config=config)
        new_ids = {option.pk: SurveyOption.objects.create(question=new_question, option_text=option.option_text,
                                                          sort_order=option.sort_order).pk
                   for option in question.surveyoption_set.order_by("sort_order", "option_id")}
        if "other_option_id" in config:  # trỏ "Khác" sang phương án tương ứng của bản sao
            if config["other_option_id"] in new_ids:
                config["other_option_id"] = new_ids[config["other_option_id"]]
            else:
                config.pop("other_option_id")
            new_question.config = config
            new_question.save(update_fields=["config"])
    return copy


# tv4: 4.1.7 tổng quan kết quả khảo sát (chỉ khảo sát đã phát hành, không tính Nháp)
def survey_overview():
    """published = số khảo sát có status khác DRAFT;
    responses = số lượt trả lời hợp lệ (SurveyResponse SUBMITTED) của các khảo sát đó;
    rate = lời mời đã hoàn thành / tổng lời mời × 100, None khi chưa có lời mời nào.
    Không có số liệu "đã mở form" vì đó không phải lượt trả lời."""
    published = Survey.objects.exclude(status=SurveyStatus.DRAFT)
    invitations = SurveyRecipient.objects.filter(survey__in=published)
    invited = invitations.count()
    done = invitations.filter(status=RECIPIENT_COMPLETED).count()
    return {
        "published": published.count(),
        "responses": SurveyResponse.objects.filter(recipient__survey__in=published, status=RESPONSE_SUBMITTED).count(),
        "invited": invited, "done": done,
        "rate": round(done * 100 / invited, 1) if invited else None,
    }


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
def _distribution(answers, values, respondents, *, stars=False):
    counts = dict(answers.values_list("rating_value").annotate(n=Count("response", distinct=True)))
    return [{"label": f"{value} sao" if stars else str(value), "n": counts.get(value, 0),
             "pct": round(counts.get(value, 0) * 100 / respondents, 1) if respondents else None}
            for value in values]


def build_stats(survey):
    """Thống kê kết quả của MỘT khảo sát (4.1.7); chỉ tính lượt trả lời SUBMITTED của khảo sát này.

    - rate = lời mời COMPLETED / tổng lời mời × 100; None khi chưa mời ai.
    - Chọn một / chọn nhiều: n = số lượt trả lời chọn phương án; pct = n / số lượt trả lời hợp lệ
      của câu đó. Câu chọn nhiều có thể có tổng > 100%.
    - Thang điểm: phân bố + trung bình trên các điểm nằm trong thang của câu.
    - Ma trận: mỗi tiêu chí tính trung bình trên điểm 1–5; "Không sử dụng" và chưa trả lời bị loại
      khỏi mẫu và đếm riêng.
    - Tự do: câu trả lời không rỗng, mới nhất trước.
    Khi câu chưa có ai trả lời: ``no_data`` = True, mọi pct = None (không hiển thị 0% giả).
    """
    sent = SurveyRecipient.objects.filter(survey=survey).count()
    done = SurveyRecipient.objects.filter(survey=survey, status=RECIPIENT_COMPLETED).count()
    total = SurveyResponse.objects.filter(recipient__survey=survey, status=RESPONSE_SUBMITTED).count()
    submitted = SurveyAnswer.objects.filter(response__status=RESPONSE_SUBMITTED,
                                           response__recipient__survey=survey)
    items = []
    for q in SurveyQuestion.objects.filter(survey=survey).order_by("sort_order", "question_id"):
        answers = submitted.filter(question=q)
        item = {"question": q, "rows": [], "texts": [], "other_texts": [], "criteria": [], "avg": None,
                "section": (q.config or {}).get("section", ""), "multi": q.question_type == QuestionType.MULTI_CHOICE}
        if q.question_type in CHOICE_TYPES:
            valid = answers.filter(option__question=q)
            respondents = valid.values("response").distinct().count()
            for option in SurveyOption.objects.filter(question=q).order_by("sort_order", "option_id"):
                n = valid.filter(option=option).values("response").distinct().count()
                item["rows"].append({"label": option.option_text, "n": n,
                                     "pct": round(n * 100 / respondents, 1) if respondents else None})
            other_id = (q.config or {}).get("other_option_id")
            if other_id:
                item["other_texts"] = list(valid.filter(option_id=other_id).exclude(answer_text__isnull=True)
                                          .exclude(answer_text="").select_related("response__recipient__customer")
                                          .order_by("-answer_id")[:200])
        elif q.question_type == QuestionType.RATING:
            low, high = rating_bounds(q)
            valid = answers.filter(rating_value__gte=low, rating_value__lte=high, option__isnull=True)
            respondents = valid.values("response").distinct().count()
            item["scale_max"] = high
            avg = valid.aggregate(a=Avg("rating_value"))["a"]
            item["avg"] = round(avg, 2) if avg is not None else None
            item["rows"] = _distribution(valid, range(low, high + 1), respondents, stars=not q.config)
        elif q.question_type == QuestionType.MATRIX:
            valid = answers.filter(option__question=q).filter(
                Q(rating_value__range=(1, 5), answer_text__isnull=True) |
                Q(rating_value__isnull=True, answer_text=NOT_USED))
            respondents = valid.values("response").distinct().count()
            for criterion in q.surveyoption_set.order_by("sort_order", "option_id"):
                values = valid.filter(option=criterion)
                scores = values.filter(rating_value__range=(1, 5))
                scored = scores.values("response").distinct().count()
                unused = values.filter(answer_text=NOT_USED).values("response").distinct().count()
                avg = scores.aggregate(a=Avg("rating_value"))["a"]
                item["criteria"].append({"label": criterion.option_text, "scored": scored, "not_used": unused,
                    "unanswered": max(total - scored - unused, 0), "avg": round(avg, 2) if avg is not None else None,
                    "rows": _distribution(scores, range(1, 6), scored)})
        else:
            from django.db.models.functions import Trim
            valid = answers.annotate(content=Trim("answer_text")).exclude(content__isnull=True).exclude(content="")
            respondents = valid.values("response").distinct().count()
            item["texts"] = list(valid.select_related("response__recipient__customer").order_by("-answer_id")[:200])
        item["respondents"] = respondents
        item["no_data"] = respondents == 0
        item["unanswered"] = max(total - respondents, 0)
        items.append(item)
    return {"sent": sent, "done": done, "pending": sent - done, "responses": total,
            "rate": round(done * 100 / sent, 1) if sent else None, "items": items}

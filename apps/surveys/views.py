import json
import re
import uuid

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.db import DatabaseError, transaction
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone

from django.db.models import Count, Q

from apps.accounts.decorators import role_required
from apps.accounts.errors import AccountPermissionDenied
from apps.accounts.permissions import account_admin_required
from apps.customers.models import Customer
from apps.customers.portal_text import localize_form, localize_rows, portal_switchable, say, tr
from .constants import BUILDER_TYPES, CHOICE_TYPES, RECIPIENT_COMPLETED, SHOP_NAME, QuestionType, SurveyStatus
from .forms import AudienceForm, BuilderQuestionForm, SurveyBuilderForm
from .configuration import populate_questionnaire, prepare_questions
from .questionnaire import TEMPLATE_KEY
from .models import Survey, SurveyQuestion, SurveyRecipient
from .translator import translate_survey
from .services import (COMPLETED_MESSAGE, build_stats, check_ready_to_send, clone_survey, close_expired, close_survey,
                       eligible_customers, filter_customers, is_survey_open, recipient_for_user, send_survey,
                       send_to_audience, start_survey, submit_survey, survey_overview)

manager_required = role_required("ADMIN", "MANAGER", "CRM_MANAGER")


@account_admin_required
@require_POST
def send(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    try:
        customer_ids = request.POST.getlist("customer_id")
        result = send_survey(request.user, survey, customer_ids)
    except (ValidationError, ValueError) as exc:
        return HttpResponseBadRequest(str(exc))
    messages.success(request, f"Đã gửi khảo sát cho {result['created']} khách hàng. Bỏ qua {result['skipped']} khách hàng đã nhận khảo sát trước đó.")
    return redirect("surveys:send_result", survey_id=survey.pk)


@account_admin_required
@require_GET
@portal_switchable
def send_result(request, survey_id):
    return render(request, "surveys/send_result.html", {"survey": get_object_or_404(Survey, pk=survey_id)})


@require_GET
def take(request, recipient_id):
    try:
        response, can_answer = start_survey(request.user, recipient_id)
    except PermissionDenied:
        return HttpResponseForbidden("Không có quyền thực hiện khảo sát này.")
    except SurveyRecipient.DoesNotExist as exc:
        raise Http404 from exc
    except ValidationError as exc:
        return HttpResponseBadRequest(str(exc))
    if not can_answer:
        messages.info(request, COMPLETED_MESSAGE)
        return redirect("surveys:result", recipient_id=recipient_id)
    questions = prepare_questions(list(SurveyQuestion.objects.filter(survey=response.recipient.survey)
                                       .prefetch_related("surveyoption_set").order_by("sort_order", "question_id")))
    return render(request, "surveys/take.html", {"response": response, "questions": questions})


@require_POST
def submit(request, recipient_id):
    wants_json = "application/json" in request.headers.get("Accept", "")
    try:
        answers = json.loads(request.POST.get("answers", "[]"))
        if not isinstance(answers, list):
            raise ValueError
        submitted = submit_survey(request.user, recipient_id, answers)
    except PermissionDenied:
        return HttpResponseForbidden("Không có quyền thực hiện khảo sát này.")
    except SurveyRecipient.DoesNotExist as exc:
        raise Http404 from exc
    except (ValidationError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        if wants_json:
            errors = exc.messages if isinstance(exc, ValidationError) else ["Dữ liệu câu trả lời không hợp lệ."]
            return JsonResponse({"errors": errors}, status=400)
        return HttpResponseBadRequest(str(exc))
    except DatabaseError:
        if wants_json:
            return JsonResponse({"errors": ["Không thể lưu câu trả lời lúc này. Vui lòng thử lại."]}, status=503)
        return HttpResponseBadRequest("Không thể lưu câu trả lời lúc này. Vui lòng thử lại.")
    messages.success(request, "Đã gửi câu trả lời." if submitted else COMPLETED_MESSAGE)
    if wants_json:
        return JsonResponse({"submitted": submitted, "redirect_url": reverse("surveys:result", args=[recipient_id])})
    return redirect("surveys:result", recipient_id=recipient_id)


@require_GET
def result(request, recipient_id):
    try:
        recipient = recipient_for_user(request.user, recipient_id)
    except PermissionDenied:
        return HttpResponseForbidden("Không có quyền xem khảo sát này.")
    except SurveyRecipient.DoesNotExist as exc:
        raise Http404 from exc
    return render(request, "surveys/result.html", {"recipient": recipient, "completed_message": COMPLETED_MESSAGE})


# ───────────────────────── TV5: CRM – manage surveys (4.1.6, 4.1.7) ─────────────────────────
# tv4: dịch lỗi "chưa thể gửi" sang tiếng Anh khi Admin xem trong Admin Portal (câu có tên câu hỏi xử lý riêng)
def _send_error(message):
    match = re.fullmatch(r'Câu "(.*)" cần ít nhất 2 lựa chọn\.', message, re.S)
    if match:
        return say(message, f'Question "{match.group(1)}" needs at least 2 options.')
    return tr(message)


# tv4: dịch nhãn thống kê (vd. "5 sao") khi Admin xem trong Admin Portal
def _localized_stats(stats):
    for item in stats["items"]:
        item["rows"] = localize_rows(item["rows"])
        item["section"] = tr(item["section"])
        item["question_text"] = tr(item["question"].question_text)
        for criterion in item["criteria"]:
            criterion["label"] = tr(criterion["label"])
            criterion["rows"] = localize_rows(criterion["rows"])
    return stats


# tv4: trang Surveys – đọc danh sách khảo sát (mới nhất trước); nút Xem/Sửa/Xóa dùng view manage_detail/edit/delete có sẵn
@manager_required
@require_GET
@portal_switchable
def manage_list(request):
    close_expired()
    items = list(Survey.objects.annotate(sent=Count("surveyrecipient", distinct=True)).order_by("-survey_id"))
    for survey in items:  # chỉ Nháp chưa gửi cho ai mới sửa/xóa được (cùng quy tắc với manage_delete)
        survey.editable = survey.status == SurveyStatus.DRAFT and not survey.sent
    return render(request, "surveys/manage_list.html", {"items": items})


# ───────────────────────── tv4: trình soạn khảo sát (trang tạo + trang sửa dùng chung) ─────────────────────────
BUILDER_MAX_QUESTIONS = 50
BUILDER_TOKENS = "survey_builder_tokens"  # khóa session: mã form tạo khảo sát → survey_id (chống gửi trùng)
# lỗi của QuestionForm → ô tương ứng trên trình soạn
BUILDER_FIELDS = {"question_text": "text", "question_type": "type", "options_text": "options", "is_required": "text",
                  "max_selections": "max_selections", "rating_min": "rating", "rating_max": "rating",
                  "rating_min_label": "rating", "rating_max_label": "rating", "other_option_position": "options",
                  "placeholder": "placeholder", "section": "text", "__all__": "text"}


# tv4: đọc danh sách câu hỏi do trình soạn (JS) gửi lên dạng JSON
def _parse_builder_questions(raw, instances=None):
    """Trả về (form hợp lệ theo thứ tự, lỗi theo câu {"0": {ô: [lỗi]}}, lỗi chung, dữ liệu thô để nạp lại trình soạn).

    ``instances``: câu hỏi đã lưu của bộ 8 câu – sửa tại chỗ theo đúng thứ tự, không thêm/bớt/đổi thứ tự."""
    try:
        items = json.loads(raw or "[]")
    except ValueError:
        items = None
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        return [], {}, [say("Dữ liệu câu hỏi không hợp lệ.", "The question data is invalid.")], []
    if len(items) > BUILDER_MAX_QUESTIONS:
        return [], {}, [say(f"Khảo sát tối đa {BUILDER_MAX_QUESTIONS} câu hỏi.",
                            f"A survey can have at most {BUILDER_MAX_QUESTIONS} questions.")], items
    if instances is not None and len(items) != len(instances):
        return [], {}, [say("Bộ câu hỏi cố định phải giữ đủ số câu và thứ tự.",
                            "The fixed questionnaire must keep all of its questions and their order.")], items
    forms_, errors = [], {}
    for index, item in enumerate(items):
        kind = str(item.get("type", ""))
        problems = {}
        labels, other = [], False
        if kind in (*CHOICE_TYPES, QuestionType.MATRIX):
            raw_options = item.get("options") if isinstance(item.get("options"), list) else []
            labels = [option.strip() if isinstance(option, str) else "" for option in raw_options]
            other = kind in CHOICE_TYPES and bool(item.get("other"))
            if other:
                labels.append(str(item.get("other_label") or say("Khác", "Other")).strip())
            if any(not label for label in labels):
                problems.setdefault("options", []).append(say("Phương án trả lời không được để trống.",
                                                              "Answer options cannot be empty."))
            folded = [label.casefold() for label in labels if label]
            if len(set(folded)) != len(folded):
                problems.setdefault("options", []).append(say("Các phương án trả lời không được trùng nhau.",
                                                              "Answer options must be different."))
        data = {"question_text": str(item.get("text", "")).strip(), "question_type": kind,
                "options_text": "\n".join(labels), "section": str(item.get("section") or "")}
        for name in ("max_selections", "rating_min", "rating_max", "rating_min_label", "rating_max_label", "placeholder"):
            value = item.get(name)
            data[name] = "" if value is None or isinstance(value, bool) else str(value).strip()
        if kind != QuestionType.MULTI_CHOICE:
            data["max_selections"] = ""
        if instances is not None:  # bộ 8 câu: thang điểm giữ chữ chú thích cố định của phiên bản
            data["rating_min_label"] = data["rating_max_label"] = ""
        if other:
            data["other_option_position"] = str(len(labels))
        if item.get("required"):
            data["is_required"] = "on"
        form = localize_form(BuilderQuestionForm(data, instance=instances[index] if instances is not None else None))
        if not form.is_valid():
            for field, field_errors in form.errors.items():
                bucket = problems.setdefault(BUILDER_FIELDS.get(field, "text"), [])
                bucket.extend(message for message in (tr(m) for m in field_errors) if message not in bucket)
        if problems:
            errors[str(index)] = problems
        else:
            forms_.append(form)
    return forms_, errors, [], items


# tv4: câu hỏi đã lưu → dữ liệu của trình soạn (thứ tự theo sort_order; lựa chọn "Khác" tách riêng)
def _builder_items(survey):
    items = []
    for question in (SurveyQuestion.objects.filter(survey=survey).prefetch_related("surveyoption_set")
                     .order_by("sort_order", "question_id")):
        config = question.config or {}
        options = sorted(question.surveyoption_set.all(), key=lambda o: (o.sort_order, o.option_id))
        other = next((o for o in options if o.pk == config.get("other_option_id")), None)
        items.append({
            "text": question.question_text, "type": question.question_type, "required": question.is_required,
            "options": [o.option_text for o in options if o is not other],
            "other": other is not None, "other_label": other.option_text if other else "",
            "max_selections": config.get("max_selections"), "rating_min": config.get("rating_min", 1),
            "rating_max": config.get("rating_max", 5), "rating_min_label": config.get("rating_min_label", ""),
            "rating_max_label": config.get("rating_max_label", ""), "placeholder": config.get("placeholder", ""),
            "section": config.get("section", ""), "key": config.get("key", ""),
        })
    return items


# tv4: quy tắc backend: chỉ khảo sát Nháp, chưa gửi cho ai và chưa có câu trả lời mới sửa được
def _survey_locked(survey):
    return (survey.status != SurveyStatus.DRAFT or survey.surveyrecipient_set.exists()
            or survey.surveyquestion_set.filter(surveyanswer__isnull=False).exists())


# tv4: lọc danh sách khách nhận khảo sát theo lựa chọn đối tượng (dùng chung cho trang tạo và trang gửi)
def _audience_customers(data):
    if data["audience"] == "pick":
        return eligible_customers().filter(customer_id__in=data["customer_ids"])
    return filter_customers(data["audience"], data["age_groups"], data["playing_levels"], data["preferences"])


# tv4: form đối tượng nhận cho trình soạn: nạp lựa chọn đã lưu cùng bản Nháp, nhãn theo ảnh mẫu
def _builder_audience_form(data, survey):
    saved = survey.audience if survey is not None and survey.audience else None
    form = AudienceForm(data, initial=saved)
    form.fields["audience"].choices = [("all", say("Tất cả khách hàng", "All customers")),
                                       ("filter", say("Nhóm khách hàng", "Customer group")),
                                       ("pick", say("Chọn khách hàng cụ thể", "Specific customers"))]
    return localize_form(form)


# tv4: đối tượng nhận lưu vào cột surveys.audience
def _audience_data(data):
    return {"audience": data["audience"], "age_groups": list(data.get("age_groups") or []),
            "playing_levels": list(data.get("playing_levels") or []), "preferences": list(data.get("preferences") or []),
            "customer_ids": [int(value) for value in data.get("customer_ids") or []] if data["audience"] == "pick" else []}


# tv4: chữ dùng trong trình soạn (JS) – dịch ở server để Admin Portal hiện tiếng Anh
def _builder_labels():
    pairs = {
        "untitled": ("(Chưa nhập nội dung câu hỏi)", "(Untitled question)"),
        "untitledSurvey": ("Tiêu đề khảo sát", "Survey title"),
        "emptyList": ("Chưa có câu hỏi nào. Bấm \"Thêm câu hỏi\" để bắt đầu.", "No questions yet. Click \"Add Question\" to start."),
        "text": ("Nội dung câu hỏi", "Question text"), "textHint": ("Nhập nội dung câu hỏi", "Enter the question"),
        "type": ("Loại câu hỏi", "Question type"), "options": ("Các phương án trả lời", "Answer options"),
        "criteria": ("Các tiêu chí đánh giá", "Criteria"), "option": ("Phương án", "Option"),
        "optionHint": ("Nhập phương án", "Enter an option"), "addOption": ("Thêm phương án", "Add option"),
        "editOption": ("Sửa phương án", "Edit option"), "deleteOption": ("Xóa phương án", "Delete option"),
        "required": ("Bắt buộc trả lời", "Required"), "requiredBadge": ("Bắt buộc", "Required"),
        "advanced": ("Tùy chọn nâng cao", "Advanced options"),
        "limit": ("Giới hạn số lựa chọn tối đa", "Limit maximum selections"),
        "limitLabel": ("Số lựa chọn tối đa", "Maximum selections"),
        "other": ("Thêm lựa chọn \"Khác\" kèm ô nhập", "Add an \"Other\" option with a text box"),
        "otherLabel": ("Nhãn lựa chọn Khác", "Other option label"), "otherDefault": ("Khác", "Other"),
        "otherInput": ("Nội dung khác", "Other answer"),
        "duplicate": ("Nhân bản câu hỏi", "Duplicate question"), "remove": ("Xóa câu hỏi", "Delete question"),
        "confirmRemove": ("Xóa câu hỏi này?", "Delete this question?"),
        "confirmType": ("Đổi sang loại này sẽ bỏ các phương án đã nhập. Tiếp tục?",
                        "Switching to this type removes the options you entered. Continue?"),
        "ratingMin": ("Điểm tối thiểu", "Minimum score"), "ratingMax": ("Điểm tối đa", "Maximum score"),
        "ratingMinLabel": ("Nhãn điểm thấp nhất", "Lowest score label"),
        "ratingMaxLabel": ("Nhãn điểm cao nhất", "Highest score label"),
        "ratingMinHint": ("VD: Rất không hài lòng", "e.g. Very dissatisfied"),
        "ratingMaxHint": ("VD: Rất hài lòng", "e.g. Very satisfied"),
        "placeholder": ("Gợi ý trong ô trả lời", "Answer box hint"),
        "placeholderHint": ("VD: Nhập ý kiến của bạn...", "e.g. Type your answer..."),
        "answerHint": ("Nhập câu trả lời của bạn...", "Type your answer..."),
        "drag": ("Kéo để đổi thứ tự (hoặc dùng phím mũi tên lên/xuống)", "Drag to reorder (or use the up/down arrow keys)"),
        "toggle": ("Mở/đóng câu hỏi", "Expand/collapse question"),
        "matrixHint": ("1: Rất tệ · 5: Rất tốt", "1: Very poor · 5: Very good"),
        "choose": ("-- Chọn --", "-- Select --"),
        "chooseMax": ("Chọn tối đa {n} đáp án", "Choose up to {n} answers"),
        # kiểm tra phía trình duyệt (server vẫn kiểm tra lại)
        "errRequired": ("Vui lòng nhập thông tin này.", "This field is required."),
        "errText": ("Vui lòng nhập nội dung câu hỏi.", "Enter the question text."),
        "errOptionsMin": ("Cần ít nhất 2 phương án trả lời.", "Add at least 2 answer options."),
        "errOptionsEmpty": ("Phương án trả lời không được để trống.", "Answer options cannot be empty."),
        "errOptionsDup": ("Các phương án trả lời không được trùng nhau.", "Answer options must be different."),
        "errLimit": ("Số lựa chọn tối đa phải từ 1 đến {n}.", "Maximum selections must be between 1 and {n}."),
        "errRating": ("Điểm tối thiểu phải nhỏ hơn điểm tối đa (trong khoảng 1–10).",
                      "The minimum score must be lower than the maximum (between 1 and 10)."),
        "errEndDate": ("Ngày kết thúc phải sau hoặc bằng ngày bắt đầu.", "The end date must be on or after the start date."),
        "errPastDate": ("Ngày bắt đầu không được ở quá khứ.", "The start date cannot be in the past."),
        "errFilter": ("Hãy chọn ít nhất một điều kiện lọc, hoặc chọn \"Tất cả khách hàng\".",
                      "Choose at least one filter, or choose \"All customers\"."),
        "errPick": ("Hãy chọn ít nhất một khách hàng.", "Select at least one customer."),
        "errNoQuestions": ("Khảo sát chưa có câu hỏi nào.", "The survey has no questions yet."),
        "errFix": ("Vui lòng kiểm tra lại các ô được đánh dấu.", "Please check the highlighted fields."),
        "errCount": ("Không đếm được số khách nhận. Vui lòng thử lại.", "Could not count the recipients. Please try again."),
        "countLoading": ("Đang đếm số khách hàng sẽ nhận...", "Counting recipients..."),
        "countText": ("Khảo sát sẽ được gửi tới {n} khách hàng. Sau khi phát hành, câu hỏi không thể sửa nữa.",
                      "The survey will be sent to {n} customer(s). Questions cannot be edited after publishing."),
        "countZero": ("Không có khách hàng nào phù hợp với đối tượng đã chọn.", "No customers match the selected audience."),
        "saving": ("Đang lưu...", "Saving..."),
        "noMatch": ("Không tìm thấy khách hàng phù hợp.", "No matching customers."),
        "selectedCount": ("Đã chọn {n} khách hàng", "{n} customer(s) selected"),
    }
    return {key: say(vi, en) for key, (vi, en) in pairs.items()}


# tv4: ghi nhớ mã form đã tạo khảo sát để lần gửi lặp (bấm 2 lần, F5) không tạo bản trùng
def _remember_builder_token(request, token, survey_id):
    tokens = dict(request.session.get(BUILDER_TOKENS, {}))
    tokens[token] = survey_id
    request.session[BUILDER_TOKENS] = dict(list(tokens.items())[-20:])


# tv4: lưu thông tin, đối tượng và toàn bộ câu hỏi (theo thứ tự kéo thả) trong một transaction; phát hành nếu được yêu cầu
def _save_builder(request, survey, form, audience_form, question_forms, *, fixed, use_template, publish):
    with transaction.atomic():
        if survey is not None and _survey_locked(Survey.objects.select_for_update().get(pk=survey.pk)):
            raise ValidationError("Không sửa câu hỏi của khảo sát đã gửi hoặc đã có câu trả lời.")
        saved = form.save(commit=False)
        if survey is None:
            saved.created_by = request.user
            saved.status = SurveyStatus.DRAFT
        saved.audience = _audience_data(audience_form.cleaned_data)
        saved.save()
        if use_template:
            populate_questionnaire(saved)
        else:
            if not fixed:  # Nháp chưa gửi: chưa có câu trả lời nào trỏ tới nên dựng lại theo thứ tự kéo thả
                SurveyQuestion.objects.filter(survey=saved).delete()
            for question_form in question_forms:  # bộ 8 câu: form gắn với câu đã lưu nên sửa tại chỗ
                question_form.save_for(saved)
        result = send_to_audience(request.user, saved, _audience_customers(audience_form.cleaned_data)) if publish else None
    if settings.CONTENT_AUTO_TRANSLATE:
        translate_survey(saved)  # tv4: dịch sẵn tiếng Anh cho Manager; lỗi mạng chỉ bỏ qua bản dịch, không chặn việc lưu
    return saved, result


# tv4: trang tạo/sửa khảo sát (bố cục 2 cột: thông tin + câu hỏi | trạng thái + xem trước)
def _survey_builder(request, survey):
    posted = request.method == "POST"
    locked = survey is not None and _survey_locked(survey)
    if posted and locked:
        messages.error(request, tr("Chỉ sửa được khảo sát ở trạng thái Nháp."))
        return redirect("surveys:manage_edit", survey_id=survey.pk)
    fixed = survey is not None and survey.template_key == TEMPLATE_KEY
    mode = "create" if survey is None else "readonly" if locked else "fixed" if fixed else "edit"
    form = localize_form(SurveyBuilderForm(request.POST if posted else None, instance=survey))
    audience_form = _builder_audience_form(request.POST if posted else None, survey)
    items = _builder_items(survey) if survey is not None else []
    question_errors, general_errors = {}, []
    token = request.POST.get("form_token", "") if posted else uuid.uuid4().hex
    if not re.fullmatch(r"[0-9a-f]{32}", token):
        token = uuid.uuid4().hex
    if posted:
        action = request.POST.get("action")
        action = action if action in ("save", "save_add", "publish") else "save"
        if survey is None:
            done = request.session.get(BUILDER_TOKENS, {}).get(token)
            if done and Survey.objects.filter(pk=done).exists():
                messages.info(request, say("Khảo sát này đã được lưu trước đó.", "This survey has already been saved."))
                return redirect("surveys:manage_edit", survey_id=done)
        # tương thích: tạo bằng bộ 8 câu mẫu chỉ còn ở backend (trang không còn ô chọn này)
        use_template = survey is None and bool(request.POST.get("use_template"))
        question_forms = []
        if not use_template:
            instances = (list(SurveyQuestion.objects.filter(survey=survey).order_by("sort_order", "question_id"))
                         if fixed else None)
            question_forms, question_errors, general_errors, items = _parse_builder_questions(
                request.POST.get("questions_json"), instances)
        valid = all([form.is_valid(), audience_form.is_valid()]) and not question_errors and not general_errors
        if valid and action == "publish" and not (fixed or use_template or question_forms):
            general_errors.append(say("Khảo sát chưa có câu hỏi nào.", "The survey has no questions yet."))
            valid = False
        if valid:
            try:
                saved, result = _save_builder(request, survey, form, audience_form, question_forms, fixed=fixed,
                                              use_template=use_template, publish=action == "publish")
            except ValidationError as exc:
                general_errors.extend(_send_error(message) for message in exc.messages)
                form.instance.pk = survey.pk if survey is not None else None  # bản lưu đã rollback
            except AccountPermissionDenied as exc:
                general_errors.append(str(exc))
                form.instance.pk = survey.pk if survey is not None else None
            else:
                if survey is None:
                    _remember_builder_token(request, token, saved.pk)
                if result is not None:
                    note = say(f" (bỏ qua {result['skipped']} người đã nhận trước đó)",
                               f" ({result['skipped']} previous recipient(s) skipped)") if result["skipped"] else ""
                    messages.success(request, say(f"Đã phát hành khảo sát cho {result['created']} khách hàng{note}.",
                                                  f"Survey published to {result['created']} customer(s){note}."))
                    return redirect("surveys:manage_detail", survey_id=saved.pk)
                if use_template:
                    messages.success(request, say("Đã tạo khảo sát với bộ 8 câu hỏi phiên bản 1.",
                                                  "Survey created with the 8-question questionnaire, version 1."))
                else:
                    messages.success(request, say("Đã lưu khảo sát Nháp.", "Draft survey saved."))
                url = reverse("surveys:manage_edit", args=[saved.pk])
                return redirect(url + "?add=1" if action == "save_add" and not (fixed or use_template) else url)
    if mode == "readonly":  # chỉ xem: khóa mọi ô (vẫn mở/đóng được từng câu hỏi để xem)
        for field in (*form.fields.values(), *audience_form.fields.values()):
            field.disabled = True
    status = survey.status if survey is not None else SurveyStatus.DRAFT
    selected ={str(value) for value in (audience_form["customer_ids"].value() or [])}
    customers = [{"id": c.customer_id, "name": c.full_name, "phone": c.phone or "", "email": c.account.email,
                  "checked": str(c.customer_id) in selected}
                 for c in eligible_customers().select_related("account").order_by("full_name", "customer_id")]
    types = [{"value": value, "label": say(label, english), "badge": say(badge, badge_en)}
             for (value, label, badge), (english, badge_en) in zip(BUILDER_TYPES, [
                 ("Multiple choice (pick 1)", "Single choice"), ("Multiple answers", "Multiple answers"),
                 ("Rating scale", "Rating"), ("Free text", "Free text"), ("Criteria rating", "Criteria")])]
    if not any(item.get("type") == QuestionType.MATRIX for item in items):
        types = [t for t in types if t["value"] != QuestionType.MATRIX]  # ma trận chỉ giữ cho câu cũ đã có
    builder = {"mode": mode, "isNew": survey is None, "addOnLoad": request.GET.get("add") == "1" and mode == "edit",
               "countUrl": reverse("surveys:manage_audience_count"), "today": timezone.localdate().isoformat(),
               "types": types, "labels": _builder_labels(), "errors": question_errors, "maxQuestions": BUILDER_MAX_QUESTIONS}
    heading = say("Tạo khảo sát mới", "Create Survey") if survey is None else say("Chỉnh sửa khảo sát", "Edit Survey")
    return render(request, "surveys/manage_create.html", {
        "form": form, "audience_form": audience_form, "survey": survey, "mode": mode, "heading": heading,
        "builder_items": items, "builder": builder, "general_errors": general_errors, "form_token": token,
        "customers": customers, "status": status, "shop_name": SHOP_NAME,
        "status_label": tr(SurveyStatus(status).label) if status in SurveyStatus.values else status})


@manager_required
@portal_switchable
def manage_create(request):
    return _survey_builder(request, None)


@manager_required
@portal_switchable
def manage_edit(request, survey_id):
    return _survey_builder(request, get_object_or_404(Survey, pk=survey_id))


# tv4: số khách sẽ nhận khảo sát theo đối tượng đang chọn (cho hộp xác nhận Phát hành)
@manager_required
@require_GET
@portal_switchable
def manage_audience_count(request):
    form = localize_form(AudienceForm(request.GET))
    if not form.is_valid():
        errors = [tr(message) for message in form.non_field_errors()]
        return JsonResponse({"errors": errors or [say("Đối tượng nhận chưa hợp lệ.", "The audience selection is invalid.")]},
                            status=400)
    return JsonResponse({"count": _audience_customers(form.cleaned_data).count()})


@manager_required
@require_POST
@portal_switchable
def manage_delete(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if survey.status != SurveyStatus.DRAFT or SurveyRecipient.objects.filter(survey=survey).exists():
        messages.error(request, say("Chỉ xóa được khảo sát Nháp chưa gửi cho ai. Hãy dùng \"Đóng khảo sát\".",
                                    "Only Draft surveys that were never sent can be deleted. Use \"Close Survey\" instead."))
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    survey.delete()
    messages.success(request, say("Đã xóa khảo sát.", "Survey deleted."))
    return redirect("surveys:manage_list")


# tv4: dữ liệu biểu đồ cho từng câu hỏi ở trang xem khảo sát (Chọn một → tròn, còn lại → cột; câu tự do không có biểu đồ)
def _question_charts(stats):
    charts = {}
    for item in stats["items"]:
        q, kind = item["question"], None
        if item["no_data"] or q.question_type == QuestionType.TEXT:
            continue
        if q.question_type == QuestionType.MATRIX:
            kind, labels = "bar-h", [c["label"].split(":")[0] for c in item["criteria"]]  # tên ngắn trước dấu ":"
            values, pcts, top = [c["avg"] or 0 for c in item["criteria"]], [None] * len(labels), 5
        else:
            kind = {QuestionType.SINGLE_CHOICE: "doughnut", QuestionType.MULTI_CHOICE: "bar-h"}.get(q.question_type, "bar")
            labels, values = [r["label"] for r in item["rows"]], [r["n"] for r in item["rows"]]
            pcts, top = [r["pct"] for r in item["rows"]], None
        charts[str(q.question_id)] = {"kind": kind, "labels": labels, "values": values, "pcts": pcts, "max": top}
    return charts


@manager_required
@require_GET
@portal_switchable
def manage_detail(request, survey_id):
    close_expired()
    survey = get_object_or_404(Survey, pk=survey_id)
    questions = prepare_questions(list(SurveyQuestion.objects.filter(survey=survey).prefetch_related("surveyoption_set")
                                      .order_by("sort_order", "question_id")))
    recipients = SurveyRecipient.objects.filter(survey=survey)
    stats = _localized_stats(build_stats(survey))
    return render(request, "surveys/manage_detail.html", {
        "stats": stats, "charts": _question_charts(stats),
        "survey": survey, "questions": questions, "is_draft": survey.status == SurveyStatus.DRAFT and not recipients.exists(),
        "status_label": tr(SurveyStatus(survey.status).label) if survey.status in SurveyStatus.values else survey.status,
        "fixed_questionnaire": survey.template_key == TEMPLATE_KEY,
        "sent": recipients.count(), "done": recipients.filter(status=RECIPIENT_COMPLETED).count()})


@manager_required
@portal_switchable
def manage_send(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    errors = [_send_error(e) for e in check_ready_to_send(survey)]
    form = localize_form(AudienceForm(request.POST or None))
    preview = None
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        customers = _audience_customers(data)
        if request.POST.get("action") == "send" and not errors:
            try:
                result = send_to_audience(request.user, survey, customers)
            except (AccountPermissionDenied, ValidationError) as exc:
                messages.error(request, tr(exc.messages[0] if isinstance(exc, ValidationError) else str(exc)))
                return redirect("surveys:manage_detail", survey_id=survey.pk)
            note = say(f" (bỏ qua {result['skipped']} người đã nhận trước đó)",
                       f" ({result['skipped']} previous recipient(s) skipped)") if result["skipped"] else ""
            messages.success(request, say(f"Đã gửi khảo sát cho {result['created']} khách hàng{note}.",
                                          f"Survey sent to {result['created']} customer(s){note}."))
            return redirect("surveys:manage_detail", survey_id=survey.pk)
        preview = customers.count()
    return render(request, "surveys/manage_send.html",
                  {"survey": survey, "form": form, "errors": errors, "preview": preview})


@manager_required
@require_POST
@portal_switchable
def manage_close(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    try:
        close_survey(request.user, survey)
    except ValidationError as exc:
        messages.error(request, tr(exc.messages[0]))
    else:
        messages.success(request, say("Đã đóng khảo sát.", "Survey closed."))
    return redirect("surveys:manage_detail", survey_id=survey.pk)


# tv4: 4.1.6 nhân bản khảo sát thành bản Nháp mới để sửa nội dung khi bản cũ đã gửi/có câu trả lời
@manager_required
@require_POST
@portal_switchable
def manage_clone(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    copy = clone_survey(request.user, survey)
    messages.success(request, say("Đã tạo bản sao Nháp. Hãy kiểm tra thời gian và nội dung trước khi gửi.",
                                  "Draft copy created. Check its schedule and content before sending."))
    return redirect("surveys:manage_detail", survey_id=copy.pk)


@manager_required
@require_GET
@portal_switchable
def manage_stats(request, survey_id):
    close_expired()
    survey = get_object_or_404(Survey, pk=survey_id)
    return render(request, "surveys/manage_stats.html", {"survey": survey, "stats": _localized_stats(build_stats(survey))})


# ───────────────────────── TV5: customer – my surveys (4.2.5) ─────────────────────────
@role_required("CUSTOMER")
@require_GET
def my_surveys(request):
    close_expired()
    customer = Customer.objects.filter(account=request.user, status="ACTIVE").first()
    todo, done, closed = [], [], []
    if customer is None:
        messages.error(request, "Tài khoản chưa có hồ sơ khách hàng.")
    else:
        rows = SurveyRecipient.objects.filter(customer=customer).exclude(survey__status=SurveyStatus.DRAFT) \
            .select_related("survey").order_by("-sent_at")
        now = timezone.now()
        for recipient in rows:
            survey = recipient.survey
            recipient.upcoming = (survey.status == SurveyStatus.ACTIVE and survey.start_at is not None
                                  and now < survey.start_at)
            if recipient.status == RECIPIENT_COMPLETED:
                done.append(recipient)
            elif is_survey_open(survey) or recipient.upcoming:
                todo.append(recipient)  # chưa tới giờ mở: hiện trong "Chưa làm" nhưng chưa có nút làm
            else:
                closed.append(recipient)  # đã đóng hoặc hết hạn
    return render(request, "surveys/my_surveys.html", {"todo": todo, "done": done, "closed": closed})

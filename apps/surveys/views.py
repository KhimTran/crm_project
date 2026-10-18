import json
import re

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
from apps.customers.portal_text import localize_form, localize_rows, portal_english, say, tr
from .constants import RECIPIENT_COMPLETED, SurveyStatus
from .forms import AudienceForm, QuestionForm, SurveyCreateForm, SurveyForm
from .configuration import populate_questionnaire, prepare_questions
from .questionnaire import TEMPLATE_KEY
from .models import Survey, SurveyQuestion, SurveyRecipient
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
@portal_english
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
    return stats


# tv4: lưu câu hỏi; nếu khảo sát vừa được gửi/có câu trả lời (kiểm tra lại khi khóa dòng) thì báo lỗi thay vì 500
def _save_question(request, form, survey):
    try:
        form.save_for(survey)
    except ValidationError as exc:
        messages.error(request, tr(exc.messages[0]))
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    return None


def _draft_or_redirect(request, survey):
    if (survey.status != SurveyStatus.DRAFT or survey.surveyrecipient_set.exists()
            or survey.surveyquestion_set.filter(surveyanswer__isnull=False).exists()):
        messages.error(request, tr("Chỉ sửa được khảo sát ở trạng thái Nháp."))
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    return None


@manager_required
@require_GET
@portal_english
def manage_list(request):
    close_expired()
    qs = Survey.objects.annotate(
        sent=Count("surveyrecipient", distinct=True),
        done=Count("surveyrecipient", filter=Q(surveyrecipient__status=RECIPIENT_COMPLETED), distinct=True),
    ).order_by("-survey_id")
    status = request.GET.get("status", "")
    if status in SurveyStatus.values:
        qs = qs.filter(status=status)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(title__icontains=q)
    surveys = list(qs)
    for survey in surveys:  # chưa trả lời, tỷ lệ phản hồi (None khi chưa mời ai) và nhãn trạng thái
        survey.pending = survey.sent - survey.done
        survey.rate = round(survey.done * 100 / survey.sent, 1) if survey.sent else None
        survey.status_label = tr(SurveyStatus(survey.status).label) if survey.status in SurveyStatus.values else survey.status
    return render(request, "surveys/manage_list.html",
                  {"surveys": surveys, "status": status, "q": q, "overview": survey_overview(),
                   "statuses": [(value, tr(label)) for value, label in SurveyStatus.choices]})


# tv4: 4.1.7 trang Survey Results riêng (tách khỏi Customer Report), số liệu từ bộ 8 câu hỏi đã phát hành.
@manager_required
@require_GET
@portal_english
def survey_results(request):
    from .survey_report import build_report, published_questionnaire_surveys

    surveys = published_questionnaire_surveys().order_by("-survey_id").only("survey_id", "title")
    selected_survey, survey_error = None, ""
    if request.GET.get("survey_id"):
        try:
            selected_survey = surveys.filter(pk=int(request.GET["survey_id"])).first()
        except (ValueError, OverflowError):
            pass
        if selected_survey is None:
            survey_error = say("Khảo sát được chọn không tồn tại, chưa phát hành hoặc không thuộc bộ 8 câu hỏi.",
                               "The selected survey does not exist, is unpublished or is not an 8-question survey.")
    report = None if survey_error else build_report(selected_survey)
    charts = None
    if report:
        charts = {
            "purchases": [{"label": r["label"], "n": r["n"], "pct": r["pct"]} for r in report["purchases"]["rows"]],
            "brands": [{"label": r["label"], "n": r["n"], "share_pct": r["share_pct"],
                        "respondent_pct": r["respondent_pct"]} for r in report["brands"]["rows"]],
            "trend": [{"label": r["label"], "avg": r["avg"], "n": r["n"]} for r in report["csat_trend"]],
            "labels": {"respondents": say("người chọn", "respondents"),
                       "share": say("lượt chọn", "of selections"),
                       "respondent_share": say("người trả lời có chọn hãng này", "of respondents chose this brand"),
                       "csat": say("CSAT trung bình", "Average CSAT"),
                       "responses": say("lượt trả lời", "responses")},
        }
    return render(request, "surveys/results_report.html", {
        "generated_at": timezone.localtime(), "surveys": surveys, "selected_survey": selected_survey,
        "survey_error": survey_error, "report": report, "charts": charts,
    })


@manager_required
@portal_english
def manage_create(request):
    form = localize_form(SurveyCreateForm(request.POST if request.method == "POST" else None))
    if request.method == "POST" and form.is_valid():
        survey = form.save(commit=False)
        survey.created_by = request.user
        survey.status = SurveyStatus.DRAFT
        use_template = form.cleaned_data["use_template"]
        with transaction.atomic():
            survey.save()
            if use_template:
                populate_questionnaire(survey)
        if use_template:
            messages.success(request, say("Đã tạo khảo sát với bộ 8 câu hỏi phiên bản 1.",
                                          "Survey created with the 8-question questionnaire, version 1."))
        else:
            messages.success(request, say("Đã tạo khảo sát Nháp. Hãy thêm câu hỏi trước khi gửi.",
                                          "Draft survey created. Add questions before sending it."))
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    return render(request, "surveys/manage_form.html", {"form": form, "heading": say("Tạo khảo sát mới", "Create Survey")})


@manager_required
@portal_english
def manage_edit(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if (blocked := _draft_or_redirect(request, survey)):
        return blocked
    form = localize_form(SurveyForm(request.POST or None, instance=survey))
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, say("Đã cập nhật khảo sát.", "Survey updated."))
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    return render(request, "surveys/manage_form.html", {"form": form, "heading": say("Sửa khảo sát", "Edit Survey")})


@manager_required
@require_POST
@portal_english
def manage_delete(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if survey.status != SurveyStatus.DRAFT or SurveyRecipient.objects.filter(survey=survey).exists():
        messages.error(request, say("Chỉ xóa được khảo sát Nháp chưa gửi cho ai. Hãy dùng \"Đóng khảo sát\".",
                                    "Only Draft surveys that were never sent can be deleted. Use \"Close Survey\" instead."))
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    survey.delete()
    messages.success(request, say("Đã xóa khảo sát.", "Survey deleted."))
    return redirect("surveys:manage_list")


@manager_required
@require_GET
@portal_english
def manage_detail(request, survey_id):
    close_expired()
    survey = get_object_or_404(Survey, pk=survey_id)
    questions = prepare_questions(list(SurveyQuestion.objects.filter(survey=survey).prefetch_related("surveyoption_set")
                                      .order_by("sort_order", "question_id")))
    recipients = SurveyRecipient.objects.filter(survey=survey)
    return render(request, "surveys/manage_detail.html", {
        "survey": survey, "questions": questions, "is_draft": survey.status == SurveyStatus.DRAFT and not recipients.exists(),
        "status_label": tr(SurveyStatus(survey.status).label) if survey.status in SurveyStatus.values else survey.status,
        "fixed_questionnaire": survey.template_key == TEMPLATE_KEY,
        "sent": recipients.count(), "done": recipients.filter(status=RECIPIENT_COMPLETED).count()})


@manager_required
@portal_english
def question_add(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if (blocked := _draft_or_redirect(request, survey)):
        return blocked
    if survey.template_key == TEMPLATE_KEY:
        return HttpResponseBadRequest("Bộ câu hỏi phiên bản này gồm đúng 8 câu; hãy tạo khảo sát mới khi đổi cấu trúc.")
    form = localize_form(QuestionForm(request.POST or None))
    if request.method == "POST" and form.is_valid():
        if (blocked := _save_question(request, form, survey)):
            return blocked
        messages.success(request, say("Đã thêm câu hỏi.", "Question added."))
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    return render(request, "surveys/question_form.html", {"form": form, "survey": survey, "heading": say("Thêm câu hỏi", "Add Question")})


@manager_required
@portal_english
def question_edit(request, survey_id, question_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if (blocked := _draft_or_redirect(request, survey)):
        return blocked
    question = get_object_or_404(SurveyQuestion, pk=question_id, survey=survey)
    form = localize_form(QuestionForm(request.POST or None, instance=question))
    if request.method == "POST" and form.is_valid():
        if (blocked := _save_question(request, form, survey)):
            return blocked
        messages.success(request, say("Đã cập nhật câu hỏi.", "Question updated."))
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    return render(request, "surveys/question_form.html", {"form": form, "survey": survey, "heading": say("Sửa câu hỏi", "Edit Question")})


@manager_required
@require_POST
@portal_english
def question_delete(request, survey_id, question_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if (blocked := _draft_or_redirect(request, survey)):
        return blocked
    if survey.template_key == TEMPLATE_KEY:
        return HttpResponseBadRequest("Giữ đủ 8 câu của phiên bản khảo sát.")
    get_object_or_404(SurveyQuestion, pk=question_id, survey=survey).delete()
    messages.success(request, say("Đã xóa câu hỏi.", "Question deleted."))
    return redirect("surveys:manage_detail", survey_id=survey.pk)


@manager_required
@require_POST
@portal_english
def question_move(request, survey_id, question_id, direction):
    survey = get_object_or_404(Survey, pk=survey_id)
    if (blocked := _draft_or_redirect(request, survey)):
        return blocked
    if survey.template_key == TEMPLATE_KEY:
        return HttpResponseBadRequest("Giữ đúng thứ tự 8 câu của phiên bản khảo sát.")
    questions = list(SurveyQuestion.objects.filter(survey=survey).order_by("sort_order", "question_id"))
    index = next((i for i, q in enumerate(questions) if q.pk == question_id), None)
    if index is not None:
        other = index - 1 if direction == "up" else index + 1
        if 0 <= other < len(questions):
            questions[index], questions[other] = questions[other], questions[index]
        for position, question in enumerate(questions, start=1):  # renumber so sort_order never collides
            if question.sort_order != position:
                question.sort_order = position
                question.save(update_fields=["sort_order"])
    return redirect("surveys:manage_detail", survey_id=survey.pk)


@manager_required
@portal_english
def manage_send(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    errors = [_send_error(e) for e in check_ready_to_send(survey)]
    form = localize_form(AudienceForm(request.POST or None))
    preview = None
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        if data["audience"] == "pick":
            customers = eligible_customers().filter(customer_id__in=data["customer_ids"])
        else:
            customers = filter_customers(data["audience"], data["age_groups"],
                                         data["playing_levels"], data["preferences"])
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
@portal_english
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
@portal_english
def manage_clone(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    copy = clone_survey(request.user, survey)
    messages.success(request, say("Đã tạo bản sao Nháp. Hãy kiểm tra thời gian và nội dung trước khi gửi.",
                                  "Draft copy created. Check its schedule and content before sending."))
    return redirect("surveys:manage_detail", survey_id=copy.pk)


@manager_required
@require_GET
@portal_english
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

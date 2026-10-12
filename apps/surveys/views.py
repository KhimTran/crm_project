import json

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from django.db.models import Count, Q

from apps.accounts.decorators import role_required
from apps.accounts.errors import AccountPermissionDenied
from apps.accounts.permissions import account_admin_required
from apps.customers.models import Customer
from .constants import RECIPIENT_COMPLETED, SurveyStatus
from .forms import AudienceForm, QuestionForm, SurveyForm
from .models import Survey, SurveyQuestion, SurveyRecipient
from .services import (COMPLETED_MESSAGE, build_stats, check_ready_to_send, close_expired, close_survey,
                       filter_customers, is_survey_open, recipient_for_user, send_survey, send_to_audience,
                       start_survey, submit_survey)

manager_required = role_required("ADMIN", "CRM_MANAGER")


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
    questions = SurveyQuestion.objects.filter(survey=response.recipient.survey).prefetch_related("surveyoption_set").order_by("sort_order", "question_id")
    return render(request, "surveys/take.html", {"response": response, "questions": questions})


@require_POST
def submit(request, recipient_id):
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
        return HttpResponseBadRequest(str(exc))
    messages.success(request, "Đã gửi câu trả lời." if submitted else COMPLETED_MESSAGE)
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
def _draft_or_redirect(request, survey):
    if survey.status != SurveyStatus.DRAFT:
        messages.error(request, "Chỉ sửa được khảo sát ở trạng thái Nháp.")
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    return None


@manager_required
@require_GET
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
    return render(request, "surveys/manage_list.html",
                  {"surveys": qs, "status": status, "q": q, "statuses": SurveyStatus.choices})


@manager_required
def manage_create(request):
    form = SurveyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        survey = form.save(commit=False)
        survey.created_by = request.user
        survey.status = SurveyStatus.DRAFT
        survey.save()
        messages.success(request, "Đã tạo khảo sát. Hãy thêm câu hỏi.")
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    return render(request, "surveys/manage_form.html", {"form": form, "heading": "Tạo khảo sát mới"})


@manager_required
def manage_edit(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if (blocked := _draft_or_redirect(request, survey)):
        return blocked
    form = SurveyForm(request.POST or None, instance=survey)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật khảo sát.")
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    return render(request, "surveys/manage_form.html", {"form": form, "heading": "Sửa khảo sát"})


@manager_required
@require_POST
def manage_delete(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if survey.status != SurveyStatus.DRAFT or SurveyRecipient.objects.filter(survey=survey).exists():
        messages.error(request, "Chỉ xóa được khảo sát Nháp chưa gửi cho ai. Hãy dùng \"Đóng khảo sát\".")
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    survey.delete()
    messages.success(request, "Đã xóa khảo sát.")
    return redirect("surveys:manage_list")


@manager_required
@require_GET
def manage_detail(request, survey_id):
    close_expired()
    survey = get_object_or_404(Survey, pk=survey_id)
    questions = SurveyQuestion.objects.filter(survey=survey).prefetch_related("surveyoption_set") \
        .order_by("sort_order", "question_id")
    recipients = SurveyRecipient.objects.filter(survey=survey)
    return render(request, "surveys/manage_detail.html", {
        "survey": survey, "questions": questions, "is_draft": survey.status == SurveyStatus.DRAFT,
        "sent": recipients.count(), "done": recipients.filter(status=RECIPIENT_COMPLETED).count()})


@manager_required
def question_add(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if (blocked := _draft_or_redirect(request, survey)):
        return blocked
    form = QuestionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save_for(survey)
        messages.success(request, "Đã thêm câu hỏi.")
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    return render(request, "surveys/question_form.html", {"form": form, "survey": survey, "heading": "Thêm câu hỏi"})


@manager_required
def question_edit(request, survey_id, question_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if (blocked := _draft_or_redirect(request, survey)):
        return blocked
    question = get_object_or_404(SurveyQuestion, pk=question_id, survey=survey)
    form = QuestionForm(request.POST or None, instance=question)
    if request.method == "POST" and form.is_valid():
        form.save_for(survey)
        messages.success(request, "Đã cập nhật câu hỏi.")
        return redirect("surveys:manage_detail", survey_id=survey.pk)
    return render(request, "surveys/question_form.html", {"form": form, "survey": survey, "heading": "Sửa câu hỏi"})


@manager_required
@require_POST
def question_delete(request, survey_id, question_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if (blocked := _draft_or_redirect(request, survey)):
        return blocked
    get_object_or_404(SurveyQuestion, pk=question_id, survey=survey).delete()
    messages.success(request, "Đã xóa câu hỏi.")
    return redirect("surveys:manage_detail", survey_id=survey.pk)


@manager_required
@require_POST
def question_move(request, survey_id, question_id, direction):
    survey = get_object_or_404(Survey, pk=survey_id)
    if (blocked := _draft_or_redirect(request, survey)):
        return blocked
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
def manage_send(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    errors = check_ready_to_send(survey)
    form = AudienceForm(request.POST or None)
    preview = None
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        customers = filter_customers(data["audience"], data["age_groups"],
                                     data["playing_levels"], data["preferences"])
        if request.POST.get("action") == "send" and not errors:
            try:
                result = send_to_audience(request.user, survey, customers)
            except (AccountPermissionDenied, ValidationError) as exc:
                messages.error(request, str(exc))
                return redirect("surveys:manage_detail", survey_id=survey.pk)
            note = f" (bỏ qua {result['skipped']} người đã nhận trước đó)" if result["skipped"] else ""
            messages.success(request, f"Đã gửi khảo sát cho {result['created']} khách hàng{note}.")
            return redirect("surveys:manage_detail", survey_id=survey.pk)
        preview = customers.count()
    return render(request, "surveys/manage_send.html",
                  {"survey": survey, "form": form, "errors": errors, "preview": preview})


@manager_required
@require_POST
def manage_close(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    close_survey(request.user, survey)
    messages.success(request, "Đã đóng khảo sát.")
    return redirect("surveys:manage_detail", survey_id=survey.pk)


@manager_required
@require_GET
def manage_stats(request, survey_id):
    close_expired()
    survey = get_object_or_404(Survey, pk=survey_id)
    return render(request, "surveys/manage_stats.html", {"survey": survey, "stats": build_stats(survey)})


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
        for recipient in rows:
            if recipient.status == RECIPIENT_COMPLETED:
                done.append(recipient)
            elif is_survey_open(recipient.survey):
                todo.append(recipient)
            else:
                closed.append(recipient)  # closed, expired or not yet open
    return render(request, "surveys/my_surveys.html", {"todo": todo, "done": done, "closed": closed})

import json

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.permissions import account_admin_required
from .models import Survey, SurveyQuestion, SurveyRecipient
from .services import COMPLETED_MESSAGE, recipient_for_user, send_survey, start_survey, submit_survey


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

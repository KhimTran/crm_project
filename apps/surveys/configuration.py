"""Stored question settings and creation of an independent questionnaire version."""
from django.core.exceptions import ValidationError
from django.db import transaction

from .constants import QuestionType, SurveyStatus
from .models import Survey, SurveyOption, SurveyQuestion
from .questionnaire import TEMPLATE_KEY, question_definitions


def rating_bounds(question):
    config = question.config or {}
    low, high = config.get("rating_min", 1), config.get("rating_max", 5)
    if type(low) is not int or type(high) is not int or not 1 <= low < high <= 10:
        raise ValidationError("Cấu hình thang điểm không hợp lệ.")
    return low, high


@transaction.atomic
def populate_questionnaire(survey):
    """Only populate a new, empty draft; never overwrite a previous questionnaire."""
    locked = Survey.objects.select_for_update().get(pk=survey.pk)
    if locked.status != SurveyStatus.DRAFT or locked.surveyquestion_set.exists() or locked.surveyrecipient_set.exists():
        raise ValidationError("Chỉ áp dụng bộ câu hỏi cho khảo sát Nháp mới, chưa có câu hỏi hoặc người nhận.")
    locked.template_key = TEMPLATE_KEY
    locked.save(update_fields=["template_key", "updated_at"])
    survey.template_key = TEMPLATE_KEY
    for position, definition in enumerate(question_definitions(), 1):
        option_texts = definition.pop("options", [])
        other_index = definition.pop("other_option_index", None)
        text, kind = definition.pop("question_text"), definition.pop("question_type")
        required = definition.pop("is_required", True)
        question = SurveyQuestion.objects.create(
            survey=survey, question_text=text, question_type=kind,
            sort_order=position, is_required=required, config=definition,
        )
        options = [SurveyOption.objects.create(question=question, option_text=label, sort_order=i)
                   for i, label in enumerate(option_texts, 1)]
        if other_index is not None:
            question.config["other_option_id"] = options[other_index].pk
            question.save(update_fields=["config"])


def prepare_questions(questions):
    """Add presentation values without mutating question text or stored settings."""
    previous_section = None
    for question in questions:
        config = question.config or {}
        section = config.get("section", "")
        question.section_heading = section if section != previous_section else ""
        previous_section = section
        question.other_option_id = config.get("other_option_id")
        question.max_selections = config.get("max_selections")
        question.placeholder = config.get("placeholder", "")
        if question.question_type == QuestionType.RATING:
            low, high = rating_bounds(question)
            question.rating_values = range(low, high + 1)
            question.rating_min, question.rating_max = low, high
            question.rating_min_label = config.get("rating_min_label", "")
            question.rating_max_label = config.get("rating_max_label", "")
        question.matrix_values = range(1, 6)
    return questions

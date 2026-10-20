from datetime import datetime, time

from django import forms
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .constants import AGE_GROUPS, CHOICE_TYPES, QuestionType, SurveyObjective
from .questionnaire import TEMPLATE_KEY, question_definitions
from .models import Survey, SurveyOption, SurveyQuestion
from .services import eligible_customers, playing_level_choices, preference_choices
from apps.customers.portal_text import say

DT_FORMAT = "%Y-%m-%dT%H:%M"


# Form for survey builder (create/edit): select dates (start 00:00, end 23:59:59 local time)
class SurveyBuilderForm(forms.ModelForm):
    DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", DT_FORMAT, "%Y-%m-%d %H:%M"]

    objective = forms.ChoiceField(label="Survey Objective", choices=[("", "-- Select objective --"), *SurveyObjective.choices])
    start_at = forms.DateField(label="Start Date", input_formats=DATE_FORMATS,
                               widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    end_at = forms.DateField(label="End Date", input_formats=DATE_FORMATS,
                             widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))

    class Meta:
        model = Survey
        fields = ["title", "objective", "description"]
        widgets = {"title": forms.TextInput(attrs={"maxlength": 200}), "description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        texts = {"title": ("Tiêu đề khảo sát", "Survey Title", "Nhập tiêu đề khảo sát", "Enter the survey title"),
                 "objective": ("Mục tiêu khảo sát", "Survey Objective", None, None),
                 "description": ("Mô tả", "Description", "Nhập mô tả chi tiết về khảo sát...",
                                 "Describe the survey in detail..."),
                 "start_at": ("Thời gian bắt đầu", "Start Date", None, None),
                 "end_at": ("Thời gian kết thúc", "End Date", None, None)}
        for name, (vi, en, hint_vi, hint_en) in texts.items():
            self.fields[name].label = say(vi, en)
            if hint_vi:
                self.fields[name].widget.attrs["placeholder"] = say(hint_vi, hint_en)
        self.fields["objective"].choices = [("", say("-- Chọn mục tiêu --", "-- Select an objective --"))] + [
            (value, say(label, english)) for (value, label), english in zip(
                SurveyObjective.choices, ["Customer satisfaction", "New product research", "Shopping needs", "Other"])]
        for name in ("start_at", "end_at"):
            value = getattr(self.instance, name)
            if value:
                self.initial[name] = timezone.localtime(value).date()

    def clean(self):
        data = super().clean()
        start, end = data.get("start_at"), data.get("end_at")
        if start and not self.instance.pk and start < timezone.localdate():
            self.add_error("start_at", "The start date cannot be in the past.")
        if start and end and end < start:
            self.add_error("end_at", "The end date must be on or after the start date.")
        return data

    def save(self, commit=True):
        survey = super().save(commit=False)
        zone = timezone.get_current_timezone()
        survey.start_at = timezone.make_aware(datetime.combine(self.cleaned_data["start_at"], time.min), zone)
        survey.end_at = timezone.make_aware(datetime.combine(self.cleaned_data["end_at"], time.max), zone)
        if commit:
            survey.save()
        return survey


class QuestionForm(forms.ModelForm):
    question_type = forms.ChoiceField(label="Question Type", choices=QuestionType.choices)
    options_text = forms.CharField(
        label="Options (one per line)", required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
        help_text="Required for single/multiple choice questions.")
    section = forms.CharField(label="Section", max_length=200, required=False)
    max_selections = forms.IntegerField(label="Maximum Selections", min_value=1, required=False)
    rating_min = forms.IntegerField(label="Minimum Score", min_value=1, max_value=9, initial=1, required=False)
    rating_max = forms.IntegerField(label="Maximum Score", min_value=2, max_value=10, initial=5, required=False)
    other_option_position = forms.IntegerField(label="Other Option Position", min_value=1, required=False,
                                              help_text="Leave empty if there is no Other option.")
    placeholder = forms.CharField(label="Input Hint", max_length=255, required=False)

    class Meta:
        model = SurveyQuestion
        fields = ["question_text", "question_type", "is_required"]
        labels = {"question_text": "Question Text", "is_required": "Required"}
        widgets = {"question_text": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["question_type"].choices = [
            (value, say("Thang điểm (theo cấu hình)", "Rating (configured scale)")) if value == QuestionType.RATING else
            (value, say("Đánh giá theo tiêu chí", "Matrix (criteria)")) if value == QuestionType.MATRIX else (value, label)
            for value, label in QuestionType.choices]
        for name, english in {"section": "Content section", "max_selections": "Maximum selections",
                              "rating_min": "Minimum score", "rating_max": "Maximum score",
                              "other_option_position": "Other option position", "placeholder": "Input hint"}.items():
            self.fields[name].label = say(self.fields[name].label, english)
            if name in ("max_selections", "rating_min", "rating_max", "other_option_position"):
                self.fields[name].widget = forms.TextInput(attrs={"inputmode": "numeric", "pattern": "[0-9]*"})
        if self.instance.pk:
            config = self.instance.config or {}
            for name in ("section", "max_selections", "rating_min", "rating_max", "placeholder"):
                if name in config:
                    self.initial[name] = config[name]
            options = list(SurveyOption.objects.filter(question=self.instance).order_by("sort_order", "option_id"))
            self.initial["other_option_position"] = next(
                (pos for pos, opt in enumerate(options, 1) if opt.pk == config.get("other_option_id")), None)
            self.initial["options_text"] = "\n".join(opt.option_text for opt in options)
            if self.instance.survey.template_key == TEMPLATE_KEY:
                self.fields["question_type"].disabled = True
                self.fields["options_text"].disabled = True
                if (config.get("rating_max") or 5) != 5:
                    self.fields["rating_max"].disabled = True
                self.fields["other_option_position"].disabled = True

    def clean(self):
        data = super().clean()
        kind = data.get("question_type")
        if kind in (*CHOICE_TYPES, QuestionType.MATRIX):
            lines = [line.strip() for line in (data.get("options_text") or "").splitlines() if line.strip()]
            options = list(dict.fromkeys(lines))  # drop duplicates, keep order
            if len(options) < 2:
                self.add_error("options_text", "Please enter at least 2 distinct options.")
            if any(len(o) > 255 for o in options):
                self.add_error("options_text", "Each option must be at most 255 characters.")
            data["option_list"] = options
        else:
            data["option_list"] = []
        low, high = data.get("rating_min") or 1, data.get("rating_max") or 5
        if kind == QuestionType.RATING and low >= high:
            self.add_error("rating_max", "Highest score must be greater than lowest score.")
        maximum = data.get("max_selections")
        if kind == QuestionType.MULTI_CHOICE and maximum and maximum > len(data["option_list"]):
            self.add_error("max_selections", "Maximum selections must be between 1 and the number of options.")
        other = data.get("other_option_position")
        if other and (kind not in CHOICE_TYPES or other > len(data["option_list"])):
            self.add_error("other_option_position", "Other option position must be within the list of options.")
        if self.instance.pk and self.instance.survey.template_key == TEMPLATE_KEY:
            definition = next((q for q in question_definitions() if q["key"] == self.instance.config.get("key")), None)
            if definition:
                if kind != definition["question_type"]:
                    self.add_error("question_type", "Keep question type from the 8-question template; create a new survey to change semantics.")
                if definition.get("is_required") is False and data.get("is_required"):
                    self.add_error("is_required", "Feedback question must be optional.")
                if len(data["option_list"]) != len(definition.get("options", [])):
                    self.add_error("options_text", "Keep the number of options / criteria for this survey version.")
                if "max_selections" in definition:
                    data["max_selections"] = definition["max_selections"]
                if "rating_max" in definition:
                    data["rating_min"], data["rating_max"] = definition["rating_min"], definition["rating_max"]
                data["section"] = definition["section"]
                if "other_option_index" in definition and not other:
                    self.add_error("other_option_position", "Brand question must have an Other option.")
        return data

    @transaction.atomic
    def save_for(self, survey):
        survey = Survey.objects.select_for_update().get(pk=survey.pk)
        if (survey.status != "DRAFT" or survey.surveyrecipient_set.exists()
                or survey.surveyquestion_set.filter(surveyanswer__isnull=False).exists()):
            raise forms.ValidationError("Cannot edit questions for a survey that has been sent or has responses.")
        question = self.save(commit=False)
        old_config = dict(question.config or {})
        question.survey = survey
        if not question.pk:
            current = SurveyQuestion.objects.filter(survey=survey).aggregate(m=Max("sort_order"))["m"]
            question.sort_order = (current or 0) + 1
        question.save()
        SurveyOption.objects.filter(question=question).delete()
        options = [SurveyOption.objects.create(question=question, option_text=text, sort_order=i)
                   for i, text in enumerate(self.cleaned_data["option_list"], start=1)]
        data = self.cleaned_data
        config = {k: v for k, v in {"section": data.get("section") or "",
                                    "max_selections": data.get("max_selections"),
                                    "rating_min": data.get("rating_min"),
                                    "rating_max": data.get("rating_max"),
                                    "placeholder": data.get("placeholder") or ""}.items() if v is not None}
        if "key" in old_config:
            config["key"] = old_config["key"]
        pos = data.get("other_option_position")
        if pos and 1 <= pos <= len(options):
            config["other_option_id"] = options[pos - 1].pk
        question.config = config
        question.save(update_fields=["config"])
        return question


class AudienceFilterForm(forms.Form):
    AUDIENCE_CHOICES = [
        ("all", "Tất cả khách hàng đủ điều kiện"),
        ("filter", "Lọc theo nhóm tuổi, trình độ hoặc sở thích"),
        ("pick", "Chọn từng khách hàng cụ thể"),
    ]

    audience = forms.ChoiceField(
        choices=AUDIENCE_CHOICES, widget=forms.RadioSelect, initial="all",
        label="Phạm vi đối tượng",
    )
    age_groups = forms.MultipleChoiceField(
        choices=AGE_GROUPS, required=False, widget=forms.CheckboxSelectMultiple,
        label="Nhóm tuổi",
    )
    playing_levels = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple, label="Trình độ chơi",
    )
    preferences = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple, label="Sở thích sản phẩm",
    )
    customer_ids = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple, label="Khách hàng",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["playing_levels"].choices = playing_level_choices()
        self.fields["preferences"].choices = preference_choices()
        self.fields["customer_ids"].choices = [
            (c.customer_id, f"{c.full_name} – {c.account.email}")
            for c in eligible_customers().select_related("account").order_by("full_name", "customer_id")]

    def clean(self):
        data = super().clean()
        if data.get("audience") == "filter" and not (
                data.get("age_groups") or data.get("playing_levels") or data.get("preferences")):
            raise forms.ValidationError('Please choose at least one filter criterion, or select "All".')
        if data.get("audience") == "pick" and not data.get("customer_ids"):
            raise forms.ValidationError("Please select at least one customer.")
        return data

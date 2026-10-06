from django import forms
from django.db import transaction
from django.db.models import Max

from .constants import AGE_GROUPS, CHOICE_TYPES, QuestionType
from .models import Survey, SurveyOption, SurveyQuestion
from .services import playing_level_choices, preference_choices

DT_FORMAT = "%Y-%m-%dT%H:%M"


class SurveyForm(forms.ModelForm):
    start_at = forms.DateTimeField(label="Mở từ", input_formats=[DT_FORMAT, "%Y-%m-%d %H:%M"],
                                   widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DT_FORMAT))
    end_at = forms.DateTimeField(label="Đóng lúc", input_formats=[DT_FORMAT, "%Y-%m-%d %H:%M"],
                                 widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DT_FORMAT))

    class Meta:
        model = Survey
        fields = ["title", "description", "start_at", "end_at"]
        labels = {"title": "Tiêu đề", "description": "Mô tả"}
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        data = super().clean()
        start, end = data.get("start_at"), data.get("end_at")
        if start and end and end <= start:
            self.add_error("end_at", "Thời điểm đóng phải sau thời điểm mở.")
        return data


class QuestionForm(forms.ModelForm):
    question_type = forms.ChoiceField(label="Loại câu hỏi", choices=QuestionType.choices)
    options_text = forms.CharField(
        label="Các lựa chọn (mỗi dòng một lựa chọn)", required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
        help_text="Chỉ cần cho câu hỏi một/nhiều lựa chọn.")

    class Meta:
        model = SurveyQuestion
        fields = ["question_text", "question_type", "is_required"]
        labels = {"question_text": "Nội dung câu hỏi", "is_required": "Bắt buộc trả lời"}
        widgets = {"question_text": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["options_text"] = "\n".join(
                SurveyOption.objects.filter(question=self.instance)
                .order_by("sort_order", "option_id").values_list("option_text", flat=True))

    def clean(self):
        data = super().clean()
        if data.get("question_type") in CHOICE_TYPES:
            lines = [line.strip() for line in (data.get("options_text") or "").splitlines() if line.strip()]
            options = list(dict.fromkeys(lines))  # drop duplicates, keep order
            if len(options) < 2:
                self.add_error("options_text", "Cần nhập ít nhất 2 lựa chọn khác nhau.")
            if any(len(o) > 255 for o in options):
                self.add_error("options_text", "Mỗi lựa chọn tối đa 255 ký tự.")
            data["option_list"] = options
        else:
            data["option_list"] = []
        return data

    @transaction.atomic
    def save_for(self, survey):
        """Only DRAFT surveys are edited, so options have no answers yet and can be rebuilt."""
        question = self.save(commit=False)
        question.survey = survey
        if not question.pk:
            current = SurveyQuestion.objects.filter(survey=survey).aggregate(m=Max("sort_order"))["m"]
            question.sort_order = (current or 0) + 1
        question.save()
        SurveyOption.objects.filter(question=question).delete()
        SurveyOption.objects.bulk_create([
            SurveyOption(question=question, option_text=text, sort_order=i)
            for i, text in enumerate(self.cleaned_data["option_list"], start=1)])
        return question


class AudienceForm(forms.Form):
    audience = forms.ChoiceField(
        label="Đối tượng nhận", initial="all", widget=forms.RadioSelect,
        choices=[("all", "Tất cả khách hàng đang hoạt động"),
                 ("filter", "Lọc theo nhóm tuổi / trình độ / sở thích")])
    age_groups = forms.MultipleChoiceField(
        label="Nhóm tuổi", required=False, widget=forms.CheckboxSelectMultiple,
        choices=[(key, label) for key, label, _lo, _hi in AGE_GROUPS])
    playing_levels = forms.MultipleChoiceField(
        label="Trình độ chơi", required=False, widget=forms.CheckboxSelectMultiple, choices=[])
    preferences = forms.MultipleChoiceField(
        label="Sở thích", required=False, widget=forms.CheckboxSelectMultiple, choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # choices come from real data, so no enum has to be guessed
        self.fields["playing_levels"].choices = playing_level_choices()
        self.fields["preferences"].choices = preference_choices()

    def clean(self):
        data = super().clean()
        if data.get("audience") == "filter" and not (
                data.get("age_groups") or data.get("playing_levels") or data.get("preferences")):
            raise forms.ValidationError('Hãy chọn ít nhất một điều kiện lọc, hoặc chọn "Tất cả".')
        return data

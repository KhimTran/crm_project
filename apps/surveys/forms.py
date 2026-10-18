from django import forms
from django.db import transaction
from django.db.models import Max

from .constants import AGE_GROUPS, CHOICE_TYPES, QuestionType
from .questionnaire import TEMPLATE_KEY, question_definitions
from .models import Survey, SurveyOption, SurveyQuestion
from .services import eligible_customers, playing_level_choices, preference_choices
from apps.customers.portal_text import say

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


# tv4: form tạo khảo sát: bộ 8 câu chỉ là mẫu tùy chọn, bỏ tích thì tạo khảo sát trống để tự thêm câu hỏi
class SurveyCreateForm(SurveyForm):
    use_template = forms.BooleanField(
        label="Dùng bộ câu hỏi mẫu 8 câu", initial=True, required=False,
        help_text="Bỏ chọn để tạo khảo sát trống và tự thêm câu hỏi.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["use_template"].label = say(self.fields["use_template"].label, "Use the 8-question template")
        self.fields["use_template"].help_text = say(self.fields["use_template"].help_text,
                                                    "Untick to create an empty survey and add your own questions.")


class QuestionForm(forms.ModelForm):
    question_type = forms.ChoiceField(label="Loại câu hỏi", choices=QuestionType.choices)
    options_text = forms.CharField(
        label="Các lựa chọn (mỗi dòng một lựa chọn)", required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
        help_text="Chỉ cần cho câu hỏi một/nhiều lựa chọn.")
    section = forms.CharField(label="Nhóm nội dung", max_length=200, required=False)
    max_selections = forms.IntegerField(label="Số lựa chọn tối đa", min_value=1, required=False)
    rating_min = forms.IntegerField(label="Điểm thấp nhất", min_value=1, max_value=9, initial=1, required=False)
    rating_max = forms.IntegerField(label="Điểm cao nhất", min_value=2, max_value=10, initial=5, required=False)
    other_option_position = forms.IntegerField(label="Vị trí lựa chọn Khác", min_value=1, required=False,
                                              help_text="Để trống nếu không có lựa chọn Khác.")
    placeholder = forms.CharField(label="Gợi ý nhập nội dung", max_length=255, required=False)

    class Meta:
        model = SurveyQuestion
        fields = ["question_text", "question_type", "is_required"]
        labels = {"question_text": "Nội dung câu hỏi", "is_required": "Bắt buộc trả lời"}
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
                (i for i, o in enumerate(options, 1) if o.pk == config.get("other_option_id")), None)
            self.initial["options_text"] = "\n".join(
                SurveyOption.objects.filter(question=self.instance)
                .order_by("sort_order", "option_id").values_list("option_text", flat=True))
            if self.instance.survey.template_key == TEMPLATE_KEY:
                for name in ("question_type", "section", "max_selections", "rating_min", "rating_max"):
                    self.fields[name].disabled = True
                if self.instance.config.get("key") == "suggestions":
                    self.fields["is_required"].disabled = True
                self.fields["other_option_position"].disabled = True

    def clean(self):
        data = super().clean()
        kind = data.get("question_type")
        if kind in (*CHOICE_TYPES, QuestionType.MATRIX):
            lines = [line.strip() for line in (data.get("options_text") or "").splitlines() if line.strip()]
            options = list(dict.fromkeys(lines))  # drop duplicates, keep order
            if len(options) < 2:
                self.add_error("options_text", "Cần nhập ít nhất 2 lựa chọn khác nhau.")
            if any(len(o) > 255 for o in options):
                self.add_error("options_text", "Mỗi lựa chọn tối đa 255 ký tự.")
            data["option_list"] = options
        else:
            data["option_list"] = []
        low, high = data.get("rating_min") or 1, data.get("rating_max") or 5
        if kind == QuestionType.RATING and low >= high:
            self.add_error("rating_max", "Điểm cao nhất phải lớn hơn điểm thấp nhất.")
        other = data.get("other_option_position")
        if other and (kind not in CHOICE_TYPES or other > len(data["option_list"])):
            self.add_error("other_option_position", "Vị trí Khác phải thuộc danh sách lựa chọn của câu hỏi.")
        if self.instance.pk and self.instance.survey.template_key == TEMPLATE_KEY:
            definition = next((q for q in question_definitions() if q["key"] == self.instance.config.get("key")), None)
            if definition:
                if kind != definition["question_type"]:
                    self.add_error("question_type", "Giữ loại câu hỏi của bộ 8 câu; hãy tạo khảo sát mới khi đổi ý nghĩa.")
                if definition.get("is_required") is False and data.get("is_required"):
                    self.add_error("is_required", "Câu góp ý phải không bắt buộc.")
                if len(data["option_list"]) != len(definition.get("options", [])):
                    self.add_error("options_text", "Giữ số lựa chọn / tiêu chí của phiên bản khảo sát này.")
                # Fixed semantic settings for this version; required flags 1–7 remain editable.
                if "max_selections" in definition:
                    data["max_selections"] = definition["max_selections"]
                if "rating_max" in definition:
                    data["rating_min"], data["rating_max"] = definition["rating_min"], definition["rating_max"]
                data["section"] = definition["section"]
                if "other_option_index" in definition and not other:
                    self.add_error("other_option_position", "Câu thương hiệu phải có lựa chọn Khác.")
        return data

    @transaction.atomic
    def save_for(self, survey):
        """Only DRAFT surveys are edited, so options have no answers yet and can be rebuilt."""
        survey = Survey.objects.select_for_update().get(pk=survey.pk)
        if (survey.status != "DRAFT" or survey.surveyrecipient_set.exists()
                or survey.surveyquestion_set.filter(surveyanswer__isnull=False).exists()):
            raise forms.ValidationError("Không sửa câu hỏi của khảo sát đã gửi hoặc đã có câu trả lời.")
        question = self.save(commit=False)
        question.survey = survey
        if not question.pk:
            current = SurveyQuestion.objects.filter(survey=survey).aggregate(m=Max("sort_order"))["m"]
            question.sort_order = (current or 0) + 1
        question.save()
        SurveyOption.objects.filter(question=question).delete()
        options = [SurveyOption.objects.create(question=question, option_text=text, sort_order=i)
                   for i, text in enumerate(self.cleaned_data["option_list"], start=1)]
        data = self.cleaned_data
        config = {"key": (question.config or {}).get("key", ""), "section": data.get("section", "")}
        if question.question_type == QuestionType.RATING:
            config.update(rating_min=data.get("rating_min") or 1, rating_max=data.get("rating_max") or 5)
        if question.question_type == QuestionType.MULTI_CHOICE and data.get("max_selections"):
            config["max_selections"] = data["max_selections"]
        if data.get("other_option_position"):
            config["other_option_id"] = options[data["other_option_position"] - 1].pk
        if data.get("placeholder"):
            config["placeholder"] = data["placeholder"]
        question.config = config
        question.save(update_fields=["config"])
        return question


class AudienceForm(forms.Form):
    audience = forms.ChoiceField(
        label="Đối tượng nhận", initial="all", widget=forms.RadioSelect,
        choices=[("all", "Tất cả khách hàng đang hoạt động"),
                 ("filter", "Lọc theo nhóm tuổi / trình độ / sở thích"),
                 ("pick", "Chọn từng khách hàng")])
    customer_ids = forms.TypedMultipleChoiceField(
        label="Khách hàng", required=False, coerce=int, widget=forms.CheckboxSelectMultiple, choices=[])
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
        # chỉ liệt kê khách đủ điều kiện nhận (chưa xóa, tài khoản không bị khóa)
        self.fields["customer_ids"].choices = [
            (c.customer_id, f"{c.full_name} – {c.account.email}")
            for c in eligible_customers().select_related("account").order_by("full_name", "customer_id")]

    def clean(self):
        data = super().clean()
        if data.get("audience") == "filter" and not (
                data.get("age_groups") or data.get("playing_levels") or data.get("preferences")):
            raise forms.ValidationError('Hãy chọn ít nhất một điều kiện lọc, hoặc chọn "Tất cả".')
        if data.get("audience") == "pick" and not data.get("customer_ids"):
            raise forms.ValidationError("Hãy chọn ít nhất một khách hàng.")
        return data

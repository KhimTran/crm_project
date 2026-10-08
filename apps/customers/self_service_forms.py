import re

from django import forms
from django.utils import timezone

from apps.catalog.models import Category, Status
from .models import Customer
from .self_service_choices import CATEGORY_PREFERENCE_TYPE, GENDER_CHOICES, PLAYING_LEVEL_CHOICES


class CustomerProfileForm(forms.ModelForm):
    gender = forms.ChoiceField(label="Giới tính", required=False)
    playing_level = forms.ChoiceField(label="Trình độ chơi", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field, choices in (("gender", GENDER_CHOICES), ("playing_level", PLAYING_LEVEL_CHOICES)):
            options = [("", "Chưa chọn"), *choices]
            saved = getattr(self.instance, field, None)
            if saved and saved not in dict(options):
                options.append((saved, f"Đã lưu: {saved}"))
            self.fields[field].choices = options
            self.fields[field].help_text = "Bạn có thể giữ lựa chọn đã lưu hoặc chọn lại."

    def _optional_choice(self, field):
        # An omitted field is not an explicit request to clear saved information.
        if field not in self.data:
            return getattr(self.instance, field, None)
        return self.cleaned_data[field] or None

    def clean_gender(self):
        return self._optional_choice("gender")

    def clean_playing_level(self):
        return self._optional_choice("playing_level")

    class Meta:
        model = Customer
        fields = ("full_name", "phone", "date_of_birth", "gender", "address", "playing_level")
        labels = {
            "full_name": "Họ và tên", "phone": "Số điện thoại", "date_of_birth": "Ngày sinh",
            "gender": "Giới tính", "address": "Địa chỉ", "playing_level": "Trình độ chơi",
        }
        widgets = {"date_of_birth": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})}
        help_texts = {
            "phone": "Nhập 9–15 chữ số, có thể có dấu +, khoảng trắng hoặc dấu gạch nối.",
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone") or ""
        if phone and (not re.fullmatch(r"\+?[0-9 ()-]+", phone)
                      or not 9 <= len(re.sub(r"\D", "", phone)) <= 15):
            raise forms.ValidationError("Số điện thoại không hợp lệ.")
        return phone or None

    def clean_date_of_birth(self):
        date = self.cleaned_data.get("date_of_birth")
        if date and date > timezone.localdate():
            raise forms.ValidationError("Ngày sinh không được ở tương lai.")
        return date


class CustomerCategoryPreferencesForm(forms.Form):
    categories = forms.TypedMultipleChoiceField(
        label="Danh mục bạn quan tâm", required=False, coerce=int, widget=forms.CheckboxSelectMultiple,
    )
    remove_preferences = forms.TypedMultipleChoiceField(
        label="Sở thích đã lưu khác", required=False, coerce=int, widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, customer, *args, active_categories=None, preferences=None, **kwargs):
        super().__init__(*args, **kwargs)
        if active_categories is None:
            active_categories = Category.objects.filter(status=Status.ACTIVE).order_by("category_name", "category_id")
        self.active_categories = list(active_categories)
        if preferences is None:
            preferences = customer.customerpreference_set.filter(preference_type=CATEGORY_PREFERENCE_TYPE)
        preferences = list(preferences)
        active_names = {category.category_name for category in self.active_categories}
        saved_names = {preference.preference_value for preference in preferences}
        self.fields["categories"].choices = [(category.pk, category.category_name) for category in self.active_categories]
        self.fields["remove_preferences"].choices = [
            (preference.pk, preference.preference_value) for preference in preferences
            if preference.preference_value not in active_names
        ]
        self.initial["categories"] = [category.pk for category in self.active_categories if category.category_name in saved_names]

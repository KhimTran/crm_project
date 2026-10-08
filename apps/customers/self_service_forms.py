import re

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory
from django.utils import timezone

from .models import Customer, CustomerPreference


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ("full_name", "phone", "date_of_birth", "gender", "address", "playing_level")
        labels = {
            "full_name": "Họ và tên", "phone": "Số điện thoại", "date_of_birth": "Ngày sinh",
            "gender": "Giới tính", "address": "Địa chỉ", "playing_level": "Trình độ chơi",
        }
        widgets = {"date_of_birth": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})}
        help_texts = {
            "gender": "Thông tin tùy chọn; hiện chưa có danh sách lựa chọn cố định.",
            "playing_level": "Mô tả trình độ của bạn (tùy chọn).",
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


class CustomerPreferenceForm(forms.ModelForm):
    class Meta:
        model = CustomerPreference
        fields = ("preference_type", "preference_value")
        labels = {"preference_type": "Loại sở thích", "preference_value": "Nội dung sở thích"}
        help_texts = {
            "preference_type": "Quy ước hiện có: CATEGORY cho sở thích về danh mục.",
            "preference_value": "Với CATEGORY, nhập tên danh mục, ví dụ Badminton rackets.",
        }


class CustomerPreferenceBaseFormSet(BaseModelFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields["DELETE"].label = "Xóa sở thích này"


CustomerPreferenceFormSet = modelformset_factory(
    CustomerPreference, form=CustomerPreferenceForm, formset=CustomerPreferenceBaseFormSet, extra=1, can_delete=True,
    max_num=50, validate_max=True, absolute_max=100,
)

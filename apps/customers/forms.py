import re
from datetime import date

from django import forms

from apps.accounts.managers import AccountManager
from apps.accounts.models import Account

from .constants import BRAND_CHOICES, PLAY_STYLE_CHOICES, CustomerStatus, Gender, PlayingLevel
from .models import Customer

PHONE_PATTERN = re.compile(r"^(0|\+84)\d{9}$")


class CustomerCreateForm(forms.Form):
    full_name = forms.CharField(label="Họ tên", max_length=150, strip=True)
    email = forms.EmailField(label="Email", max_length=255)
    phone = forms.CharField(label="Số điện thoại", max_length=20, strip=True)
    date_of_birth = forms.DateField(label="Ngày sinh", required=False,
                                    widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    gender = forms.ChoiceField(label="Giới tính", required=False, choices=[("", "-- Chọn --"), *Gender.choices])
    address = forms.CharField(label="Địa chỉ", required=False, max_length=255, strip=True)
    playing_level = forms.ChoiceField(label="Trình độ chơi", required=False,
                                      choices=[("", "-- Chọn --"), *PlayingLevel.choices])
    play_styles = forms.MultipleChoiceField(label="Lối chơi", required=False, choices=PLAY_STYLE_CHOICES,
                                            widget=forms.CheckboxSelectMultiple)
    brands = forms.MultipleChoiceField(label="Thương hiệu yêu thích", required=False, choices=BRAND_CHOICES,
                                       widget=forms.CheckboxSelectMultiple)

    # tv4: chuẩn hóa email và chặn email đã có tài khoản
    def clean_email(self):
        email = AccountManager.normalize_account_email(self.cleaned_data["email"])
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError("Email đã được sử dụng.")
        return email

    # tv4: kiểm tra định dạng SĐT Việt Nam và chặn SĐT trùng với khách hàng chưa xóa
    def clean_phone(self):
        phone = self.cleaned_data["phone"].replace(" ", "")
        if not PHONE_PATTERN.match(phone):
            raise forms.ValidationError("Số điện thoại không hợp lệ (ví dụ 0901234567).")
        if Customer.objects.filter(phone=phone).exclude(status=CustomerStatus.DELETED).exists():
            raise forms.ValidationError("Số điện thoại đã được sử dụng.")
        return phone

    # tv4: chặn ngày sinh ở tương lai hoặc trước năm 1900
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob is not None and not (date(1900, 1, 1) <= dob <= date.today()):
            raise forms.ValidationError("Ngày sinh không hợp lệ.")
        return dob


class CustomerLockForm(forms.Form):
    # Schema không có cột lý do khóa nên lý do chỉ hiển thị trong thông báo, không lưu DB.
    reason = forms.CharField(label="Lý do khóa", required=False, max_length=255, strip=True)

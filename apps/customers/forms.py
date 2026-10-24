import re
from datetime import date

from django import forms
from django.contrib.auth.password_validation import password_validators_help_text_html, validate_password

from apps.accounts.managers import AccountManager
from apps.accounts.models import Account

from .constants import (
    AGE_GROUP_CHOICES, AccountStatusFilter, CustomerStatus, Gender, PlayingLevel,
)
from .models import Customer

PHONE_PATTERN = re.compile(r"^(0|\+84)\d{9}$")


# tv4: 4.1.1 form thêm khách hàng, kiểm tra SĐT / ngày sinh
class CustomerCreateForm(forms.Form):
    full_name = forms.CharField(label="Họ tên", max_length=150, strip=True)
    email = forms.EmailField(label="Email", max_length=255)
    password = forms.CharField(label="Mật khẩu", strip=False,
                               widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "crm-input"}))
    phone = forms.CharField(label="Số điện thoại", max_length=20, strip=True)
    date_of_birth = forms.DateField(label="Ngày sinh", required=False,
                                    widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    gender = forms.ChoiceField(label="Giới tính", required=False, choices=[("", "-- Chọn --"), *Gender.choices])
    address = forms.CharField(label="Địa chỉ", required=False, max_length=255, strip=True)
    playing_level = forms.ChoiceField(label="Trình độ chơi", required=False,
                                      choices=[("", "-- Chọn --"), *PlayingLevel.choices])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].help_text = password_validators_help_text_html()

    def clean(self):
        data = super().clean()
        if data.get("password"):
            try:
                validate_password(data["password"], Account(email=data.get("email", "")))
            except forms.ValidationError as exc:
                self.add_error("password", exc)
        return data

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


# tv4: 4.1.3 form nhập lý do khóa tài khoản
class CustomerLockForm(forms.Form):
    # Schema không có cột lý do khóa nên lý do chỉ hiển thị trong thông báo, không lưu DB.
    reason = forms.CharField(label="Lý do khóa", required=False, max_length=255, strip=True)


# tv4: form tìm kiếm / lọc danh sách khách hàng
class CustomerFilterForm(forms.Form):
    q = forms.CharField(label="Từ khóa", required=False, max_length=100, strip=True,
                        widget=forms.TextInput(attrs={"placeholder": "Tên, SĐT, email"}))
    age_group = forms.ChoiceField(label="Nhóm tuổi", required=False, choices=[("", "Tất cả"), *AGE_GROUP_CHOICES])
    gender = forms.ChoiceField(label="Giới tính", required=False, choices=[("", "Tất cả"), *Gender.choices])
    playing_level = forms.ChoiceField(label="Trình độ", required=False, choices=[("", "Tất cả"), *PlayingLevel.choices])
    account_status = forms.ChoiceField(label="Tài khoản", required=False,
                                       choices=[("", "Tất cả"), *AccountStatusFilter.choices])

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


class CustomerCreateForm(forms.Form):
    full_name = forms.CharField(label="Full Name", max_length=150, strip=True)
    email = forms.EmailField(label="Email", max_length=255)
    password = forms.CharField(label="Password", strip=False,
                               widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "crm-input"}))
    phone = forms.CharField(label="Phone", max_length=20, strip=True)
    date_of_birth = forms.DateField(label="Date of Birth", required=False,
                                    widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    gender = forms.ChoiceField(label="Gender", required=False, choices=[("", "-- Select --"), *Gender.choices])
    address = forms.CharField(label="Address", required=False, max_length=255, strip=True)
    playing_level = forms.ChoiceField(label="Playing Level", required=False,
                                      choices=[("", "-- Select --"), *PlayingLevel.choices])

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

    def clean_email(self):
        email = AccountManager.normalize_account_email(self.cleaned_data["email"])
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"].replace(" ", "")
        if not PHONE_PATTERN.match(phone):
            raise forms.ValidationError("Invalid phone number (e.g. 0901234567).")
        if Customer.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Phone number is already in use.")
        return phone

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob is not None and not (date(1900, 1, 1) <= dob <= date.today()):
            raise forms.ValidationError("Invalid date of birth.")
        return dob


class CustomerEditForm(forms.Form):
    full_name = forms.CharField(label="Full Name", max_length=150, strip=True, widget=forms.TextInput(attrs={"class": "crm-input"}))
    email = forms.EmailField(label="Email", max_length=255, widget=forms.EmailInput(attrs={"class": "crm-input"}))
    phone = forms.CharField(label="Phone", max_length=20, required=False, strip=True, widget=forms.TextInput(attrs={"class": "crm-input"}))
    date_of_birth = forms.DateField(label="Date of Birth", required=False,
                                    widget=forms.DateInput(attrs={"type": "date", "class": "crm-input"}, format="%Y-%m-%d"))
    gender = forms.ChoiceField(label="Gender", required=False, choices=[("", "-- Select --"), *Gender.choices],
                               widget=forms.Select(attrs={"class": "crm-select"}))
    address = forms.CharField(label="Address", required=False, max_length=255, strip=True, widget=forms.TextInput(attrs={"class": "crm-input"}))
    playing_level = forms.ChoiceField(label="Playing Level", required=False,
                                      choices=[("", "-- Select --"), *PlayingLevel.choices],
                                      widget=forms.Select(attrs={"class": "crm-select"}))

    def __init__(self, *args, customer_id=None, **kwargs):
        self.customer_id = customer_id
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = AccountManager.normalize_account_email(self.cleaned_data["email"])
        qs = Account.objects.filter(email=email)
        if self.customer_id:
            qs = qs.exclude(pk=self.customer_id)
        if qs.exists():
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        if not phone:
            return ""
        phone = phone.replace(" ", "")
        if not PHONE_PATTERN.match(phone):
            raise forms.ValidationError("Invalid phone number (e.g. 0901234567).")
        qs = Customer.objects.filter(phone=phone)
        if self.customer_id:
            qs = qs.exclude(pk=self.customer_id)
        if qs.exists():
            raise forms.ValidationError("Phone number is already in use.")
        return phone

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob is not None and not (date(1900, 1, 1) <= dob <= date.today()):
            raise forms.ValidationError("Invalid date of birth.")
        return dob


class CustomerLockForm(forms.Form):
    reason = forms.CharField(label="Lock reason", required=False, max_length=255, strip=True)


class CustomerFilterForm(forms.Form):
    q = forms.CharField(label="Keyword", required=False, max_length=100, strip=True,
                        widget=forms.TextInput(attrs={"placeholder": "Name, phone, email"}))
    age_group = forms.ChoiceField(label="Age Group", required=False, choices=[("", "All"), *AGE_GROUP_CHOICES])
    gender = forms.ChoiceField(label="Gender", required=False, choices=[("", "All"), *Gender.choices])
    playing_level = forms.ChoiceField(label="Playing Level", required=False, choices=[("", "All"), *PlayingLevel.choices])
    account_status = forms.ChoiceField(label="Account", required=False,
                                       choices=[("", "All"), *AccountStatusFilter.choices])

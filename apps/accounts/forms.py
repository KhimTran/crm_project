from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .constants import AccountRole, AccountStatus, normalize_account_choice
from .managers import AccountManager
from .models import Account


class CanonicalChoiceField(forms.ChoiceField):
    def to_python(self, value):
        return super().to_python(normalize_account_choice(value))


class AccountCreateForm(forms.Form):
    email = forms.EmailField(max_length=255)
    role = CanonicalChoiceField(choices=AccountRole.choices, widget=forms.Select(attrs={"id": "id_create_role"}))
    status = CanonicalChoiceField(choices=AccountStatus.choices, widget=forms.Select(attrs={"id": "id_create_status"}))
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    # Optional profile fields
    full_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={"placeholder": "Full name..."}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={"placeholder": "Phone number..."}))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    gender = forms.ChoiceField(
        choices=[("", "-- Select gender --"), ("MALE", "Male"), ("FEMALE", "Female"), ("OTHER", "Other")],
        required=False,
    )
    address = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={"placeholder": "Address..."}))

    def clean_email(self):
        email = AccountManager.normalize_account_email(self.cleaned_data["email"])
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use")
        return email

    def clean(self):
        data = super().clean()
        password = data.get("password")
        confirmation = data.get("password_confirm")
        if password and confirmation and password != confirmation:
            self.add_error("password_confirm", "Passwords do not match")
        if password and data.get("email") and password == confirmation:
            try:
                validate_password(password, Account(email=data["email"], role=data.get("role")))
            except ValidationError as exc:
                self.add_error("password", exc)
        return data


class AccountProfileEditForm(forms.Form):
    full_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(max_length=255, required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    gender = forms.ChoiceField(
        choices=[("", "-- Select gender --"), ("MALE", "Male"), ("FEMALE", "Female"), ("OTHER", "Other")],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    address = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    playing_level = forms.ChoiceField(
        choices=[
            ("", "-- Select playing level --"),
            ("BEGINNER", "Beginner"),
            ("RECREATIONAL", "Recreational"),
            ("COMPETITIVE", "Competitive"),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, account_id=None, **kwargs):
        self.account_id = account_id
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            email = AccountManager.normalize_account_email(email)
            qs = Account.objects.filter(email=email)
            if self.account_id:
                qs = qs.exclude(pk=self.account_id)
            if qs.exists():
                raise forms.ValidationError("Email is already in use")
        return email


class AccountRoleForm(forms.Form):
    role = CanonicalChoiceField(choices=AccountRole.choices)


class AccountListFilterForm(forms.Form):
    q = forms.CharField(required=False, strip=True, max_length=255, widget=forms.TextInput(attrs={"placeholder": "Search email, name, code...", "autocomplete": "off"}))
    role = CanonicalChoiceField(choices=[("", "All roles"), *AccountRole.choices], required=False)
    status = CanonicalChoiceField(choices=[("", "All statuses"), *AccountStatus.choices], required=False)


class AdminPasswordResetForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    new_password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        data = super().clean()
        if data.get("new_password") and data.get("new_password_confirm"):
            if data["new_password"] != data["new_password_confirm"]:
                self.add_error("new_password_confirm", "Passwords do not match")
        return data

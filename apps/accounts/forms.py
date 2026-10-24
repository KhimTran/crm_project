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


class AccountRoleForm(forms.Form):
    role = CanonicalChoiceField(choices=AccountRole.choices)


class AccountListFilterForm(forms.Form):
    q = forms.CharField(required=False, strip=True, max_length=255, widget=forms.TextInput(attrs={"placeholder": "Search by email...", "autocomplete": "off"}))
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

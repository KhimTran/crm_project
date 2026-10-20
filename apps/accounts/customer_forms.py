from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.customers.self_service_forms import CustomerProfileForm
from .constants import AccountStatus
from .managers import AccountManager
from .models import Account


class CustomerLoginForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=255, widget=forms.EmailInput(attrs={"autocomplete": "username"}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.account = None
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if data.get("email") and data.get("password"):
            email = AccountManager.normalize_account_email(data["email"])
            self.account = authenticate(self.request, email=email, password=data["password"])
            if self.account is None:
                locked = Account.objects.filter(email=email, status=AccountStatus.LOCKED).first()
                if locked is not None and locked.check_password(data["password"]):
                    raise forms.ValidationError("Account has been locked. Please contact management.")
                raise forms.ValidationError("Invalid email or password.")
        return data


class CustomerRegistrationForm(CustomerProfileForm):
    email = forms.EmailField(label="Email", max_length=255)
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password_confirm = forms.CharField(label="Confirm password", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def clean_email(self):
        email = AccountManager.normalize_account_email(self.cleaned_data["email"])
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean(self):
        data = super().clean()
        password = data.get("password")
        if password and password != data.get("password_confirm"):
            self.add_error("password_confirm", "Confirmation password does not match.")
        if password:
            try:
                validate_password(password, Account(email=data.get("email", "")))
            except ValidationError as exc:
                self.add_error("password", exc)
        return data


class AccountPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Email", max_length=255)

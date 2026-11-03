"""Shared birth-date validation and calendar bounds for account profiles."""
from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .constants import AccountRole


def minimum_age_for_role(role):
    return 18 if str(role).strip().upper() in (AccountRole.ADMIN, AccountRole.MANAGER) else 14


def latest_birth_date(minimum_age, today=None):
    today = today or timezone.localdate()
    # On leap day, Feb 28 is the latest birthday that has already occurred.
    try:
        return today.replace(year=today.year - minimum_age)
    except ValueError:
        return today.replace(year=today.year - minimum_age, day=28)


def validate_birth_date(value, minimum_age):
    if value is None:
        return
    today = timezone.localdate()
    if value > today:
        raise ValidationError("Date of birth cannot be in the future.")
    if value > latest_birth_date(minimum_age, today):
        raise ValidationError(f"Must be at least {minimum_age} years old.")


class BirthDateInput(forms.DateInput):
    input_type = "date"
    minimum_age = 14

    def get_context(self, name, value, attrs):
        attrs = {**(attrs or {}), "max": latest_birth_date(self.minimum_age).isoformat(),
                 "data-adult-max": latest_birth_date(18).isoformat(),
                 "data-customer-max": latest_birth_date(14).isoformat()}
        return super().get_context(name, value, attrs)


class BirthDateField(forms.DateField):
    def __init__(self, *args, minimum_age=14, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = BirthDateInput(attrs=self.widget.attrs, format="%Y-%m-%d")
        self.set_minimum_age(minimum_age)

    def set_minimum_age(self, minimum_age):
        self.minimum_age = minimum_age
        self.widget.minimum_age = minimum_age

    def validate(self, value):
        super().validate(value)
        validate_birth_date(value, self.minimum_age)

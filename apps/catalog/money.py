"""Lossless money parsing and presentation, independent of the current locale."""
import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.core.exceptions import ValidationError

MONEY_PATTERN = re.compile(r"[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?\Z")


def parse_money(value):
    if isinstance(value, Decimal):
        amount = value
    else:
        text = str(value).strip()
        if not MONEY_PATTERN.fullmatch(text):
            raise ValidationError("Enter a valid amount (e.g. 1,234.50).", code="invalid")
        try:
            amount = Decimal(text.replace(",", ""))
        except InvalidOperation as exc:
            raise ValidationError("Enter a valid amount.", code="invalid") from exc
    if not amount.is_finite():
        raise ValidationError("Enter a valid amount.", code="invalid")
    return amount


def format_money(value):
    amount = parse_money(value)
    text = format(amount, ",f")
    if amount == amount.to_integral_value():
        return text.split(".")[0]
    # DECIMAL(12,2) cents remain visible, including the final zero.
    return text if "." in text and len(text.rsplit(".", 1)[1]) >= 2 else text + "0"


class MoneyInput(forms.TextInput):
    def __init__(self, attrs=None):
        super().__init__({"inputmode": "decimal", "data-money": "", **(attrs or {})})

    def format_value(self, value):
        if value in (None, ""):
            return ""
        try:
            return format_money(value)
        except ValidationError:
            return value


class MoneyField(forms.DecimalField):
    widget = MoneyInput

    def to_python(self, value):
        if value in self.empty_values:
            return None
        return super().to_python(parse_money(value))

from django import template
from django.core.exceptions import ValidationError

from apps.catalog.money import format_money

register = template.Library()


@register.filter
def money(value):
    try:
        return format_money(value)
    except (ValidationError, TypeError, ValueError):
        return ""

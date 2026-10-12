"""Presentation helpers for the customer storefront only."""
from decimal import Decimal, InvalidOperation
import unicodedata

from django import template

from apps.catalog.models import Category, Status

register = template.Library()


def active_shop_categories(request=None):
    if request is not None and hasattr(request, "_shop_categories"):
        return request._shop_categories
    categories = list(Category.objects.filter(status=Status.ACTIVE).order_by("category_name", "category_id"))
    if request is not None:
        request._shop_categories = categories
    return categories


@register.inclusion_tag("shop/_category_navigation.html", takes_context=True)
def shop_navigation(context):
    request = context.get("request")
    return {"categories": active_shop_categories(request), "request": request}


@register.filter
def vnd_price(value):
    """Format Decimal prices without locale dependence or loss of cents."""
    try:
        amount = Decimal(value)
        if not amount.is_finite():
            return ""
        whole, fraction = format(amount, ".2f").split(".")
        grouped = format(int(whole), ",").replace(",", ".")
        return f"{grouped}{',' + fraction if fraction != '00' else ''} ₫"
    except (InvalidOperation, TypeError, ValueError):
        return ""


@register.filter
def category_art(category_name):
    # Match category labels only; never pretend an illustration is a real model.
    label = unicodedata.normalize("NFKD", str(category_name)).encode("ascii", "ignore").decode().strip().casefold()
    kinds = {
        "racket": "racket", "rackets": "racket", "demo rackets": "racket", "badminton rackets": "racket", "vot": "racket", "vot cau long": "racket",
        "shoes": "shoes", "badminton shoes": "shoes", "giay": "shoes", "giay cau long": "shoes",
        "shuttlecocks": "shuttle", "shuttlecock": "shuttle", "qua cau": "shuttle", "cau long": "shuttle",
        "bags": "bag", "bag": "bag", "tui": "bag", "tui vot": "bag", "balo": "bag", "balo cau long": "bag",
        "apparel": "apparel", "clothing": "apparel", "quan ao": "apparel", "quan ao cau long": "apparel",
        "accessories": "accessory", "phu kien": "accessory", "phu kien cau long": "accessory",
    }
    return f"images/shop-{kinds.get(label, 'generic')}.svg"


@register.filter
def product_art(product):
    return category_art(product.category.category_name)

"""Repeatable data repair; no schema, relationship or price changes."""
from django.core.management.base import CommandError
from django.db import transaction

from .models import Brand, Product
from .vocabulary import BRAND_PREFERENCE_TYPES, brand_aliases, canonical_product_name


@transaction.atomic
def normalize_catalog(*, apply=False):
    from apps.customers.models import CustomerPreference
    brands = list(Brand.objects.select_for_update().filter(brand_name__in=brand_aliases("Li-Ning")))
    if len(brands) > 1:
        raise CommandError("Multiple Li-Ning/Lining brand IDs exist; resolve ownership before repair. No changes made.")
    counts = {"brands": 0, "products": 0, "preferences": 0, "merged": 0}
    if brands:
        brand = brands[0]
        counts["brands"] = int(brand.brand_name != "Li-Ning")
        if apply and counts["brands"]:
            Brand.objects.filter(pk=brand.pk).update(brand_name="Li-Ning")
        for product in Product.objects.select_for_update().filter(brand=brand):
            name = canonical_product_name(product.product_name)
            if name != product.product_name:
                counts["products"] += 1
                if apply:
                    Product.objects.filter(pk=product.pk).update(product_name=name)
    seen = set()
    rows = CustomerPreference.objects.select_for_update().filter(
        preference_type__in=BRAND_PREFERENCE_TYPES,
        preference_value__in=brand_aliases("Li-Ning"),
    ).order_by("preference_id")
    # FAVORITE_BRAND readers use the latest row; keep that ordering even when
    # another favorite value sits between the two aliases in historical data.
    rows = sorted(rows, key=lambda row: (
        row.preference_type, -row.pk if row.preference_type == "FAVORITE_BRAND" else row.pk,
    ))
    for preference in rows:
        key = (preference.customer_id, preference.preference_type, "Li-Ning")
        if key in seen:
            counts["merged"] += 1
            if apply:
                preference.delete()
        else:
            seen.add(key)
            if preference.preference_value != "Li-Ning":
                counts["preferences"] += 1
                if apply:
                    CustomerPreference.objects.filter(pk=preference.pk).update(preference_value="Li-Ning")
    return counts

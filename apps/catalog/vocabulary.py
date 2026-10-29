"""Shared catalog vocabulary. Query choices at call time, never during import."""
import re

BRAND_ALIASES = {"Lining": "Li-Ning", "Li-Ning": "Li-Ning"}
BRAND_PREFERENCE_TYPES = ("BRAND", "FAVORITE_BRAND")


def canonical_brand(value):
    value = (value or "").strip()
    return BRAND_ALIASES.get(value, value)


def brand_aliases(value):
    canonical = canonical_brand(value)
    return tuple(alias for alias, name in BRAND_ALIASES.items() if name == canonical) or (canonical,)


def canonical_product_name(value):
    return re.sub(r"^Lining(?=\s|$)", "Li-Ning", value)


def search_aliases(value):
    """Expand only the explicitly supported brand token, preserving model suffixes."""
    values = {value}
    for alias in BRAND_ALIASES:
        if re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", value, flags=re.I):
            for replacement in BRAND_ALIASES:
                values.add(re.sub(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", replacement, value, flags=re.I))
    return sorted(values)


def brand_choices(*, saved=(), include_other=False):
    from .models import Brand, Status
    names = {canonical_brand(name) for name in Brand.objects.filter(status=Status.ACTIVE)
             .values_list("brand_name", flat=True)}
    names.update(canonical_brand(name) for name in saved if name)
    names.discard("Other")
    choices = [(name, name) for name in sorted(names)]
    if include_other:
        choices.append(("Other", "Other"))
    return choices

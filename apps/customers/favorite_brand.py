"""Thương hiệu cầu lông yêu thích của khách hàng (đọc / ghi / thống kê).

Mỗi khách có tối đa 1 dòng FAVORITE_BRAND trong customer_preferences; đổi thương hiệu = thay giá trị, không cộng dồn.
"""

from django.db import transaction
from apps.catalog.vocabulary import brand_choices, canonical_brand

from .constants import (
    FAVORITE_BRAND_OTHER, FAVORITE_BRAND_OTHER_TYPE, FAVORITE_BRAND_TYPE,
)
from .models import CustomerPreference


# tv4: đọc thương hiệu yêu thích hiện tại của một khách -> (brand, other_name); (None, "") nếu chưa khai báo
def get_favorite_brand(customer):
    rows = dict(CustomerPreference.objects.filter(
        customer=customer, preference_type__in=(FAVORITE_BRAND_TYPE, FAVORITE_BRAND_OTHER_TYPE),
    ).order_by("preference_id").values_list("preference_type", "preference_value"))
    brand = canonical_brand(rows.get(FAVORITE_BRAND_TYPE)) or None
    return brand, (rows.get(FAVORITE_BRAND_OTHER_TYPE, "") if brand == FAVORITE_BRAND_OTHER else "")


# tv4: lưu thương hiệu yêu thích (thay thế bản ghi cũ, không tạo trùng); None = giữ nguyên, "" = xóa lựa chọn
@transaction.atomic
def set_favorite_brand(customer, brand, other_name=""):
    if brand is None:
        return
    type(customer).objects.select_for_update().get(pk=customer.pk)
    brand = canonical_brand(brand)
    saved, _ = get_favorite_brand(customer)
    if brand and brand not in dict(brand_choices(saved=(saved,), include_other=True)):
        raise ValueError(f"Invalid favorite brand: {brand!r}")
    other_name = (other_name or "").strip() if brand == FAVORITE_BRAND_OTHER else ""
    CustomerPreference.objects.filter(
        customer=customer, preference_type__in=(FAVORITE_BRAND_TYPE, FAVORITE_BRAND_OTHER_TYPE),
    ).delete()
    if not brand:
        return
    CustomerPreference.objects.create(customer=customer, preference_type=FAVORITE_BRAND_TYPE, preference_value=brand)
    if other_name:
        CustomerPreference.objects.create(
            customer=customer, preference_type=FAVORITE_BRAND_OTHER_TYPE, preference_value=other_name)

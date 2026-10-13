"""Truy vấn khách hàng dùng chung: danh sách CRM (TV4), chọn người nhận khảo sát (TV5), báo cáo (4.1.5)."""

from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from .constants import AGE_GROUPS, CustomerStatus, PreferenceType
from .models import Customer, CustomerPreference

_AGE_BOUNDS = {value: (low, high) for value, _, low, high in AGE_GROUPS}


# tv4: khách hàng chưa bị xóa, kèm account, mới nhất trước
def customer_queryset():
    return (Customer.objects.exclude(status=CustomerStatus.DELETED)
            .select_related("account").order_by("-customer_id"))


# tv4: ngày cách hôm nay n năm (29/02 rơi vào năm không nhuận thì lùi về 28/02)
def years_ago(today, years):
    try:
        return today.replace(year=today.year - years)
    except ValueError:
        return today.replace(year=today.year - years, day=28)


# tv4: tính tuổi tròn từ ngày sinh
def age_of(date_of_birth, today=None):
    today = today or timezone.localdate()
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))


# tv4: trả về mã nhóm tuổi (AGE_GROUPS) của một ngày sinh, None nếu chưa có ngày sinh
def age_group_of(date_of_birth, today=None):
    if date_of_birth is None:
        return None
    age = age_of(date_of_birth, today)
    for value, _, low, high in AGE_GROUPS:
        if (low is None or age >= low) and (high is None or age <= high):
            return value
    return None


# tv4: điều kiện ngày sinh ứng với một nhóm tuổi (tuổi >= low <=> sinh trước/đúng ngày cách đây low năm)
def _age_group_q(age_group, today):
    low, high = _AGE_BOUNDS[age_group]
    q = Q(date_of_birth__isnull=False)
    if low is not None:
        q &= Q(date_of_birth__lte=years_ago(today, low))
    if high is not None:
        q &= Q(date_of_birth__gt=years_ago(today, high + 1))
    return q


# tv4: điều kiện "khách hàng có sở thích type=value" (Exists để không nhân bản dòng)
def _has_preference(preference_type, value):
    return Exists(CustomerPreference.objects.filter(customer=OuterRef("pk"), preference_type=preference_type,
                                                    preference_value=value))


# tv4: bộ lọc khách hàng dùng chung (TV5 dùng lại để chọn người nhận khảo sát)
def filter_customers(qs, params, today=None):
    """Lọc queryset Customer theo params (thường là cleaned_data của CustomerFilterForm).

    Khóa hỗ trợ, khóa nào rỗng/thiếu thì bỏ qua:
      q              – tìm trong họ tên, SĐT, email
      age_group      – mã trong constants.AGE_GROUPS (UNDER_18, 18_24, ..., 55_PLUS); KH chưa có ngày sinh bị loại
      gender         – MALE / FEMALE / OTHER
      playing_level  – BEGINNER / RECREATIONAL / COMPETITIVE
      play_style     – một giá trị trong PLAY_STYLE_CHOICES (VD "Tấn công")
      brand          – một giá trị trong BRAND_CHOICES (VD "Yonex")
      account_status – ACTIVE / LOCKED (accounts.status)
    Ví dụ TV5: filter_customers(customer_queryset(), {"age_group": "18_24", "brand": "Yonex",
                                                     "account_status": "ACTIVE"})
    """
    today = today or timezone.localdate()
    q = (params.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(full_name__icontains=q) | Q(phone__icontains=q) | Q(account__email__icontains=q))
    if params.get("age_group") in _AGE_BOUNDS:
        qs = qs.filter(_age_group_q(params["age_group"], today))
    if params.get("gender"):
        qs = qs.filter(gender=params["gender"])
    if params.get("playing_level"):
        qs = qs.filter(playing_level=params["playing_level"])
    if params.get("play_style"):
        qs = qs.filter(_has_preference(PreferenceType.PLAY_STYLE, params["play_style"]))
    if params.get("brand"):
        qs = qs.filter(_has_preference(PreferenceType.BRAND, params["brand"]))
    if params.get("account_status"):
        qs = qs.filter(account__status=params["account_status"])
    return qs

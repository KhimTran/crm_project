"""4.1.5 Báo cáo khách hàng: số liệu cho biểu đồ Chart.js và bảng in.

Mỗi hàm trả về list dict {"label": ..., "count": ...} để template vẽ bảng và truyền json_script cho biểu đồ.
Nhóm theo tháng làm bằng Python (localtime) thay cho TruncMonth vì MySQL cần nạp bảng timezone mới đổi múi giờ được.
"""

from collections import Counter
from datetime import datetime

from django.db.models import Avg, Count
from django.utils import timezone

from apps.accounts.constants import AccountStatus
from apps.feedback.models import Feedback

from .constants import AGE_GROUPS, Gender, PlayingLevel, PreferenceType
from .models import CustomerPreference
from .selectors import age_group_of, customer_queryset

UNKNOWN_LABEL = "Chưa khai báo"


# tv4: 4.1.5 đổi Counter thành danh sách {label, count} theo đúng thứ tự choices, thêm dòng "Chưa khai báo" nếu có
def _rows_from_counter(counter, choices):
    rows = [{"label": label, "count": counter.get(value, 0)} for value, label in choices]
    if counter.get(None):
        rows.append({"label": UNKNOWN_LABEL, "count": counter[None]})
    return rows


# tv4: 4.1.5 thống kê số khách hàng theo nhóm tuổi (<18, 18–24, ..., ≥55) từ date_of_birth
def age_group_report(today=None):
    today = today or timezone.localdate()
    counter = Counter(age_group_of(dob, today)
                      for dob in customer_queryset().values_list("date_of_birth", flat=True))
    return _rows_from_counter(counter, [(value, label) for value, label, _, _ in AGE_GROUPS])


# tv4: 4.1.5 thống kê theo giới tính
def gender_report():
    counter = Counter(v if v in Gender.values else None
                      for v in customer_queryset().values_list("gender", flat=True))
    return _rows_from_counter(counter, Gender.choices)


# tv4: 4.1.5 thống kê theo trình độ chơi
def playing_level_report():
    counter = Counter(v if v in PlayingLevel.values else None
                      for v in customer_queryset().values_list("playing_level", flat=True))
    return _rows_from_counter(counter, PlayingLevel.choices)


# tv4: 4.1.5 thống kê sở thích theo loại (lối chơi / thương hiệu / nhóm sản phẩm), nhiều KH chọn nhất trước
def preference_report():
    rows = (CustomerPreference.objects.filter(customer__in=customer_queryset().values("pk"))
            .values("preference_type", "preference_value")
            .annotate(count=Count("customer", distinct=True))
            .order_by("preference_type", "-count", "preference_value"))
    report = {}
    for row in rows:
        report.setdefault(row["preference_type"], []).append({"label": row["preference_value"], "count": row["count"]})
    return [{"type": ptype, "label": label, "rows": report[ptype]}
            for ptype, label in PreferenceType.choices if ptype in report]


# tv4: 4.1.5 số khách hàng mới theo tháng trong `months` tháng gần nhất (tính cả tháng hiện tại, tháng 0 KH vẫn hiện)
def new_customers_by_month(months=12, today=None):
    today = today or timezone.localdate()
    keys = []
    year, month = today.year, today.month
    for _ in range(months):
        keys.append((year, month))
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    keys.reverse()
    first_day = timezone.make_aware(datetime(keys[0][0], keys[0][1], 1))
    counter = Counter()
    for created_at in customer_queryset().filter(created_at__gte=first_day).values_list("created_at", flat=True):
        local = timezone.localtime(created_at)
        counter[(local.year, local.month)] += 1
    return [{"label": f"{m:02d}/{y}", "count": counter.get((y, m), 0)} for y, m in keys]


# tv4: 4.1.5 điểm hài lòng trung bình (rating) và số phản hồi theo sản phẩm, điểm thấp lên trước để dễ chú ý
def satisfaction_by_product():
    rows = (Feedback.objects.values("product__product_name")
            .annotate(avg_rating=Avg("rating"), count=Count("feedback_id"))
            .order_by("avg_rating", "-count", "product__product_name"))
    return [{"label": r["product__product_name"], "avg": round(float(r["avg_rating"]), 2), "count": r["count"]}
            for r in rows]


# tv4: 4.1.5 các chỉ số tổng quan đầu trang báo cáo
def summary(today=None):
    today = today or timezone.localdate()
    customers = customer_queryset()
    month_start = timezone.make_aware(datetime(today.year, today.month, 1))
    rating = Feedback.objects.aggregate(avg=Avg("rating"))["avg"]
    return {
        "total": customers.count(),
        "new_this_month": customers.filter(created_at__gte=month_start).count(),
        "locked": customers.filter(account__status=AccountStatus.LOCKED).count(),
        "feedbacks": Feedback.objects.count(),
        "avg_rating": round(float(rating), 2) if rating is not None else None,
    }

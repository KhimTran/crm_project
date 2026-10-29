"""4.1.5 Báo cáo khách hàng: số liệu cho biểu đồ Chart.js và bảng in.

Mỗi hàm trả về list dict {"label": ..., "count": ...} để template vẽ bảng và truyền json_script cho biểu đồ.
Nhóm theo tháng làm bằng Python (localtime) thay cho TruncMonth vì MySQL cần nạp bảng timezone mới đổi múi giờ được.
"""

from collections import Counter
from datetime import datetime

from django.db.models import Avg, Count
from django.utils import timezone

from apps.accounts.constants import AccountStatus
from apps.feedback.constants import FeedbackStatus
from apps.feedback.models import Feedback

from .constants import (
    AGE_GROUPS, FAVORITE_BRAND_TYPE, FAVORITE_BRANDS, CustomerStatus, Gender, PlayingLevel, PreferenceType,
)
from .models import Customer, CustomerPreference
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
    """Tuổi tròn tính từ date_of_birth của hồ sơ khách hàng tại ngày xem (giờ Asia/Ho_Chi_Minh);
    chỉ khách chưa xóa mềm. Khách chưa có ngày sinh vào dòng "Chưa khai báo"."""
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
    """Sở thích lấy từ bảng customer_preferences của hồ sơ khách (không lấy từ câu trả lời khảo sát);
    count = số khách chưa xóa khai báo giá trị đó, nhóm theo loại sở thích."""
    rows =(CustomerPreference.objects.filter(customer__in=customer_queryset().values("pk"))
            .values("preference_type", "preference_value")
            .annotate(count=Count("customer", distinct=True))
            .order_by("preference_type", "-count", "preference_value"))
    report = {}
    for row in rows:
        report.setdefault(row["preference_type"], []).append({"label": row["preference_value"], "count": row["count"]})
    return [{"type": ptype, "label": label, "rows": report[ptype]}
            for ptype, label in PreferenceType.choices if ptype in report]


# tv4: thống kê thương hiệu cầu lông yêu thích của khách chưa xóa (mỗi khách tính đúng 1 lần theo giá trị hiện tại)
def favorite_brand_report():
    """Mẫu số của % = số khách có thương hiệu hợp lệ (`answered`); khách chưa khai báo / giá trị null, rỗng,
    không thuộc 5 nhóm được đếm riêng ở `unanswered` và không vào biểu đồ. Nếu dữ liệu lỗi có nhiều dòng
    cho một khách thì lấy dòng mới nhất."""
    current = {}
    for customer_id, value in (CustomerPreference.objects.filter(
            preference_type=FAVORITE_BRAND_TYPE, customer__in=customer_queryset().values("pk"))
            .order_by("preference_id").values_list("customer_id", "preference_value")):
        current[customer_id] = value
    counter = Counter(v for v in current.values() if v in FAVORITE_BRANDS)
    answered = sum(counter.values())
    total = customer_queryset().count()
    rows = [{"label": brand, "count": counter[brand], "pct": _pct(counter[brand], answered)} for brand in FAVORITE_BRANDS]
    return {"rows": rows, "answered": answered, "unanswered": total - answered, "total_customers": total}


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
    for created_at, gender in customer_queryset().filter(created_at__gte=first_day).values_list("created_at", "gender"):
        local = timezone.localtime(created_at)
        counter[(local.year, local.month, None)] += 1
        counter[(local.year, local.month, gender if gender in Gender.values else "UNKNOWN")] += 1
    # tv4: ngoài tổng "count", mỗi dòng có thêm số KH mới theo giới tính (male/female/other/unknown) để vẽ đường theo giới tính
    return [{"label": f"{m:02d}/{y}", "count": counter[(y, m, None)],
             **{g.lower(): counter[(y, m, g)] for g in [*Gender.values, "UNKNOWN"]}}
            for y, m in keys]


# tv4: 4.1.5 phản hồi của khách hàng chưa bị xóa (báo cáo không tính phản hồi của KH đã xóa)
def _active_feedbacks():
    return Feedback.objects.filter(customer__in=customer_queryset().values("pk"))


# tv4: 4.1.5 điểm hài lòng trung bình (rating) và số phản hồi theo sản phẩm (nhóm theo ID sản phẩm, không theo tên), điểm thấp lên trước
def satisfaction_by_product():
    rows = (_active_feedbacks().values("product_id", "product__product_name")
            .annotate(avg_rating=Avg("rating"), count=Count("feedback_id"))
            .order_by("avg_rating", "-count", "product__product_name", "product_id"))
    return [{"label": r["product__product_name"], "avg": round(float(r["avg_rating"]), 2), "count": r["count"]}
            for r in rows]


# tv4: phần trăm có chặn mẫu số 0 (None = chưa có dữ liệu)
def _pct(part, whole):
    return round(part * 100 / whole, 1) if whole else None


# Tỷ lệ tài khoản hoạt động / bị khóa của khách hàng
def account_status_report():
    customers = customer_queryset()
    total = customers.count()
    active = customers.filter(status=AccountStatus.ACTIVE).count()
    locked = customers.filter(status=AccountStatus.LOCKED).count()
    return {"total": total, "active": active, "locked": locked,
            "active_pct": _pct(active, total), "locked_pct": _pct(locked, total)}


# Không sử dụng xóa mềm (DELETED) nên số khách xóa mềm = 0
def deleted_count():
    return 0


# tv4: 4.1.5 số phản hồi theo tháng (theo created_at, giờ địa phương) và theo trạng thái xử lý hiện tại
def feedback_by_month(months=6, today=None):
    """Phản hồi của khách chưa xóa trong `months` tháng gần nhất (kể cả tháng hiện tại).
    Mỗi dòng: tổng và số theo trạng thái NEW / IN_PROGRESS / RESOLVED hiện tại. Không có loại phản hồi
    trong CSDL nên không chia theo loại."""
    today = today or timezone.localdate()
    keys = []
    year, month = today.year, today.month
    for _ in range(months):
        keys.append((year, month))
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    keys.reverse()
    first_day = timezone.make_aware(datetime(keys[0][0], keys[0][1], 1))
    counter = Counter()
    for created_at, status in _active_feedbacks().filter(created_at__gte=first_day).values_list("created_at", "status"):
        local = timezone.localtime(created_at)
        counter[(local.year, local.month, None)] += 1
        counter[(local.year, local.month, status)] += 1
    return [{"label": f"{m:02d}/{y}", "count": counter[(y, m, None)],
             **{status.lower(): counter[(y, m, status)] for status in FeedbackStatus.values}}
            for y, m in keys]


# tv4: 4.1.5 số phản hồi theo trạng thái xử lý (toàn bộ, khách chưa xóa)
def feedback_status_report():
    counter = Counter(_active_feedbacks().values_list("status", flat=True))
    total = sum(counter.values())
    return [{"label": label, "count": counter.get(value, 0), "pct": _pct(counter.get(value, 0), total)}
            for value, label in FeedbackStatus.choices]


# tv4: 4.1.5 thời gian xử lý trung bình (giờ) = TB(resolved_at − created_at) của phản hồi đã xử lý
def avg_resolution_hours():
    """Chỉ phản hồi RESOLVED có cả created_at và resolved_at; None khi chưa có phản hồi nào như vậy."""
    pairs = list(_active_feedbacks().filter(status=FeedbackStatus.RESOLVED, resolved_at__isnull=False)
                 .values_list("created_at", "resolved_at"))
    if not pairs:
        return None
    seconds = sum(max((resolved - created).total_seconds(), 0) for created, resolved in pairs)
    return round(seconds / len(pairs) / 3600, 1)


# tv4: 4.1.5 các chỉ số tổng quan đầu trang báo cáo
def summary(today=None):
    today = today or timezone.localdate()
    customers = customer_queryset()
    month_start = timezone.make_aware(datetime(today.year, today.month, 1))
    feedbacks = _active_feedbacks()
    rating = feedbacks.aggregate(avg=Avg("rating"))["avg"]
    return {
        "total": customers.count(),
        "new_this_month": customers.filter(created_at__gte=month_start).count(),
        "locked": customers.filter(status=AccountStatus.LOCKED).count(),
        "feedbacks": feedbacks.count(),
        "avg_rating": round(float(rating), 2) if rating is not None else None,
    }

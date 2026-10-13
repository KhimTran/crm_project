from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone

from .models import Feedback


# tv4: đổi ngày (date) thành mốc datetime có múi giờ, tránh __date (MySQL cần bảng timezone)
def _start_of_day(day):
    return timezone.make_aware(datetime.combine(day, time.min))


# tv4: 4.1.4 truy vấn danh sách phản hồi kèm khách hàng, sản phẩm, người xử lý; mới nhất trước
def feedback_queryset():
    return (Feedback.objects.select_related("customer__account", "product", "handled_by")
            .order_by("-created_at", "-feedback_id"))


# tv4: 4.1.4 lọc phản hồi theo từ khóa, trạng thái, sản phẩm, số sao, khoảng ngày gửi
def filter_feedbacks(qs, params):
    """params là cleaned_data của FeedbackFilterForm; khóa nào rỗng thì bỏ qua."""
    q = params.get("q")
    if q:
        qs = qs.filter(Q(content__icontains=q) | Q(customer__full_name__icontains=q)
                       | Q(customer__account__email__icontains=q) | Q(product__product_name__icontains=q))
    if params.get("status"):
        qs = qs.filter(status=params["status"])
    if params.get("product"):
        qs = qs.filter(product=params["product"])
    if params.get("rating"):
        qs = qs.filter(rating=params["rating"])
    if params.get("date_from"):
        qs = qs.filter(created_at__gte=_start_of_day(params["date_from"]))
    if params.get("date_to"):
        qs = qs.filter(created_at__lt=_start_of_day(params["date_to"] + timedelta(days=1)))
    return qs

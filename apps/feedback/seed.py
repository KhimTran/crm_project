"""Dữ liệu demo phản hồi (TV4) – được gọi từ `python manage.py seed_data` sau khi đã có khách hàng và sản phẩm.

Idempotent theo (khách hàng, sản phẩm, nội dung): chạy lại không sinh trùng.
"""

import random
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Product, Status as ProductStatus
from apps.customers.seed import demo_customers

from .constants import FeedbackStatus
from .models import Feedback

DEMO_FEEDBACK_COUNT = 36

# Nội dung mẫu theo loại sản phẩm và mức hài lòng (tốt: 4–5 sao, vừa: 3 sao, kém: 1–2 sao).
CONTENTS = {
    "racket": {
        "good": ["Vợt đầm tay, đánh cầu cao sâu rất dễ.", "Khung vợt chắc, đập cầu uy lực, rất hài lòng.",
                 "Vợt nhẹ đầu, phòng thủ phản tạt nhanh, đáng tiền."],
        "mid": ["Vợt ổn nhưng cước căng hơi chùng sau 2 tuần.", "Đánh được, tuy nhiên cán hơi to so với tay mình."],
        "bad": ["Vợt bị nứt khung sau một tháng sử dụng.", "Giao sai màu so với đơn đặt hàng, mong shop đổi lại."],
    },
    "shoe": {
        "good": ["Giày êm, bám sân tốt, di chuyển rất thoải mái.", "Giày nhẹ, form chuẩn size, sẽ ủng hộ tiếp."],
        "mid": ["Giày đẹp nhưng hơi chật phần mũi.", "Đế bám tốt, tuy nhiên lót giày hơi mỏng."],
        "bad": ["Giày bị bong keo đế sau 3 tuần.", "Giao nhầm size, đổi trả hơi lâu."],
    },
    "shuttle": {
        "good": ["Cầu bay ổn định, bền, đánh được nhiều trận.", "Cầu lông vịt chuẩn tốc độ, rất ổn."],
        "mid": ["Cầu bay được nhưng hơi nhanh so với sân của mình.", "Chất lượng tạm ổn, vài quả bị lệch."],
        "bad": ["Cầu gãy lông nhanh, một ống chỉ dùng được vài trận.", "Nhiều quả bay lắc, không đều."],
    },
}
REPLIES = {
    "good": "Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.",
    "mid": "Cảm ơn góp ý của bạn. Cửa hàng hỗ trợ căng lại cước/đổi size miễn phí, bạn mang sản phẩm qua shop nhé.",
    "bad": "Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.",
}
# Thứ tự trạng thái rải đều: khoảng 1/3 mới, 1/4 đang xử lý, còn lại đã xử lý.
STATUS_CYCLE = [FeedbackStatus.NEW, FeedbackStatus.RESOLVED, FeedbackStatus.IN_PROGRESS,
                FeedbackStatus.RESOLVED, FeedbackStatus.NEW, FeedbackStatus.RESOLVED]
RATINGS = [5, 5, 4, 4, 4, 3, 3, 2, 1]


# tv4: đoán loại sản phẩm (vợt / giày / cầu) từ tên để chọn nội dung phản hồi phù hợp
def _product_kind(product):
    name = product.product_name.lower()
    if "giày" in name or "shoe" in name:
        return "shoe"
    if "cầu" in name or "shuttle" in name:
        return "shuttle"
    return "racket"


# tv4: nhóm mức hài lòng theo số sao
def _sentiment(rating):
    return "good" if rating >= 4 else ("mid" if rating == 3 else "bad")


# tv4: tạo ≥ 30 phản hồi demo về sản phẩm đang bán, đủ 3 trạng thái, một số đã có trả lời; trả về số đã tạo
@transaction.atomic
def seed_feedbacks(handler, count=DEMO_FEEDBACK_COUNT):
    customers = demo_customers()
    products = list(Product.objects.filter(status=ProductStatus.ACTIVE).order_by("product_id"))
    if not customers or not products:
        return 0
    rng = random.Random(2026)
    now = timezone.now()
    created = 0
    for index in range(count):
        customer = customers[index % len(customers)]
        product = products[index % len(products)]
        rating = RATINGS[rng.randrange(len(RATINGS))]
        sentiment = _sentiment(rating)
        content = rng.choice(CONTENTS[_product_kind(product)][sentiment])
        status = STATUS_CYCLE[index % len(STATUS_CYCLE)]
        created_at = now - timedelta(days=rng.randint(1, 120), hours=rng.randint(0, 23))
        resolve_days = rng.randint(1, 3)  # lấy trước khi bỏ qua bản ghi cũ để dãy random không bị lệch
        feedback, is_new = Feedback.objects.get_or_create(
            customer=customer, product=product, content=content,
            defaults={"rating": rating, "status": FeedbackStatus.NEW},
        )
        if not is_new:
            continue
        fields = {"created_at": created_at, "status": status}
        if status != FeedbackStatus.NEW:
            fields["handled_by"] = handler
            if status == FeedbackStatus.RESOLVED:
                fields["manager_note"] = REPLIES[sentiment]
                fields["resolved_at"] = created_at + timedelta(days=resolve_days)
        Feedback.objects.filter(pk=feedback.pk).update(**fields)
        created += 1
    return created

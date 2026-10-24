from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Status as ProductStatus

from .constants import FeedbackStatus
from .errors import FeedbackNoteRequired, FeedbackNotFound, InvalidFeedbackStatus, ProductNotAvailable
from .models import Feedback

HANDLE_STATUSES = (FeedbackStatus.IN_PROGRESS, FeedbackStatus.RESOLVED)


# tv4: 4.2.4 khách hàng gửi phản hồi về sản phẩm, trạng thái ban đầu NEW
def create_feedback(*, customer, product, rating, content):
    if product.status != ProductStatus.ACTIVE:
        raise ProductNotAvailable("Sản phẩm không còn kinh doanh")
    return Feedback.objects.create(customer=customer, product=product, rating=rating,
                                   content=content.strip(), status=FeedbackStatus.NEW)


# tv4: 4.1.4 cập nhật trạng thái + câu trả lời của phản hồi, ghi người xử lý và thời điểm xử lý xong
@transaction.atomic
def handle_feedback(feedback_id, *, status, manager_note, handled_by):
    """4.1.4: status chỉ nhận IN_PROGRESS/RESOLVED; RESOLVED bắt buộc có manager_note.

    handled_by = tài khoản thao tác; resolved_at = now khi RESOLVED, mở lại (IN_PROGRESS) thì xóa resolved_at.
    """
    if status not in HANDLE_STATUSES:
        raise InvalidFeedbackStatus("Trạng thái xử lý không hợp lệ")
    manager_note = (manager_note or "").strip()
    if status == FeedbackStatus.RESOLVED and not manager_note:
        raise FeedbackNoteRequired("Cần nhập câu trả lời trước khi đánh dấu Đã xử lý")

    feedback = Feedback.objects.select_for_update().filter(pk=feedback_id).first()
    if feedback is None:
        raise FeedbackNotFound("Không tìm thấy phản hồi")

    if status == FeedbackStatus.RESOLVED:
        # Giữ mốc xử lý xong ban đầu nếu chỉ sửa lại câu trả lời.
        if feedback.status != FeedbackStatus.RESOLVED or feedback.resolved_at is None:
            feedback.resolved_at = timezone.now()
    else:
        feedback.resolved_at = None
    feedback.status = status
    feedback.manager_note = manager_note or None
    feedback.handled_by = handled_by
    feedback.save(update_fields=["status", "manager_note", "handled_by", "resolved_at"])
    return feedback

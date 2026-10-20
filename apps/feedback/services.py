from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Status as ProductStatus

from .constants import FeedbackStatus
from .errors import FeedbackNoteRequired, FeedbackNotFound, InvalidFeedbackStatus, ProductNotAvailable
from .models import Feedback

HANDLE_STATUSES = (FeedbackStatus.IN_PROGRESS, FeedbackStatus.RESOLVED)


def create_feedback(*, customer, product, rating, content):
    if product.status != ProductStatus.ACTIVE:
        raise ProductNotAvailable("Product is no longer available.")
    return Feedback.objects.create(customer=customer, product=product, rating=rating,
                                   content=content.strip(), status=FeedbackStatus.NEW)


@transaction.atomic
def handle_feedback(feedback_id, *, status, manager_note, handled_by):
    if status not in HANDLE_STATUSES:
        raise InvalidFeedbackStatus("Invalid feedback status.")
    manager_note = (manager_note or "").strip()
    if status == FeedbackStatus.RESOLVED and not manager_note:
        raise FeedbackNoteRequired("Manager response is required before marking as Resolved.")

    feedback = Feedback.objects.select_for_update().filter(pk=feedback_id).first()
    if feedback is None:
        raise FeedbackNotFound("Feedback not found.")

    if status == FeedbackStatus.RESOLVED:
        if feedback.status != FeedbackStatus.RESOLVED or feedback.resolved_at is None:
            feedback.resolved_at = timezone.now()
    else:
        feedback.resolved_at = None
    feedback.status = status
    feedback.manager_note = manager_note or None
    feedback.handled_by = handled_by
    feedback.save(update_fields=["status", "manager_note", "handled_by", "resolved_at"])
    return feedback

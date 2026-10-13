from .constants import FeedbackStatus
from .models import Feedback


# tv4: số phản hồi NEW hiển thị badge trên menu CRM (chỉ đếm khi đang ở trang /crm/ để đỡ tốn truy vấn)
def crm_feedback_badge(request):
    if not request.path.startswith("/crm/") or not getattr(request.user, "is_authenticated", False):
        return {}
    return {"new_feedback_count": Feedback.objects.filter(status=FeedbackStatus.NEW).count()}

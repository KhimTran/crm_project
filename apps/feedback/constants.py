from django.db import models


# tv4: trạng thái phản hồi NEW → IN_PROGRESS → RESOLVED
class FeedbackStatus(models.TextChoices):
    NEW = "NEW", "Mới"
    IN_PROGRESS = "IN_PROGRESS", "Đang xử lý"
    RESOLVED = "RESOLVED", "Đã xử lý"


RATING_CHOICES = [(n, f"{n} sao") for n in range(1, 6)]

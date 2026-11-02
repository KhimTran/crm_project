from django.db import models

class FeedbackStatus(models.TextChoices):
    NEW = "NEW", "Mới"
    RESOLVED = "RESOLVED", "Đã xử lý"

RATING_CHOICES = [(n, f"{n} sao") for n in range(1, 6)]

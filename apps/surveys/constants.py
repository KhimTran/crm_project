"""Survey vocabulary shared by services, forms, views and templates.

Existing lifecycle values are retained. The owner approved MATRIX and stored
questionnaire settings on 2026-10-18. Legacy RATING questions default to 1–5;
configured versioned questions may use 1–10, with bounds checked per question.
"""
from django.db import models


class SurveyStatus(models.TextChoices):
    DRAFT = "DRAFT", "Nháp"
    ACTIVE = "ACTIVE", "Đang mở"
    CLOSED = "CLOSED", "Đã đóng"


class QuestionType(models.TextChoices):
    SINGLE_CHOICE = "SINGLE_CHOICE", "Một lựa chọn"
    MULTI_CHOICE = "MULTI_CHOICE", "Nhiều lựa chọn"
    RATING = "RATING", "Thang điểm 1–5"
    MATRIX = "MATRIX", "Đánh giá theo tiêu chí"
    TEXT = "TEXT", "Trả lời tự do"


CHOICE_TYPES = (QuestionType.SINGLE_CHOICE, QuestionType.MULTI_CHOICE)

RECIPIENT_SENT = "SENT"
RECIPIENT_OPENED = "OPENED"
RECIPIENT_COMPLETED = "COMPLETED"
RESPONSE_SUBMITTED = "SUBMITTED"

MANAGER_GROUP = "CRM_MANAGER"

# (key, label, min_age, max_age) – same buckets the CRM customer report should use
AGE_GROUPS = [
    ("u18", "Dưới 18", 0, 17),
    ("18_24", "18–24", 18, 24),
    ("25_34", "25–34", 25, 34),
    ("35_44", "35–44", 35, 44),
    ("45_54", "45–54", 45, 54),
    ("55p", "Từ 55", 55, 200),
]

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


# tv4: mục tiêu khảo sát (cột surveys.objective, migration 0004)
class SurveyObjective(models.TextChoices):
    SATISFACTION = "SATISFACTION", "Đánh giá mức độ hài lòng"
    NEW_PRODUCT = "NEW_PRODUCT", "Thăm dò sản phẩm mới"
    SHOPPING_NEEDS = "SHOPPING_NEEDS", "Nhu cầu mua sắm"
    OTHER = "OTHER", "Khác"


# tv4: nhãn loại câu hỏi trên trình soạn khảo sát: (giá trị, nhãn ô chọn, nhãn badge) – chỉ dùng ở trang tạo/sửa
BUILDER_TYPES = [
    (QuestionType.SINGLE_CHOICE, "Trắc nghiệm (Chọn 1)", "Trắc nghiệm (1)"),
    (QuestionType.MULTI_CHOICE, "Chọn nhiều đáp án", "Chọn nhiều đáp án"),
    (QuestionType.RATING, "Thang điểm", "Thang điểm"),
    (QuestionType.TEXT, "Câu trả lời tự do", "Câu trả lời tự do"),
    (QuestionType.MATRIX, "Đánh giá theo tiêu chí", "Theo tiêu chí"),
]

SHOP_NAME = "Cửa hàng cầu lông"  # cùng tên với khung trang khách hàng (layouts/base_customer.html)

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

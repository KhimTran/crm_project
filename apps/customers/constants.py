from django.db import models


# Trạng thái khách hàng (ACTIVE / LOCKED - không sử dụng DELETED)
class CustomerStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Đang hoạt động"
    LOCKED = "LOCKED", "Đã khóa"


# Giới tính khách hàng kèm nhãn tiếng Việt
class Gender(models.TextChoices):
    MALE = "MALE", "Nam"
    FEMALE = "FEMALE", "Nữ"
    OTHER = "OTHER", "Khác"


# Trình độ chơi cầu lông kèm nhãn tiếng Việt
class PlayingLevel(models.TextChoices):
    BEGINNER = "BEGINNER", "Mới chơi"
    RECREATIONAL = "RECREATIONAL", "Phong trào"
    COMPETITIVE = "COMPETITIVE", "Thi đấu"


# Loại sở thích lưu trong customer_preferences
class PreferenceType(models.TextChoices):
    PLAY_STYLE = "PLAY_STYLE", "Lối chơi"
    BRAND = "BRAND", "Thương hiệu"
    CATEGORY = "CATEGORY", "Nhóm sản phẩm"


# Play styles are independent of the catalog; brand options come from catalog.vocabulary.
PLAY_STYLE_CHOICES = [(v, v) for v in ("Tấn công", "Phòng thủ", "Toàn diện", "Đánh đơn", "Đánh đôi")]


# Giá trị lọc theo trạng thái tài khoản (hoạt động / đã khóa)
class AccountStatusFilter(models.TextChoices):
    ACTIVE = "ACTIVE", "Hoạt động"
    LOCKED = "LOCKED", "Đã khóa"


# Nhóm tuổi dùng chung cho bộ lọc KH (TV5 gửi khảo sát) và báo cáo 4.1.5: (giá trị, nhãn, tuổi min, tuổi max).
AGE_GROUPS = [
    ("UNDER_18", "Dưới 18", None, 17),
    ("18_24", "18–24", 18, 24),
    ("25_34", "25–34", 25, 34),
    ("35_44", "35–44", 35, 44),
    ("45_54", "45–54", 45, 54),
    ("55_PLUS", "Từ 55", 55, None),
]
AGE_GROUP_CHOICES = [(value, label) for value, label, _, _ in AGE_GROUPS]


# tv4: thương hiệu cầu lông yêu thích (đúng 1 thương hiệu / khách) lưu trong customer_preferences, không thêm cột mới.
# FAVORITE_BRAND stores one catalog name (or a retained saved value); Other has a separate free-text row.
# Tách khỏi loại BRAND (nhiều giá trị do quản lý/seed nhập) để không lẫn với bộ lọc khách hàng hiện có.
FAVORITE_BRAND_TYPE = "FAVORITE_BRAND"
FAVORITE_BRAND_OTHER_TYPE = "FAVORITE_BRAND_OTHER"
FAVORITE_BRAND_OTHER = "Other"
FAVORITE_BRAND_OTHER_MAX_LENGTH = 100

from django.db import models


# tv4: trạng thái hồ sơ khách hàng (ACTIVE / DELETED khi xóa mềm)
class CustomerStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Đang hoạt động"
    DELETED = "DELETED", "Đã xóa"


# tv4: giới tính khách hàng kèm nhãn tiếng Việt
class Gender(models.TextChoices):
    MALE = "MALE", "Nam"
    FEMALE = "FEMALE", "Nữ"
    OTHER = "OTHER", "Khác"


# tv4: trình độ chơi cầu lông kèm nhãn tiếng Việt
class PlayingLevel(models.TextChoices):
    BEGINNER = "BEGINNER", "Mới chơi"
    RECREATIONAL = "RECREATIONAL", "Phong trào"
    COMPETITIVE = "COMPETITIVE", "Thi đấu"


# tv4: loại sở thích lưu trong customer_preferences
class PreferenceType(models.TextChoices):
    PLAY_STYLE = "PLAY_STYLE", "Lối chơi"
    BRAND = "BRAND", "Thương hiệu"
    CATEGORY = "CATEGORY", "Nhóm sản phẩm"


# preference_value lưu đúng chuỗi hiển thị; TV1 (đăng ký) và TV5 (lọc khảo sát) dùng chung danh sách này.
PLAY_STYLE_CHOICES = [(v, v) for v in ("Tấn công", "Phòng thủ", "Toàn diện", "Đánh đơn", "Đánh đôi")]
BRAND_CHOICES = [(v, v) for v in ("Yonex", "Victor", "Li-Ning", "Mizuno", "Kumpoo", "Apacs", "VNB")]


# tv4: giá trị lọc theo trạng thái tài khoản (hoạt động / đã khóa)
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

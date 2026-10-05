from django.db import models


class CustomerStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Đang hoạt động"
    DELETED = "DELETED", "Đã xóa"


class Gender(models.TextChoices):
    MALE = "MALE", "Nam"
    FEMALE = "FEMALE", "Nữ"
    OTHER = "OTHER", "Khác"


class PlayingLevel(models.TextChoices):
    BEGINNER = "BEGINNER", "Mới chơi"
    RECREATIONAL = "RECREATIONAL", "Phong trào"
    COMPETITIVE = "COMPETITIVE", "Thi đấu"


class PreferenceType(models.TextChoices):
    PLAY_STYLE = "PLAY_STYLE", "Lối chơi"
    BRAND = "BRAND", "Thương hiệu"
    CATEGORY = "CATEGORY", "Nhóm sản phẩm"


# preference_value lưu đúng chuỗi hiển thị; TV1 (đăng ký) và TV5 (lọc khảo sát) dùng chung danh sách này.
PLAY_STYLE_CHOICES = [(v, v) for v in ("Tấn công", "Phòng thủ", "Toàn diện", "Đánh đơn", "Đánh đôi")]
BRAND_CHOICES = [(v, v) for v in ("Yonex", "Victor", "Li-Ning", "Mizuno", "Kumpoo", "Apacs", "VNB")]

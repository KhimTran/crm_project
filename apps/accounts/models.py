from django.contrib.auth.models import AbstractUser
from django.db import models


class TaiKhoan(AbstractUser):
    class VaiTro(models.TextChoices):
        ADMIN = 'ADMIN', 'Quản trị'
        QUAN_LY = 'QUAN_LY', 'Quản lý CRM'
        NV_CSKH = 'NV_CSKH', 'Nhân viên CSKH'
        KHACH_HANG = 'KHACH_HANG', 'Khách hàng'

    ho_ten = models.CharField(max_length=100, blank=True)
    so_dien_thoai = models.CharField(max_length=15, blank=True)
    vai_tro = models.CharField(max_length=20, choices=VaiTro.choices,
                               default=VaiTro.KHACH_HANG)
    ly_do_khoa = models.CharField(max_length=255, null=True, blank=True)
    ngay_khoa = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tai_khoan'
        verbose_name = 'Tài khoản'
        verbose_name_plural = 'Tài khoản'

    def __str__(self):
        return self.username
"""Dữ liệu demo khách hàng (TV4) – được gọi từ `python manage.py seed_data`.

Idempotent: khách hàng đã có (theo email) thì bỏ qua, không đổi mật khẩu/hồ sơ; kh40 chỉ bị khóa khi mới tạo (mở khóa rồi seed lại thì giữ nguyên).
"""

import random
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.models import Account

from .constants import BRAND_CHOICES, PLAY_STYLE_CHOICES, CustomerStatus, Gender, PlayingLevel, PreferenceType
from .models import Customer, CustomerPreference
from .selectors import years_ago

DEMO_CUSTOMER_COUNT = 40
DEMO_CUSTOMER_PASSWORD = "Khach@123"  # Chỉ dùng cho dữ liệu demo, không dùng cho tài khoản thật.
LOCKED_DEMO_INDEX = 40

LAST_NAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô"]
MALE_NAMES = [("Văn", "An"), ("Minh", "Khoa"), ("Đức", "Huy"), ("Quang", "Hải"), ("Hoàng", "Long"),
              ("Tuấn", "Kiệt"), ("Gia", "Bảo"), ("Thành", "Đạt"), ("Hữu", "Phước"), ("Công", "Danh")]
FEMALE_NAMES = [("Thị", "Bình"), ("Ngọc", "Lan"), ("Thu", "Trang"), ("Minh", "Thư"), ("Bảo", "Ngọc"),
                ("Thanh", "Hương"), ("Mỹ", "Linh"), ("Khánh", "Vy"), ("Hồng", "Nhung"), ("Phương", "Anh")]
CITIES = ["Quận 1, TP. Hồ Chí Minh", "Quận Bình Thạnh, TP. Hồ Chí Minh", "Thủ Đức, TP. Hồ Chí Minh",
          "Cầu Giấy, Hà Nội", "Đống Đa, Hà Nội", "Hải Châu, Đà Nẵng", "Ninh Kiều, Cần Thơ", "Biên Hòa, Đồng Nai"]
# Tuổi mẫu rải đủ các nhóm tuổi của báo cáo (<18 ... ≥55).
SAMPLE_AGES = [16, 19, 21, 23, 26, 28, 31, 33, 36, 39, 42, 46, 49, 53, 57, 62]
LEVELS = [PlayingLevel.BEGINNER, PlayingLevel.RECREATIONAL, PlayingLevel.RECREATIONAL, PlayingLevel.COMPETITIVE]


# tv4: email đăng nhập của khách hàng demo thứ i (kh01 ... kh40)
def demo_email(index):
    return f"kh{index:02d}@example.test"


# tv4: sinh hồ sơ khách hàng demo thứ i một cách cố định (cùng seed -> cùng dữ liệu)
def _demo_profile(index, rng, today):
    gender = Gender.OTHER if index % 11 == 0 else (Gender.MALE if index % 2 else Gender.FEMALE)
    middle, first = (FEMALE_NAMES if gender == Gender.FEMALE else MALE_NAMES)[index % 10]
    date_of_birth = None
    if index % 13 != 0:  # vài KH không khai ngày sinh để báo cáo có dòng "Chưa khai báo"
        age = SAMPLE_AGES[index % len(SAMPLE_AGES)]
        date_of_birth = years_ago(today, age) - timedelta(days=rng.randint(1, 300))
    return {
        "full_name": f"{LAST_NAMES[index % len(LAST_NAMES)]} {middle} {first}",
        "phone": f"0912{index:06d}",
        "date_of_birth": date_of_birth,
        "gender": gender,
        "address": CITIES[index % len(CITIES)],
        "playing_level": None if index % 17 == 0 else LEVELS[index % len(LEVELS)],
        "play_styles": rng.sample([v for v, _ in PLAY_STYLE_CHOICES], rng.randint(1, 2)),
        "brands": rng.sample([v for v, _ in BRAND_CHOICES], rng.randint(1, 3)),
        "days_ago": rng.randint(0, 365),  # ngày tạo rải trong 12 tháng gần nhất
    }


# tv4: tạo ≥ 40 khách hàng demo (kh01…kh40, kh40 bị khóa) kèm sở thích, ngày tạo rải 12 tháng; trả về số đã tạo
@transaction.atomic
def seed_customers(count=DEMO_CUSTOMER_COUNT, password=DEMO_CUSTOMER_PASSWORD):
    rng = random.Random(2026)
    today = timezone.localdate()
    now = timezone.now()
    password_hash = None
    created = 0
    for index in range(1, count + 1):
        profile = _demo_profile(index, rng, today)  # luôn sinh để giữ thứ tự random ổn định
        email = demo_email(index)
        account = Account.objects.filter(email=email).first()
        if account is None:
            # Chỉ đặt trạng thái khóa khi tạo mới, để mở khóa kh40 rồi seed lại không bị khóa lại.
            status = AccountStatus.LOCKED if index == LOCKED_DEMO_INDEX else AccountStatus.ACTIVE
            account = Account(email=email, role=AccountRole.CUSTOMER, status=status)
            if password_hash is None:
                # Băm một lần bằng Django hasher rồi dùng chung cho các tài khoản demo (cùng mật khẩu demo).
                validate_password(password, account)
                password_hash = make_password(password)
            account.password = password_hash
            account.save()
        if not Customer.objects.filter(account=account).exists():
            customer = Customer.objects.create(
                account=account, full_name=profile["full_name"], phone=profile["phone"],
                date_of_birth=profile["date_of_birth"], gender=profile["gender"], address=profile["address"],
                playing_level=profile["playing_level"], status=CustomerStatus.ACTIVE,
            )
            CustomerPreference.objects.bulk_create(
                [CustomerPreference(customer=customer, preference_type=PreferenceType.PLAY_STYLE, preference_value=v)
                 for v in profile["play_styles"]]
                + [CustomerPreference(customer=customer, preference_type=PreferenceType.BRAND, preference_value=v)
                   for v in profile["brands"]]
            )
            Customer.objects.filter(pk=customer.pk).update(created_at=now - timedelta(days=profile["days_ago"]))
            created += 1
    return created


# tv4: danh sách khách hàng demo theo thứ tự kh01…kh40 (để seed phản hồi)
def demo_customers(count=DEMO_CUSTOMER_COUNT):
    emails = [demo_email(i) for i in range(1, count + 1)]
    customers = {c.account.email: c for c in Customer.objects.select_related("account")
                 .filter(account__email__in=emails)}
    return [customers[e] for e in emails if e in customers]

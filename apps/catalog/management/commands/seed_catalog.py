from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Brand, Category, Product, Status, Supplier

SUPPLIERS = (
    ("SUP001", "Yonex Vietnam"), ("SUP002", "Lining Sports"),
    ("SUP003", "Victor Distribution"), ("SUP004", "Mizuno Sports"),
    ("SUP005", "Kawasaki Badminton"), ("SUP006", "Apacs Vietnam"),
)

CATEGORIES = (
    ("Badminton rackets", "Vợt cầu lông các dòng thiên công, thủ và toàn diện"),
    ("Badminton shoes", "Giày cầu lông"),
    ("Shuttlecocks", "Cầu lông thi đấu và tập luyện"),
    ("Badminton apparel", "Quần áo cầu lông"),
)

# (tên thương hiệu, mã nhà cung cấp, mô tả)
BRANDS = (
    ("Yonex", "SUP001", "Thương hiệu cầu lông Nhật Bản"),
    ("Lining", "SUP002", "Thương hiệu thể thao Trung Quốc"),
    ("Victor", "SUP003", "Thương hiệu cầu lông Đài Loan"),
    ("Mizuno", "SUP004", "Thương hiệu thể thao Nhật Bản"),
    ("Apacs", "SUP006", "Thương hiệu cầu lông Malaysia"),
)

# (danh mục, thương hiệu, tên sản phẩm, mô tả, giá VND)
PRODUCTS = (
    # --- Yonex ---
    ("Badminton rackets", "Yonex", "Yonex Astrox 88D Pro", "Vợt thiên công, đầu nặng, hợp đánh đôi nam cuối sân", "4200000"),
    ("Badminton rackets", "Yonex", "Yonex Astrox 99 Pro", "Vợt thiên công, đầu nặng, lực đập mạnh", "4300000"),
    ("Badminton rackets", "Yonex", "Yonex Arcsaber 11 Pro", "Vợt cân bằng, kiểm soát cầu tốt", "3800000"),
    ("Badminton rackets", "Yonex", "Yonex Nanoflare 800 Pro", "Vợt thiên tốc độ, đầu nhẹ, phản hồi nhanh", "4000000"),
    ("Badminton rackets", "Yonex", "Yonex Duora 10", "Vợt hai đầu, linh hoạt công thủ", "3500000"),
    ("Badminton shoes", "Yonex", "Yonex Power Cushion 65 Z3", "Giày đệm êm, bám sân tốt", "3200000"),
    ("Shuttlecocks", "Yonex", "Yonex Aerosensa 50", "Cầu lông vũ thi đấu, hộp 12 quả", "950000"),
    ("Badminton apparel", "Yonex", "Yonex Áo thi đấu nam", "Áo thun thoáng khí cho thi đấu", "650000"),
    # --- Lining ---
    ("Badminton rackets", "Lining", "Lining Axforce 80", "Vợt thiên công, khung cứng", "3300000"),
    ("Badminton rackets", "Lining", "Lining Windstorm 72", "Vợt nhẹ, linh hoạt, phù hợp người mới chơi", "1900000"),
    ("Badminton rackets", "Lining", "Lining Aeronaut 9000", "Vợt thiên công, đầu nặng", "3000000"),
    ("Badminton rackets", "Lining", "Lining Turbocharging 75", "Vợt thiên tốc độ, nhẹ", "2400000"),
    ("Badminton rackets", "Lining", "Lining Bladex 900", "Vợt cân bằng, bền", "2800000"),
    ("Badminton shoes", "Lining", "Lining Saga II", "Giày nhẹ, hỗ trợ di chuyển nhanh", "1800000"),
    ("Shuttlecocks", "Lining", "Lining A+60", "Cầu lông vũ tập luyện, hộp 12 quả", "700000"),
    ("Badminton apparel", "Lining", "Lining Áo thi đấu nam", "Áo thun thoáng khí, co giãn", "450000"),
    # --- Victor ---
    ("Badminton rackets", "Victor", "Victor Auraspeed 90S", "Vợt tốc độ, đầu nhẹ", "3300000"),
    ("Badminton rackets", "Victor", "Victor Thruster Ryuga II", "Vợt thiên công, đầu nặng", "3600000"),
    ("Badminton rackets", "Victor", "Victor Jetspeed S 12", "Vợt tốc độ, đầu nhẹ", "3200000"),
    ("Badminton rackets", "Victor", "Victor Drive X 9X", "Vợt cân bằng, đa dụng", "3100000"),
    ("Badminton rackets", "Victor", "Victor Brave Sword 12", "Vợt thiên công, dễ kiểm soát", "2800000"),
    ("Badminton shoes", "Victor", "Victor P9200", "Giày ổn định, hỗ trợ cổ chân", "2500000"),
    ("Shuttlecocks", "Victor", "Victor Gold No.1", "Cầu lông vũ, hộp 12 quả", "800000"),
    ("Badminton apparel", "Victor", "Victor Áo thi đấu nam", "Áo thun thoáng khí cho thi đấu", "500000"),
    # --- Mizuno ---
    ("Badminton rackets", "Mizuno", "Mizuno Fortius 10 Quick", "Vợt thiên tốc độ, đầu nhẹ", "2800000"),
    ("Badminton rackets", "Mizuno", "Mizuno Fortius 30 Power", "Vợt thiên công, đầu nặng", "3000000"),
    ("Badminton rackets", "Mizuno", "Mizuno Altius 01 Speed", "Vợt nhẹ, linh hoạt", "2500000"),
    ("Badminton rackets", "Mizuno", "Mizuno Altius 03 Feel", "Vợt cân bằng, cảm giác cầu tốt", "2600000"),
    ("Badminton rackets", "Mizuno", "Mizuno Acrospeed 5.0", "Vợt tầm trung cho người mới", "1800000"),
    ("Badminton shoes", "Mizuno", "Mizuno Wave Claw 2", "Giày nhẹ, linh hoạt", "2200000"),
    ("Shuttlecocks", "Mizuno", "Mizuno Cầu tập luyện", "Cầu tập luyện, hộp 12 quả", "600000"),
    ("Badminton apparel", "Mizuno", "Mizuno Áo thi đấu nam", "Áo thun thoáng khí, thấm hút tốt", "550000"),
    # --- Apacs ---
    ("Badminton rackets", "Apacs", "Apacs Nano Fusion Speed 722", "Vợt tầm trung, thiên tốc độ", "2200000"),
    ("Badminton rackets", "Apacs", "Apacs Feather Weight 55", "Vợt siêu nhẹ cho người mới", "1600000"),
    ("Badminton rackets", "Apacs", "Apacs Z-Ziggler", "Vợt thiên công, cứng", "2400000"),
    ("Badminton rackets", "Apacs", "Apacs Edgesaber 10", "Vợt cân bằng, đa dụng", "2000000"),
    ("Badminton rackets", "Apacs", "Apacs Virtuoso Pro", "Vợt thiên tốc độ, nhẹ", "2300000"),
    ("Badminton shoes", "Apacs", "Apacs Cushion Pro", "Giày đệm êm cho tập luyện", "1500000"),
    ("Shuttlecocks", "Apacs", "Apacs Cầu lông vũ", "Cầu lông vũ, hộp 12 quả", "650000"),
    ("Badminton apparel", "Apacs", "Apacs Áo thi đấu nam", "Áo thun thoáng khí cho tập luyện", "350000"),
)

# Link ảnh trực tiếp (kết thúc .jpg, .png hoặc .webp). Sản phẩm nào chưa có link thì để trống.
IMAGES = {
    # "Yonex Astrox 88D Pro": "https://...",
    # "Yonex Astrox 99 Pro": "https://...",
}

class Command(BaseCommand):
    help = "Create repeatable real catalog data: categories, brands, suppliers and products"

    @transaction.atomic
    def handle(self, *args, **options):
        suppliers = {}
        for code, name in SUPPLIERS:
            suppliers[code], _ = Supplier.objects.get_or_create(
                supplier_code=code, defaults={"supplier_name": name}
            )

        categories = {}
        for name, description in CATEGORIES:
            categories[name], _ = Category.objects.update_or_create(
                category_name=name,
                defaults={"description": description, "status": Status.ACTIVE},
            )

        brands = {}
        supplier_of_brand = {}
        for name, supplier_code, description in BRANDS:
            brands[name], _ = Brand.objects.update_or_create(
                brand_name=name,
                defaults={"description": description, "status": Status.ACTIVE},
            )
            supplier_of_brand[name] = suppliers[supplier_code]

        created = 0
        for category_name, brand_name, name, description, price in PRODUCTS:
            defaults = {
                "category": categories[category_name],
                "brand": brands[brand_name],
                "description": description,
                "price": Decimal(price),
                "status": Status.ACTIVE,
            }
            if name in IMAGES:
                defaults["image_url"] = IMAGES[name]
            _, was_created = Product.objects.update_or_create(
                product_name=name,
                supplier=supplier_of_brand[brand_name],
                defaults=defaults,
            )
            created += was_created

        self.stdout.write(self.style.SUCCESS(
            f"Catalog data ready: {len(PRODUCTS)} products ({created} new)."
        ))
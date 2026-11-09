from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Brand, Category, Product, Status
from apps.catalog.normalization import normalize_catalog

CATEGORIES = (
    ("Badminton rackets", "Vợt cầu lông các dòng thiên công, thủ và toàn diện"),
    ("Badminton shoes", "Giày cầu lông"),
    ("Shuttlecocks", "Cầu lông thi đấu và tập luyện"),
    ("Badminton apparel", "Quần áo cầu lông"),
    ("Badminton bags", "Túi và balo đựng vợt"),
    ("Accessories", "Quấn cán, dây cước và phụ kiện"),
)

BRANDS = (
    ("Yonex", "Thương hiệu cầu lông Nhật Bản"),
    ("Li-Ning", "Thương hiệu thể thao Trung Quốc"),
    ("Victor", "Thương hiệu cầu lông Đài Loan"),
    ("Mizuno", "Thương hiệu thể thao Nhật Bản"),
    ("Apacs", "Thương hiệu cầu lông Malaysia"),
)

# tv4: thương hiệu đã bị loại khỏi danh mục; seed sẽ xóa nếu không còn sản phẩm nào tham chiếu
REMOVED_BRANDS = ("Kumpoo",)

# Preserve the existing canonical catalog's availability, including hidden items.
INACTIVE_PRODUCTS = frozenset({"Mizuno Cầu tập luyện", "Apacs Cầu lông vũ"})

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
    ("Badminton rackets", "Li-Ning", "Li-Ning Axforce 80", "Vợt thiên công, khung cứng", "3300000"),
    ("Badminton rackets", "Li-Ning", "Li-Ning Windstorm 72", "Vợt nhẹ, linh hoạt, phù hợp người mới chơi", "1900000"),
    ("Badminton rackets", "Li-Ning", "Li-Ning Aeronaut 9000", "Vợt thiên công, đầu nặng", "4000000"),
    ("Badminton rackets", "Li-Ning", "Li-Ning Turbocharging 75", "Vợt thiên tốc độ, nhẹ", "2400000"),
    ("Badminton rackets", "Li-Ning", "Li-Ning Bladex 900", "Vợt cân bằng, bền", "2800000"),
    ("Badminton shoes", "Li-Ning", "Li-Ning Saga II", "Giày nhẹ, hỗ trợ di chuyển nhanh", "1800000"),
    ("Shuttlecocks", "Li-Ning", "Li-Ning A+60", "Cầu lông vũ tập luyện, hộp 12 quả", "700000"),
    ("Badminton apparel", "Li-Ning", "Li-Ning Áo thi đấu nam", "Áo thun thoáng khí, co giãn", "450000"),
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
    ("Badminton shoes", "Mizuno", "Mizuno Wave Claw 2", "Giày nhẹ, linh hoạt", "3200000"),
    ("Shuttlecocks", "Mizuno", "Mizuno Cầu tập luyện", "Cầu tập luyện, hộp 12 quả", "600000"),
    ("Badminton apparel", "Mizuno", "Mizuno Áo thi đấu nam", "Áo thun thoáng khí, thấm hút tốt", "450000"),
    # --- Apacs ---
    ("Badminton rackets", "Apacs", "Apacs Nano Fusion Speed 722", "Vợt tầm trung, thiên tốc độ", "2200000"),
    ("Badminton rackets", "Apacs", "Apacs Feather Weight 55", "Vợt siêu nhẹ cho người mới", "1600000"),
    ("Badminton rackets", "Apacs", "Apacs Z-Ziggler", "Vợt thiên công, cứng", "2400000"),
    ("Badminton rackets", "Apacs", "Apacs Edgesaber 10", "Vợt cân bằng, đa dụng", "2000000"),
    ("Badminton rackets", "Apacs", "Apacs Virtuoso Pro", "Vợt thiên tốc độ, nhẹ", "2300000"),
    ("Badminton shoes", "Apacs", "Apacs Cushion Pro", "Giày đệm êm cho tập luyện", "1500000"),
    ("Shuttlecocks", "Apacs", "Apacs Cầu lông vũ", "Cầu lông vũ, hộp 12 quả", "650000"),
    ("Badminton apparel", "Apacs", "Apacs Áo thi đấu nam", "Áo thun thoáng khí cho tập luyện", "350000"),
    # --- Badminton bags ---
    ("Badminton bags", "Yonex", "Yonex Pro Racquet Bag BA92226", "Túi vợt 6 cây, có ngăn giày riêng", "2100000"),
    ("Badminton bags", "Yonex", "Yonex Active Backpack BA82212", "Balo cầu lông gọn nhẹ, đựng 2 vợt", "950000"),
    ("Badminton bags", "Li-Ning", "Li-Ning ABJT005 Racquet Bag", "Túi vợt 6 cây, chống thấm nước", "1100000"),
    ("Badminton bags", "Li-Ning", "Li-Ning Backpack ABSS23", "Balo thể thao đựng vợt và quần áo", "650000"),
    ("Badminton bags", "Victor", "Victor BR9213 Racquet Bag", "Túi vợt 9 cây, ngăn giày thoáng khí", "1800000"),
    ("Badminton bags", "Victor", "Victor BR3025 Backpack", "Balo cầu lông đa ngăn, đựng 3 vợt", "1200000"),
    ("Badminton bags", "Mizuno", "Mizuno Racquet Bag 73GD", "Túi vợt 6 cây, vải bền chống mài mòn", "1300000"),
    ("Badminton bags", "Apacs", "Apacs AP-2188 Racquet Bag", "Túi vợt 6 cây cho tập luyện", "850000"),
    # --- Accessories ---
    ("Accessories", "Yonex", "Yonex Super Grap AC102 (3 cuộn)", "Quấn cán vợt thấm hút mồ hôi, bộ 3 cuộn", "95000"),
    ("Accessories", "Yonex", "Yonex Cước BG65 Titanium", "Cước đan vợt bền, độ nảy tốt", "130000"),
    ("Accessories", "Yonex", "Yonex Vớ thể thao cầu lông", "Vớ dày chống trượt, thấm hút mồ hôi", "120000"),
    ("Accessories", "Li-Ning", "Li-Ning GP20 Grip (5 cuộn)", "Quấn cán vợt mỏng, bộ 5 cuộn", "70000"),
    ("Accessories", "Li-Ning", "Li-Ning No.1 String", "Cước đan vợt tầm trung, cảm giác êm", "90000"),
    ("Accessories", "Li-Ning", "Li-Ning Băng bảo vệ cổ tay", "Băng cổ tay co giãn, thấm hút", "80000"),
    ("Accessories", "Victor", "Victor GR262 Grip", "Quấn cán vợt chống trượt", "85000"),
    ("Accessories", "Victor", "Victor VS-850 String", "Cước đan vợt độ bền cao", "110000"),
    ("Accessories", "Victor", "Victor Băng bảo vệ đầu gối", "Băng gối hỗ trợ khớp khi thi đấu", "220000"),
    ("Accessories", "Mizuno", "Mizuno Vớ cầu lông", "Vớ cổ ngắn, đệm êm gót chân", "110000"),
    ("Accessories", "Mizuno", "Mizuno Quấn cán Towel Grip", "Quấn cán dạng khăn, thấm hút tốt", "75000"),
    ("Accessories", "Apacs", "Apacs Quấn cán AP-3 (3 cuộn)", "Quấn cán vợt giá tốt, bộ 3 cuộn", "60000"),
    ("Accessories", "Apacs", "Apacs Cước Nano String", "Cước đan vợt cho người mới chơi", "80000"),
)

# Link ảnh trực tiếp (kết thúc .jpg, .png hoặc .webp). Sản phẩm nào chưa có link thì để trống.
IMAGES = {
    # "Yonex Astrox 88D Pro": "https://...",
    # "Yonex Astrox 99 Pro": "https://...",
    'Apacs Áo thi đấu nam': 'https://i.imgur.com/uES1S6c.jpeg',
    'Apacs Cushion Pro': 'https://i.imgur.com/eCAtV3F.jpeg',
    'Apacs Edgesaber 10': 'https://i.imgur.com/jv3ufh2.jpeg',
    'Apacs Feather Weight 55': 'https://i.imgur.com/t9Ovk0U.jpeg',
    'Apacs Nano Fusion Speed 722': 'https://i.imgur.com/DtsE3lD.jpeg',
    'Apacs Virtuoso Pro': 'https://i.imgur.com/02l3P1e.jpeg',
    'Apacs Z-Ziggler': 'https://i.imgur.com/6yXd346.jpeg',
    'Li-Ning A+60': 'https://i.imgur.com/Wu1mNuH.jpeg',
    'Li-Ning Aeronaut 9000': 'https://i.imgur.com/93F6k1G.jpeg',
    'Li-Ning Áo thi đấu nam': 'https://i.imgur.com/NFacQwV.jpeg',
    'Li-Ning Axforce 80': 'https://i.imgur.com/e0z4dBv.jpeg',
    'Li-Ning Bladex 900': 'https://i.imgur.com/CPs0pT4.jpeg',
    'Li-Ning Saga II': 'https://i.imgur.com/d5oihyp.jpeg',
    'Li-Ning Turbocharging 75': 'https://i.imgur.com/NqFuEKf.jpeg',
    'Li-Ning Windstorm 72': 'https://i.imgur.com/NjODJwE.jpeg',
    'Mizuno Acrospeed 5.0': 'https://i.imgur.com/4c4orId.jpeg',
    'Mizuno Altius 01 Speed': 'https://i.imgur.com/GsttcMO.jpeg',
    'Mizuno Altius 03 Feel': 'https://i.imgur.com/vaAtEUX.jpeg',
    'Mizuno Áo thi đấu nam': 'https://i.imgur.com/aOJdEMv.jpeg',
    'Mizuno Fortius 10 Quick': 'https://i.imgur.com/HXpI9bt.jpeg',
    'Mizuno Fortius 30 Power': 'https://i.imgur.com/xu5HUQn.jpeg',
    'Mizuno Wave Claw 2': 'https://i.imgur.com/WSROf0I.jpeg',
    'Victor Áo thi đấu nam': 'https://i.imgur.com/WrFioUJ.jpeg',
    'Victor Auraspeed 90S': 'https://i.imgur.com/cjyx7bK.jpeg',
    'Victor Brave Sword 12': 'https://i.imgur.com/wjB6oWu.jpeg',
    'Victor Drive X 9X': 'https://i.imgur.com/AY9sy0U.jpeg',
    'Victor Gold No.1': 'https://i.imgur.com/WUR6gNc.jpeg',
    'Victor Jetspeed S 12': 'https://i.imgur.com/LxQnsJ4.jpeg',
    'Victor P9200': 'https://i.imgur.com/hl6DGNB.jpeg',
    'Victor Thruster Ryuga II': 'https://i.imgur.com/uFe7miv.jpeg',
    'Yonex Aerosensa 50': 'https://i.imgur.com/6KdFcrG.jpeg',
    'Yonex Áo thi đấu nam': 'https://i.imgur.com/d2wCZYO.jpeg',
    'Yonex Arcsaber 11 Pro': 'https://i.imgur.com/9msX3aJ.jpeg',
    'Yonex Astrox 88D Pro': 'https://i.imgur.com/Xs2XCJ6.jpeg',
    'Yonex Astrox 99 Pro': 'https://i.imgur.com/XFEFPT0.jpeg',
    'Yonex Duora 10': 'https://i.imgur.com/juLsHih.jpeg',
    'Yonex Nanoflare 800 Pro': 'https://i.imgur.com/8mCquG1.jpeg',
    'Yonex Power Cushion 65 Z3': 'https://i.imgur.com/GFxsPzr.jpeg'
}

# tv4: ảnh minh họa dùng chung theo loại cho túi/balo và phụ kiện (chưa có ảnh riêng từng sản phẩm)
_BAG = "https://badminton-shop.com/wp-content/uploads/2022/09/Yonex-Pro-Racket-Bag-92326EX-X6-Grayish-Pearl.jpg"
_BACKPACK = "https://ksa.gosportme.com/cdn/shop/files/int_ba82412_black.jpg?v=1716438099"
_GRIP = "https://images.nexusapp.co/assets/ce/cb/c5/212170651.jpg"
_STRING = "https://racquetstore.com/cdn/shop/files/YonexAerobiteBadmintonStringReel.jpg?v=1755649671"
_SOCKS = "https://img.lazcdn.com/g/p/f27ed810d0cda1e2abfe6d7da31a8819.png_720x720q80.png"
_WRIST = "https://joybadminton.com/cdn/shop/collections/badminton-wrist-band-ac489ex-main2.jpg?v=1616179352"
_KNEE = "https://feelrecovery.com/wp-content/uploads/Knee-Brace-Support-Black-4-2-1024x1024.jpg"
IMAGES.update({
    "Yonex Pro Racquet Bag BA92226": _BAG, "Li-Ning ABJT005 Racquet Bag": _BAG,
    "Victor BR9213 Racquet Bag": _BAG, "Mizuno Racquet Bag 73GD": _BAG, "Apacs AP-2188 Racquet Bag": _BAG,
    "Yonex Active Backpack BA82212": _BACKPACK, "Li-Ning Backpack ABSS23": _BACKPACK, "Victor BR3025 Backpack": _BACKPACK,
    "Yonex Super Grap AC102 (3 cuộn)": _GRIP, "Li-Ning GP20 Grip (5 cuộn)": _GRIP, "Victor GR262 Grip": _GRIP,
    "Mizuno Quấn cán Towel Grip": _GRIP, "Apacs Quấn cán AP-3 (3 cuộn)": _GRIP,
    "Yonex Cước BG65 Titanium": _STRING, "Li-Ning No.1 String": _STRING, "Victor VS-850 String": _STRING,
    "Apacs Cước Nano String": _STRING,
    "Yonex Vớ thể thao cầu lông": _SOCKS, "Mizuno Vớ cầu lông": _SOCKS,
    "Li-Ning Băng bảo vệ cổ tay": _WRIST, "Victor Băng bảo vệ đầu gối": _KNEE,
})


class Command(BaseCommand):
    help = "Create repeatable real catalog data: categories, brands and products"

    @transaction.atomic
    def handle(self, *args, **options):
        normalize_catalog(apply=True)
        categories = {}
        for name, description in CATEGORIES:
            categories[name], _ = Category.objects.update_or_create(
                category_name=name,
                defaults={"description": description, "status": Status.ACTIVE},
            )

        brands = {}
        for name, description in BRANDS:
            brands[name], _ = Brand.objects.update_or_create(
                brand_name=name,
                defaults={"description": description, "status": Status.ACTIVE},
            )

        # tv4: xóa thương hiệu đã loại bỏ (Kumpoo) nếu không còn sản phẩm tham chiếu
        for removed in REMOVED_BRANDS:
            if not Product.objects.filter(brand__brand_name=removed).exists():
                Brand.objects.filter(brand_name=removed).delete()

        created = 0
        for category_name, brand_name, name, description, price in PRODUCTS:
            defaults = {
                "category": categories[category_name],
                "brand": brands[brand_name],
                "description": description,
                "price": Decimal(price),
                "status": Status.INACTIVE if name in INACTIVE_PRODUCTS else Status.ACTIVE,
            }
            if name in IMAGES:
                defaults["image_url"] = IMAGES[name]
            _, was_created = Product.objects.update_or_create(
                product_name=name,
                defaults=defaults,
            )
            created += was_created

        self.stdout.write(self.style.SUCCESS(
            f"Catalog data ready: {len(PRODUCTS)} products ({created} new)."
        ))

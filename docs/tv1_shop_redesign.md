# TV1 shop redesign — bản thử 2026-10-12

Nhánh `feature/tv1-shop-redesign` tạo sau fetch từ `origin/develop` tại `6dc4372`.
Working tree ban đầu sạch. Thực hiện trong worktree Codex hiện có; checkout chính
`D:/Desktop/crm_project` vẫn sạch trên `develop`. Lưu commit cục bộ; không push,
tạo PR, merge hoặc bật auto-merge.

## Giao diện

- Header trắng, GET search bằng `q`, menu tài khoản native `details`, POST logout/
  CSRF và Escape đóng menu. Thanh danh mục chỉ lấy Category ACTIVE từ DB.
- Home có SVG sân cầu lông gốc, danh mục và tám Product ACTIVE đầu tiên theo thứ
  tự hiện có. Card bốn cột desktop, hai cột ở mobile từ 360px, một cột dưới 360px.
- Catalogue có sidebar desktop và filter mobile thu gọn bằng JavaScript cục bộ.
  Khi JS không chạy, filter vẫn mở và gửi GET bình thường. Giữ `q`, `category`,
  `brand`, `min_price`, `max_price`, validation, 12 sản phẩm/trang và query pagination.
  Category và Brand là hai trường riêng.
- Card/detail hiển thị brand, tên, danh mục, giá và ảnh minh họa cân đối. Decimal
  nguyên: `1.250.000 ₫`; phần lẻ được giữ: `1.250.000,50 ₫`.
- Detail có breadcrumb, thông tin và mô tả. Product ACTIVE thuộc Category INACTIVE
  vẫn hiển thị theo selector cũ; category chỉ là text, CTA về catalogue chung để
  tránh link filter trả 400.
- Đồng bộ login/register, password change/reset và customer profile. Giữ field
  names, actions, CSRF, errors, immutable email, ownership và permission guards.

## Phạm vi và tài sản

Không đổi model/migration/SQL/URL/API/auth/service/permission/seed. Không sửa
Admin/CRM templates, CSS hoặc business modules của TV2/TV3/TV4/TV5. CSS đều nằm
dưới `.customer-layout`; tái dùng Bootstrap cục bộ. Không thêm dependency/build,
giỏ hàng, thanh toán, giảm giá, reviews hoặc tồn kho giả.

Product không có field ảnh. `shop-*.svg` là minh họa gốc theo loại, không ảnh mẫu
hàng/brand cụ thể. Match danh mục rõ nghĩa tiếng Việt/English, gồm `Demo Rackets`
đang có; danh mục không nhận diện dùng generic. Không đoán từ product_name/brand.
Giữ mọi dữ liệu demo, kể cả tên dài của fixture cũ. Nguồn/provenance và tham khảo
[VNB](https://shopvnb.com/), [FBShop](https://fbshop.vn/) ghi tại
[README.shop.md](../static/images/README.shop.md). Không lấy ảnh/brand/code từ các shop.

## Kiểm chứng thực tế

Windows CPython 3.12.10, Django 5.2.17, MySQL hiện có. `.env` và local settings sao
chép từ checkout chính, vẫn ignored; DB demo là `crm_tv1_demo`. `showmigrations`
read-only xác nhận toàn bộ đã apply. Không migrate/seed/reset/restore DB demo.

```powershell
python manage.py check --settings=config.local_settings
python manage.py makemigrations --check --dry-run --settings=config.local_settings
python manage.py showmigrations --settings=config.local_settings
python manage.py test --settings=config.test_settings --keepdb --noinput
python manage.py test apps.shop apps.accounts.tests.test_layouts --settings=config.test_settings --keepdb --noinput
git diff --check
```

- Check 0 issues; dry-run No changes detected; diff không lỗi whitespace.
- Full suite **211/211 passed**, 205.067s, MySQL **test_crm_db**.
- Sau review thêm regression Product ACTIVE/Category INACTIVE và mở filter mặc
  định cho no-JS: focused shop/layout **20/20 passed**, 0.270s. Không báo full suite
  212/212; full suite đã chạy trước regression cuối.
- Focused đầu 60/61: một assertion text cũ đòi menu khảo sát “Sắp có”, đã cập nhật.
- Browser demo: search, combined category/brand/price filters, pagination giữ query,
  detail, empty search, reversed-price error, login/register layouts, menu. Home
  320/390/768/1024/1280px không tràn ngang; catalogue desktop bốn cột, mobile 390px
  hai cột và filter đóng mặc định.
- Login sai/đúng, profile save/checkbox/message/logout và Admin login/account list
  bằng server tạm 8002 trên **test_crm_db**. Hai Account, một Customer, hai Category
  tổng hợp được tạo chỉ cho browser test rồi dọn đúng IDs và sessions. Server,
  settings/credential files tạm đã dọn. Không dùng/sửa tài khoản demo cho kiểm tra.
- Keyboard focus card/menu có outline cam; Escape đóng menu và trả focus về
  summary. Các cặp chữ chính trong palette đạt ít nhất 4.8:1. Profile/login/register/
  filter-error mobile không tràn ngang. Admin giữ layout/CSS và regression riêng;
  không đổi responsive Admin hiện có.
- Ảnh viewport lưu ngoài repo trong visualizations của chat. Full-page capture
  không ổn định nên dùng viewport. Chưa kiểm tra điện thoại vật lý, mọi browser
  hoặc SMTP delivery.

## Chạy thử và quay lại develop

Xem [bản thử cổng 8001](http://127.0.0.1:8001/). Nếu preview Codex còn chạy, dừng PID
ghi trong phần bàn giao trước khi tự khởi động lại trên cùng cổng:

```powershell
Set-Location C:/Users/Khiem/.codex/worktrees/44c0/crm_project
$env:PYTHONIOENCODING = 'utf-8'
python manage.py runserver 127.0.0.1:8001 --settings=config.local_settings
```

Đăng nhập bằng tài khoản demo hiện có. Không cần migrate/seed.

Trên máy này `develop` đã checkout ở repo chính, nên không switch develop trong
worktree thử. Dừng preview rồi quay lại repo chính; nhánh thử vẫn được giữ:

```powershell
Set-Location D:/Desktop/crm_project
git branch --show-current  # develop
$env:PYTHONIOENCODING = 'utf-8'
python manage.py runserver 127.0.0.1:8001 --settings=config.local_settings
```

Quay lại bản thử bằng Set-Location về worktree phía trên. Trên máy không có
develop ở worktree khác, với working tree sạch dùng `git switch develop` /
`git switch feature/tv1-shop-redesign` bình thường.

# crm_project

Website bán đồ cầu lông tích hợp CRM. Django 5.2, MySQL 8.x, Django Templates.

Phần TV1 trên nhánh `feature/tv1-auth-customer` được xây từ develop `ee13e42`.
Không cần gộp nhánh TV2/TV4/TV5 để chạy auth, hồ sơ cá nhân và cửa hàng.

## Chạy ứng dụng

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Điền SECRET_KEY và thông tin MySQL thực tế vào `.env`; không commit file này.
DB_NAME phải là `crm_db`. Dùng database đã được chủ nhóm khởi tạo đúng migrations
của revision hiện tại. Chỉ với database mới, rỗng và được chỉ định cho phát triển,
người quản lý DB mới chạy `python manage.py migrate`; không chạy lại dump,
migrate, seed, flush hoặc restore máy móc trên DB chung.

```powershell
python manage.py check
python manage.py showmigrations
python manage.py migrate --plan
python manage.py runserver
```

Giữ một hostname duy nhất khi demo, ví dụ `http://127.0.0.1:8000`.
Account email bất biến, role chỉ ADMIN/CUSTOMER. Quyền CRM dùng Groups
CRM_MANAGER/CUSTOMER_SERVICE; TV1 không cung cấp màn hình tự gán nhóm.

## URLs TV1

| URL | Chức năng / quyền |
| --- | --- |
| `/` | Trang chủ cửa hàng, công khai |
| `/products/` | Danh sách, tìm tên, lọc và phân trang, công khai |
| `/products/<product_id>/` | Chi tiết sản phẩm ACTIVE, công khai |
| `/login/` | Đăng nhập khách hàng/CRM/ADMIN |
| `/logout/` | Đăng xuất, chỉ POST + CSRF |
| `/register/` | Tạo Account CUSTOMER ACTIVE và Customer cùng transaction |
| `/crm/` | ACTIVE ADMIN hoặc nhóm CRM_MANAGER/CUSTOMER_SERVICE |
| `/account/profile/` | ACTIVE CUSTOMER, chỉ hồ sơ ACTIVE của chính mình |
| `/account/password/change/` | Account ACTIVE, yêu cầu mật khẩu hiện tại |
| `/password/reset/` | Yêu cầu liên kết reset, phản hồi không tiết lộ email tồn tại |
| `/password/reset/done/` | Xác nhận đã nhận yêu cầu |
| `/password/reset/<uidb64>/<token>/` | Đặt mật khẩu qua token Django |
| `/password/reset/complete/` | Xác nhận reset thành công |

Admin Portal giữ nguyên `/admin-portal/login/`, `/admin-portal/logout/`,
`/admin-portal/`; `/admin/`, `/api/docs`, `/api/auth/*`, `/api/accounts/*` vẫn tồn tại.
Tên URL `login`/`logout` cũ vẫn thuộc admin; TV1 dùng namespace `customer_auth`.
LOGIN_URL mới là `customer_auth:login`, guard admin riêng vẫn dùng route admin.

Đăng nhập không có `next`: ADMIN → `/admin-portal/`, nhóm CRM → `/crm/`,
CUSTOMER → `/`. `next` chỉ nhận route GET nội bộ nằm trong allowlist và phù hợp
quyền; bỏ qua URL ngoài site, route auth gây vòng lặp, route chưa có và thao tác POST.
Tài khoản LOCKED không dùng được trang bảo vệ qua session cũ.
Chỉ thông báo khóa tại login sau khi mật khẩu đã được xác minh.

## Email và mật khẩu

DEBUG=True mặc định dùng console backend khi EMAIL_BACKEND chưa đặt. Ví dụ:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@example.test
```

Yêu cầu reset và lấy liên kết trong console server ở môi trường phát triển.
Liên kết có hiệu lực 1 giờ; không dùng lại sau khi đổi mật khẩu/login làm token mất
hiệu lực. Reset không tự đăng nhập, không mở khóa và vô hiệu các session cũ.
Đổi mật khẩu giữ session đang thao tác và vô hiệu các session khác.
Không gửi mật khẩu thô; console reset link chỉ dùng cục bộ, không đưa vào báo cáo.

Email thật cần SMTP được nhà cung cấp cấp phép và cấu hình riêng, ví dụ:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_HOST_USER=<smtp-user>
EMAIL_HOST_PASSWORD=<smtp-password>
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=<verified-sender>
```

Không bật TLS và SSL cùng lúc. Gửi SMTP thật chưa được kiểm chứng trong task này.
Cơ chế reset kế thừa [Django authentication views](https://docs.djangoproject.com/en/5.2/topics/auth/default/),
chỉ tùy biến lọc ACTIVE vì Account.is_active là property.

## Contract hồ sơ và sản phẩm

Hồ sơ nhận `full_name`, `phone`, `date_of_birth`, `gender`, `address`,
`playing_level`; các ID/account/email/role/status/groups/permissions không writable.
Sở thích dùng formset `preferences`, nhận `preference_type`, `preference_value`
và DELETE với kiểm tra quyền sở hữu ID ở service. Thêm một dòng sau mỗi lần lưu,
tối đa 50 dòng trong một lần gửi; giới hạn này bảo vệ kích thước form, không sửa DB.
Quy ước seed hiện có là `CATEGORY` / tên danh mục, ví dụ `Badminton rackets`.
Model chưa chốt enum cho gender/playing_level/preference nên giữ văn bản theo độ
dài schema, không đặt bộ giá trị mới. Điện thoại nhận 9–15 chữ số và dấu định dạng;
ngày sinh phải hợp lệ và không ở tương lai.

Cửa hàng chỉ đọc `Product.status=ACTIVE`, không suy ra trạng thái bán từ tồn kho
hay thêm cột. Bộ lọc `q`, `category`, `brand`, `min_price`, `max_price`, `page`;
12 sản phẩm/trang, thứ tự product_id ổn định. ID lọc phải có trong danh mục/thương
hiệu ACTIVE; giá dùng Decimal không âm và có tối đa 2 số lẻ; khoảng giá sai trả 400
kèm lỗi form. Chi tiết không tồn tại hoặc INACTIVE trả 404.
Bootstrap 5.3.3 CSS và placeholder SVG nằm trong static, không cần CDN.
Phản hồi/khảo sát và các module CRM chưa có landing phù hợp hiển thị “Sắp có”.

## Kiểm thử

MySQL user cần quyền tạo/đọc/ghi `test_crm_db`, tách khỏi `crm_db`.
`config.test_settings` chỉ định TEST.NAME=`test_crm_db`, UTF-8 và email locmem.
Test runner áp dụng migrations thật lên DB test; không fake hay bỏ migrations.
DB này dành riêng kiểm thử, không chứa dữ liệu cần bảo toàn. Không chạy đồng thời
nhiều test runner dùng cùng test_crm_db.

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.accounts.tests.test_customer_auth apps.customers apps.shop --settings=config.test_settings --keepdb --noinput
python manage.py test --settings=config.test_settings --keepdb --noinput
```

Lệnh trên đã chạy bằng Python 3.12.10 / Django 5.2.17 / mysqlclient 2.3.0.
Kết quả và giới hạn môi trường ghi trong `plans.md`.
Review trước PR chạy lại toàn bộ suite: **144/144 passed trong 175.004 giây**,
check 0 lỗi và không có migration mới. Kết quả này bao gồm regression API/admin;
chưa thay thế smoke test trên database demo mới đang thiếu quyền.

## Demo và bàn giao

Demo TV1 dùng MySQL database **`crm_tv1_demo`**, độc lập với `crm_db` legacy và
`test_crm_db` (chỉ dùng automated tests). Cấu hình máy ở
`config/local_settings.py` được Git bỏ qua; không đổi `.env` hoặc settings mặc định
của nhóm để chuyển DB demo. Nếu chưa có file này, tạo cục bộ:

```python
from copy import deepcopy
from .settings import *

DATABASES = deepcopy(DATABASES)
DATABASES['default']['NAME'] = 'crm_tv1_demo'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Tài khoản MySQL đọc từ `.env` cần quyền CREATE/DDL/DML trên `crm_tv1_demo`.
Người quản trị MySQL có thể cấp quyền vào **DB demo này**:

```sql
GRANT ALL PRIVILEGES ON crm_tv1_demo.* TO 'crm_user'@'localhost';
CREATE DATABASE crm_tv1_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Chỉ CREATE khi tên DB chưa tồn tại; nếu đã có thì kiểm tra trước, không DROP/reset.
Sau khi DB mới được tạo và vẫn rỗng, dùng đúng settings demo để xem kế hoạch,
apply migrations hiện có và chạy server:

```powershell
python manage.py migrate --plan --settings=config.local_settings
python manage.py migrate --settings=config.local_settings
python manage.py check --settings=config.local_settings
python manage.py runserver 127.0.0.1:8000 --settings=config.local_settings
```

Không chạy test runner với local_settings vì dữ liệu demo cần được giữ lại.
Khách hàng có thể đăng ký qua `/register/`; ADMIN tạo bằng
`python manage.py createsuperuser --settings=config.local_settings` (nhập mật khẩu
tại prompt, không đặt trong argv/source). Người quản trị cấp nhóm
CRM_MANAGER/CUSTOMER_SERVICE cho Account demo qua quy trình quản trị riêng;
không thêm role mới. Sản phẩm demo tạo bằng chức năng catalog hiện có trên DB demo.
Không sao chép dữ liệu cá nhân từ DB chung vào demo.

**Trạng thái lần review trước PR:** tạo `crm_tv1_demo` bị MySQL từ chối (1044)
vì crm_user chỉ có quyền trên crm_db và test_crm_db. Cấu hình demo cục bộ đã sẵn
sàng; chưa migrate hoặc chạy browser smoke test trên DB demo mới. Không lấy kết
quả automated tests hay lần browser trên DB test trước đó làm kết quả demo.

Trên DB phát triển đã khớp schema: mở `/`, lọc sản phẩm; đăng ký một khách hàng;
đăng nhập, cập nhật hồ sơ/sở thích; đổi mật khẩu; đăng xuất bằng nút POST; yêu cầu
reset và dùng console link. Dùng Account có nhóm CRM do người quản lý cấp sẵn để
xem `/crm/`; ADMIN vẫn vào Admin Portal hiện có. Không chạy seed trong task TV1.

**Giới hạn tại máy khảo sát 2026-10-08:** live `crm_db` còn bảng auth legacy và
chưa khớp models develop. Check source thành công không chứng minh live DB dùng
được. Chủ DB cần xử lý riêng bằng quy trình backup/migration đã duyệt trước demo;
TV1 không reset hoặc migrate DB đó. Kiểm thử TV1 dùng MySQL test schema riêng.

Bàn giao: [docs/tv1_handoff.md](docs/tv1_handoff.md).
Kế hoạch: [docs/15_week_plan.md](docs/15_week_plan.md).
Báo cáo: [docs/chapter4.md](docs/chapter4.md).

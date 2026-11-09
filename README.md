# CRM Shop Cầu Lông

Đồ án môn **Hệ thống thông tin doanh nghiệp** (841065) — Đại học Sài Gòn (SGU), HK1 2026–2027.
Website bán đồ cầu lông tích hợp hệ thống quản lý quan hệ khách hàng (CRM).

- Công nghệ: Python 3.12, Django 5.2, MySQL 8.x, Django Templates + Bootstrap 5, Chart.js
- Repository: https://github.com/KhimTran/crm_project

## Nhóm thực hiện

| TV | Họ tên | MSSV | Phụ trách |
| --- | --- | --- | --- |
| TV1 | Trần Trọng Duy Khiêm | 3123411153 | Nhóm trưởng; nền tảng, xác thực, giao diện khách hàng, tích hợp, tổng hợp báo cáo |
| TV2 | Nguyễn Công Vinh | 3123411341 | Danh mục sản phẩm, loại sản phẩm, thương hiệu; khảo sát doanh nghiệp |
| TV3 | Trần Thị Quỳnh Như | 3123411214 | Tài khoản, phân quyền, CSDL, sao lưu/phục hồi, giao diện Admin |
| TV4 | Huỳnh Phúc Hoàng Nhật | 3123411208 | Khách hàng, phản hồi, báo cáo khách hàng, phân tích hệ thống |
| TV5 | Nguyễn Minh | 3123411188 | Khảo sát khách hàng, thống kê kết quả, sơ đồ luồng dữ liệu |

## Chức năng chính

- **Khách hàng** (`/login/`): xem/lọc sản phẩm, đăng ký, hồ sơ cá nhân, gửi phản hồi, làm khảo sát.
- **Manager** (`/manager/login/`): quản lý sản phẩm, danh mục, thương hiệu; CRM gồm khách hàng, báo cáo, phản hồi, khảo sát.
- **Admin** (`/admin/login/`): quản lý tài khoản (tạo, xóa, khóa/mở khóa, đặt lại mật khẩu, phân quyền) và công cụ database (backup/restore).

## Yêu cầu cài đặt

- Python 3.12, MySQL Server 8.x (đã thử trên 8.4), Git
- Tài khoản MySQL có quyền tạo bảng trên database `crm_db`

## Cài đặt và chạy

**1. Lấy mã nguồn và cài thư viện** (PowerShell, Windows)

```powershell
git clone https://github.com/KhimTran/crm_project.git
cd crm_project
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

**2. Tạo database rỗng** (đăng nhập MySQL bằng tài khoản quản trị)

```sql
CREATE DATABASE crm_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON crm_db.* TO '<user>'@'localhost';
```

**3. Sửa file `.env`**: điền `SECRET_KEY`, `DB_USER`, `DB_PASSWORD` (giữ `DB_NAME=crm_db`, `DB_HOST=127.0.0.1`, `DB_PORT=3306`) và `MYSQL_BIN` là thư mục `bin` của MySQL trên máy bạn (dùng cho backup/restore). Không commit file `.env`.

**4. Nạp dữ liệu — chọn MỘT trong hai cách, không kết hợp trên cùng database**

*Cách A (khuyến nghị): migrations + seed*

```powershell
python manage.py migrate
python manage.py seed_demo
```

*Cách B: import bản dump có sẵn* vào database rỗng (không chạy `migrate`/`seed_demo` trước đó):

```sql
SOURCE <đường-dẫn>/crm_project/database/crm_db.sql;
```

**5. Chạy server**

```powershell
python manage.py check
python manage.py runserver
```

Mở http://127.0.0.1:8000 (dùng một hostname duy nhất khi demo).

## Tài khoản demo

Mật khẩu chung: **`Crm@2026`** (chỉ dùng cho demo, dữ liệu giả lập).

| Vai trò | Email | Trang đăng nhập |
| --- | --- | --- |
| Admin (2) | `admin1@demo.test`, `admin2@demo.test` | `/admin/login/` |
| Manager (3) | `manager1@demo.test` … `manager3@demo.test` | `/manager/login/` |
| Khách hàng (15) | `cus1@demo.test` … `cus15@demo.test` | `/login/` |

Dữ liệu demo: 20 tài khoản, 40 sản phẩm (6 danh mục, 6 thương hiệu), 20 phản hồi, 18 khảo sát (61 lượt trả lời).
Trang chủ: `/` · Django Admin mặc định (chỉ để phát triển): `/django-admin/`.

## Backup / Restore

- Vào `/admin/login/` → mục **Database Tools** (`/admin/database/`): tạo bản sao lưu, tải về và khôi phục.
- File sao lưu lưu trong `database/backups/` (không đưa lên Git). Khi restore, hệ thống yêu cầu gõ đúng tên database đích và tự tạo bản sao lưu trước khi khôi phục.
- Cần cấu hình đúng `MYSQL_BIN` trong `.env`. Không restore lên database đang có dữ liệu thật.
- Kế hoạch sao lưu chi tiết xem trong báo cáo (chương 4).

## Kiểm thử

Cần MySQL user có quyền tạo `test_crm_db` (tách khỏi `crm_db`):

```powershell
python manage.py test --settings=config.test_settings --keepdb --noinput
```

## Cấu trúc thư mục

```
apps/accounts      Tài khoản, vai trò, đăng nhập, phân quyền
apps/admin_portal  Giao diện Admin và Manager
apps/catalog       Sản phẩm, danh mục, thương hiệu (+ lệnh seed_demo)
apps/customers     Hồ sơ khách hàng, sở thích, báo cáo khách hàng
apps/feedback      Phản hồi của khách hàng
apps/surveys       Khảo sát
apps/shop          Trang cửa hàng cho khách hàng
config/            Cấu hình Django (settings, urls)
database/          crm_db.sql (dump demo), backups/
docs/              Tài liệu hướng dẫn, báo cáo
templates/ static/ Giao diện và tài nguyên tĩnh
```

## Cơ sở dữ liệu

MySQL `crm_db`, utf8mb4: 14 bảng nghiệp vụ — `roles`, `accounts`, `categories`, `brands`, `products`, `customer_preferences`, `feedbacks`, `surveys`, `survey_questions`, `survey_options`, `survey_recipients`, `survey_responses`, `survey_answers` — cộng các bảng kỹ thuật của Django. Khách hàng là tài khoản có vai trò CUSTOMER (không có bảng `customers` riêng).

## Lưu ý

- Chỉ chạy `migrate`/`seed_demo`/import/restore trên database **mới, rỗng, dành cho phát triển**.
- Không chạy các lệnh seed lịch sử: `seed_data`, `seed_surveys`, `seed_survey_report_demo`.
- Không commit `.env`, mật khẩu MySQL hoặc dữ liệu thật.
- Hướng dẫn chi tiết hơn: [docs/HUONG_DAN_CHAY_DO_AN.md](docs/HUONG_DAN_CHAY_DO_AN.md).

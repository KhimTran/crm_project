# Thiết lập bộ demo CRM cuối cùng

Django 5.2 + MySQL 8.x. Chỉ dùng database phát triển mới, trống, đã cấu hình
trong `.env`. Không commit `.env`, mật khẩu MySQL hoặc dữ liệu thật.
Không chạy migrate/seed/import/restore/reset trên database dùng chung hoặc có dữ liệu thật.
Chọn **một** trong hai cách dưới đây, không kết hợp hai cách nạp trên cùng database.

## A. Migrations + Seed (khuyến nghị)

```powershell
git pull origin develop
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py check
python manage.py runserver
```

Tạo database MySQL rỗng bằng tài khoản quản trị của bạn, charset `utf8mb4`,
collation `utf8mb4_unicode_ci`, rồi cấu hình DB_NAME/DB_HOST/DB_PORT/DB_USER/DB_PASSWORD
và MYSQL_BIN trong `.env` trước khi chạy. Không dùng `CREATE DATABASE IF NOT EXISTS`
để bỏ qua việc xác minh database có thực sự rỗng hay không.

`seed_demo` là lệnh setup duy nhất. Không chạy thêm `seed_data`, `seed_surveys`,
`seed_survey_report_demo`: đây là các bộ fixture lịch sử độc lập, tạo thêm khách hàng/khảo sát.
Seed không chạy khi khởi động server. Seed chạy lại giữ nguyên bản ghi đã có và
Catalog hiện tại, không reset mật khẩu hay xóa dữ liệu ngoài bộ demo. Email demo
xung đột role/status/password sẽ làm lệnh thất bại và rollback, không ghi đè account.
Số lượng toàn DB chỉ đúng trên database demo sạch; seed không xóa dữ liệu ngoài phạm vi để ép số lượng.

## B. Restore Full Backup

Pull source và cài dependencies như cách A. Tạo một database **mới, rỗng**, cấu hình
`.env` trỏ đúng database đó. Không chạy migrations + seed trước khi restore full dump.
Full dump đã chứa schema, indexes, constraints, dữ liệu và migration history.

File Full Backup chuẩn: `database/backups/crm_YYMMDD_HHMMSS.sql`; manifest nằm ngay cạnh,
tên `crm_YYMMDD_HHMMSS.sql.json`. Chỉ dùng file đã VERIFIED và đối chiếu checksum:

Bản bàn giao đã restore kiểm chứng: `crm_261104_135013.sql`, 181755 bytes.
SHA-256: `b0234fd76d0158879ee6edac2c154252bdb034097d2190e3f7173df8ae5fadeb`.
Chỉ dùng `database/backups/` cho SQL backup và manifest. Các snapshot cũ đã được
xóa sau khi chủ dự án cho phép thay toàn bộ dữ liệu local và restore thành công.
Backup trước restore cũng nằm tại đây; chỉ dọn sau khi đã xác minh restore/recovery.

```powershell
Get-FileHash database/backups/crm_YYMMDD_HHMMSS.sql -Algorithm SHA256
Get-Content database/backups/crm_YYMMDD_HHMMSS.sql.json
& "$env:MYSQL_BIN/mysql.exe" -h 127.0.0.1 -u <your-user> -p <new-database>
```

Trong MySQL prompt (thay đường dẫn bằng file thực tế, dùng `/`):

```sql
SOURCE E:/path/crm_project/database/backups/crm_YYMMDD_HHMMSS.sql;
```

`database/crm_db.sql` là canonical full dump cùng dataset, có thể dùng thay backup.
`database/seed_survey_report.sql` là data-only tương thích schema đã migrate, chỉ
dành cho DB demo trống; không cần import file này sau `seed_demo` hoặc full restore.
Không import data-only vào DB chứa dữ liệu khác vì SQL snapshot dùng IDs của bản xuất.
Import seed SQL lần hai giữ nguyên dữ liệu, nhưng không phải công cụ hợp nhất dữ liệu người dùng.

Sau restore:

```powershell
python manage.py check
python manage.py showmigrations
python manage.py migrate --plan
python manage.py runserver
```

Migration plan phải không còn thao tác. Không dùng `--fake` hoặc sửa migration history.
Admin Backup/Restore UI ở `/admin/database/` yêu cầu Admin, CSRF và xác nhận chính xác
database đích; restore tạo recovery backup trước khi import. Không thực hiện trên DB thật để thử demo.
Hai backup cùng giây bị từ chối an toàn; đợi sang giây tiếp theo rồi thử lại.

## Tài khoản demo công khai

Mật khẩu chung: **`Crm@2026`**, chỉ dành cho demo giả lập. Database lưu Django hash.

| Email | Role | URL đăng nhập |
| --- | --- | --- |
| `admin1@demo.test` | ADMIN | `/admin/login/` |
| `admin2@demo.test` | ADMIN | `/admin/login/` |
| `manager1@demo.test` | MANAGER | `/manager/login/` |
| `manager2@demo.test` | MANAGER | `/manager/login/` |
| `manager3@demo.test` | MANAGER | `/manager/login/` |
| `cus1@demo.test` | CUSTOMER | `/login/` |
| `cus2@demo.test` | CUSTOMER | `/login/` |
| `cus3@demo.test` | CUSTOMER | `/login/` |
| `cus4@demo.test` | CUSTOMER | `/login/` |
| `cus5@demo.test` | CUSTOMER | `/login/` |
| `cus6@demo.test` | CUSTOMER | `/login/` |
| `cus7@demo.test` | CUSTOMER | `/login/` |
| `cus8@demo.test` | CUSTOMER | `/login/` |
| `cus9@demo.test` | CUSTOMER | `/login/` |
| `cus10@demo.test` | CUSTOMER | `/login/` |
| `cus11@demo.test` | CUSTOMER | `/login/` |
| `cus12@demo.test` | CUSTOMER | `/login/` |
| `cus13@demo.test` | CUSTOMER | `/login/` |
| `cus14@demo.test` | CUSTOMER | `/login/` |
| `cus15@demo.test` | CUSTOMER | `/login/` |

Mọi account ACTIVE. Manager có role MANAGER thật; không dùng Customer gắn nhóm để thay thế.

## Số liệu và kiểm tra

2 Admin + 3 Manager + 15 Customer = 20 Account; 45 preferences; Catalog chuẩn
40 sản phẩm (38 ACTIVE, 2 INACTIVE), 6 danh mục, 6 thương hiệu; giá, ảnh và trạng thái
giữ theo Catalog của commit nguồn, đã đồng bộ định nghĩa `seed_catalog`.
20 Feedback = 8 NEW + 12 RESOLVED, rating 1–5.
18 Survey = 3 DRAFT + 7 ACTIVE + 8 CLOSED; 144 Questions, 432 Options;
91 Recipients, 61 SUBMITTED Responses, 854 Answers.
Mỗi ACTIVE có 5 lời mời/3 hoàn thành; mỗi CLOSED có 7/5; DRAFT không có lời mời/trả lời.
Mọi survey có Single/Multi/Rating5/Rating10/Text/Matrix. Tất cả người nhận thuộc 15 Customer trên.
Customer là proxy trên Account theo schema hiện hành, không có bảng Customer riêng.

Chạy trong MySQL prompt của database demo:

```sql
SELECT role, status, COUNT(*) FROM accounts GROUP BY role, status;
SELECT status, COUNT(*) FROM feedbacks GROUP BY status;
SELECT status, COUNT(*) FROM surveys GROUP BY status;
SELECT s.title, s.status, COUNT(DISTINCT r.recipient_id) AS invited,
       COUNT(DISTINCT CASE WHEN p.status='SUBMITTED' THEN p.response_id END) AS submitted
FROM surveys s LEFT JOIN survey_recipients r ON r.survey_id=s.survey_id
LEFT JOIN survey_responses p ON p.recipient_id=r.recipient_id
GROUP BY s.survey_id, s.title, s.status;
```

Đăng nhập đúng từng portal, kiểm tra `/crm/reports/customers/`, Feedback và
`/surveys/manage/<survey_id>/stats/` cho từng Survey ACTIVE/CLOSED.

```powershell
python manage.py makemigrations --check --dry-run
python manage.py test --settings=config.test_settings
```

Tests phải dùng database test riêng và tài khoản có quyền tạo/xóa database test.
Không trỏ test runner vào database chứa dữ liệu cần giữ. Không commit/push tự động.

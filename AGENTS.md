# Project Overview

## CURRENT ACCOUNT INPUT CONTRACT — owner decision 2026-10-01

Account email is immutable after creation. Account role/status input is case-insensitive (`strip().upper()`), while stored values remain `ADMIN`/`CUSTOMER` and `ACTIVE`/`LOCKED`. Account generic PATCH and the HTML email-edit route are removed. Role change, lock/unlock, and password reset remain dedicated actions. This decision supersedes historical edit/PATCH proposals below; it requires no SQL or business migration.

## CURRENT DATABASE BUILD — owner decision 2026-10-01

`crm_db` is rebuilt from Django models and fresh project migrations. All 14 business primary keys and 17 business foreign keys are signed INT. Project migrations are new initial migrations for accounts, catalog, customers, feedback and surveys, plus `surveys/0002_schema_contract.py` for MySQL-specific constraints and types. `database/crm_db.sql` is a mysqldump of the migrated and seeded database; it no longer creates or drops the database. Do not use the superseded BIGINT migration strategy below.

## HISTORICAL ID TYPE DECISION — owner request 2026-09-30

The current target for all 14 business tables (including `suppliers`) is **signed INT** for every domain primary key and related foreign key. Django domain primary keys use `AutoField`; `DEFAULT_AUTO_FIELD` is `AutoField`. The 13-table/BIGINT inventory below records the earlier SQL baseline and is superseded for ID types and supplier scope by this decision. Preserve supplier FK/index and both survey UNIQUE constraints. `accounts/0001_initial.py` is an applied historical migration and remains BIGINT; `accounts/0002_int_identifiers.py` converts the physical Account ID, dependent business FKs and Django technical references without resetting data. Never run the SQL initialization file against an existing database because it contains `DROP DATABASE`.

## CURRENT ACTIVE ACCOUNT FOUNDATION — owner decision 2026-09-29

`TaiKhoan` / `tai_khoan` = **REMOVED LEGACY IMPLEMENTATION**. `Account` / `accounts` = **ONLY SUPPORTED ACCOUNT IMPLEMENTATION**. `AUTH_USER_MODEL='accounts.Account'`; Django's `password` and `last_login` fields map to `password_hash` and `last_login_at`. The current `accounts/0001_initial.py` creates `accounts` and its technical permission mappings from a clean database. Historical legacy inventory below is retained solely as audit evidence and does not authorize compatibility code or data migration from the removed model.

Đồ án: **Website bán đồ thể thao cầu lông tích hợp hệ thống quản lý quan hệ khách hàng (CRM)**. Backend Python/Django 5.2, MySQL 8.x; UI dự kiến Django Templates + Bootstrap 5. Windows là môi trường phát triển/demo chính. Mục tiêu là nghiệp vụ đúng, dữ liệu demo tái tạo được, phân quyền có kiểm thử và tài liệu đủ để bàn giao/báo cáo.

Hiện tại **backend-first**: requirements → database → backend/service → API → validation/permission → test/debug → frontend → integration → demo → báo cáo. Không triển khai UI trước khi backend liên quan ổn định. Không tự cài DRF hoặc refactor toàn repository.

## HISTORICAL STATE — REMOVED LEGACY IMPLEMENTATION, khảo sát 2026-09-28

- Entry point: `manage.py`; project config: `config/settings.py`, `config/urls.py`, `config/asgi.py`, `config/wsgi.py`.
- Apps đã khai báo: `apps.accounts`, `apps.shop`, `apps.catalog`, `apps.admin_portal`, `apps.customers`, `apps.feedback`, `apps.surveys`.
- `requirements.txt` pin Django **5.2.17**, mysqlclient **2.3.0**, python-dotenv **1.2.3**, cùng asgiref, pillow, sqlparse, tzdata. Không có DRF hay pytest trong dependencies.
- Model nghiệp vụ duy nhất hiện có là **LEGACY IMPLEMENTATION**: `apps/accounts/models.py::TaiKhoan(AbstractUser)`, bảng legacy `tai_khoan`; migration duy nhất của apps: `apps/accounts/migrations/0001_initial.py`. Những `models.py` còn lại là scaffold. Đây không phải target architecture.
- `views.py`, `admin.py`, `tests.py` của cả bảy apps là scaffold; chưa có test nghiệp vụ, service layer, API, app URLconf hoặc response convention để kế thừa. `config/urls.py` chỉ có `/admin/` của Django admin.
- Cấu hình auth legacy: `AUTH_USER_MODEL = 'accounts.TaiKhoan'`; `LOGIN_URL = 'accounts:login'` nhưng chưa có namespace/route tương ứng. Session, auth và CSRF middleware đã bật. `.env.example` ghi DB_NAME=crm_db theo quyết định hiện hành.
- Settings đọc `.env` qua python-dotenv; DB MySQL dùng charset `utf8mb4`, `STRICT_TRANS_TABLES`; `USE_TZ=True`, timezone `Asia/Ho_Chi_Minh`. `.env.example` có `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `MYSQL_BIN`. `MYSQL_BIN` chưa được settings/service sử dụng.
- Chưa có thư mục `scripts/`, `database/`, `templates/`, `static/` trong checkout; settings có tham chiếu hai thư mục cuối. `.gitignore` đã bỏ qua `.env`, `database/backups/`, `*.log`, virtualenv.
- README hiện chỉ có tên repository. Chưa có tài liệu API, seed command, backup/restore hoặc SQL export.
- Audit source không chứng minh trạng thái DB thật. Chưa kiểm tra migration đã apply, dữ liệu nhóm, MySQL server/version hoặc executable tại `MYSQL_BIN`. Shell audit dùng Python 3.12.7 từ MSYS2, thiếu pip/Django/MySQLdb/dotenv; `mysql`/`mysqldump` không có trên PATH. Đây là giới hạn của shell đang kiểm tra, không kết luận máy chưa cài các công cụ ở nơi khác.

Baseline là bằng chứng tại thời điểm khảo sát; luôn kiểm tra lại code khi bắt đầu task. Lần review naming phát hiện thêm file untracked `badminton_crm_db.db`; tên/đuôi file không chứng minh engine hay trạng thái MySQL. Không thay đổi file này hoặc coi nó là schema authority. Tiến độ và xung đột được theo dõi trong [plans.md](plans.md); prompt thực hành ở [prompts.md](prompts.md).

## CURRENT STATE — Official English Architecture

- Model `Account`, app label `accounts`, `AUTH_USER_MODEL = 'accounts.Account'`; không giữ model label legacy làm kiến trúc đích.
- Bảng `accounts`, đúng 8 cột English trong schema chính thức; toàn bộ 13 model/table dùng mapping bên dưới. Backend/API/test mới dùng English identifiers.
- Database `crm_db`, charset `utf8mb4`, collation `utf8mb4_unicode_ci`. Các bảng/model khác chưa implement không được coi là đã hoàn thành chỉ vì target đã được chốt.
- Naming target đã được chủ đồ án quyết định; chỉ migration strategy/data preservation còn cần khảo sát. Không dùng rủi ro migration làm lý do tiếp tục xây kiến trúc mới bằng tên legacy.

# Source of Truth

Khi dữ liệu/tài liệu mâu thuẫn, ưu tiên:

1. Official English database schema supplied by the project owner — danh mục 13 bảng trong **Database Rules** là bản ghi của schema này.
2. Explicit decisions made by the project owner after that schema.
3. AGENTS.md architecture rules.
4. plans.md approved decisions — không gồm đề xuất chưa duyệt.
5. Current repository implementation.
6. Old project documents / assignment documents.

Tên bảng/cột cũ không được tự động thay thế schema chính thức. Code và migrations cũ là **LEGACY IMPLEMENTATION**, bằng chứng hiện trạng, không có thẩm quyền định nghĩa lại target. Không tự thêm field từ tài liệu cũ. Nếu phát hiện conflict: ghi CURRENT STATE vs TARGET STATE, ưu tiên schema English, giải thích ảnh hưởng trước thay đổi lớn và cập nhật decision/blocker trong `plans.md`.

Schema dưới đây chốt tên cột, kiểu và một số enum; **chưa chốt đầy đủ** nullability, default, uniqueness, indexes, cardinality, FK/on_delete và các enum không liệt kê. Không suy diễn các phần thiếu thành requirement đã được duyệt. Ghi đề xuất và quyết định trước migration liên quan.

# English Naming Policy — Mandatory

**All domain, database, backend, API, and test identifiers must use English naming based on the official database schema.**

Áp dụng cho Django model classes/fields, database tables/columns, API routes/request/response fields, serializers/forms/schemas, services/repositories/helpers, constants/permissions, tests/fixtures/seed code, migration names khi khả thi, documentation examples và biến domain. Tiếng Việt chỉ dùng cho UI labels, user-facing messages, comments khi hữu ích và nội dung báo cáo/giải thích; không dùng cho technical domain identifiers.

## Official Model Naming

| Official table | Required Django model |
| --- | --- |
| accounts | Account |
| customers | Customer |
| products | Product |
| categories | Category |
| brands | Brand |
| customer_preferences | CustomerPreference |
| feedbacks | Feedback |
| surveys | Survey |
| survey_questions | SurveyQuestion |
| survey_options | SurveyOption |
| survey_recipients | SurveyRecipient |
| survey_responses | SurveyResponse |
| survey_answers | SurveyAnswer |

Khai báo `Meta.db_table` đúng bảng English, không để tên bảng mặc định có app prefix làm lệch schema. Ví dụ target `Account.Meta.db_table = "accounts"`. PK dùng tên chuẩn `account_id`, `customer_id`, v.v.; không để Django tự tạo cột `id` thay cho PK chính thức. Không trộn English model với field legacy. Thuật ngữ trong thảo luận kỹ thuật: Account management, Account lock/unlock, Password reset, Account permissions, Customer account, Feedback handler, Survey creator.

## Legacy Naming Ban

Những tên dưới đây **không được xuất hiện trong NEW implementation** như model/table/field/route/service/test/fixture/domain identifiers:

```text
TaiKhoan tai_khoan
KhachHang khach_hang
SanPham san_pham
DanhMuc danh_muc
ThuongHieu thuong_hieu
PhanHoi phan_hoi
KhaoSat khao_sat
CauHoi cau_hoi
LuaChon lua_chon
TraLoi tra_loi
PhieuKhaoSat phieu_khao_sat
vai_tro trang_thai
```

Danh sách không giới hạn ở các ví dụ trên: `ho_ten`, `so_dien_thoai`, `ngay_sinh`, `gioi_tinh`, `dia_chi`, `trinh_do`, `tai_khoan_id` cũng là tên legacy, không dùng làm target fields. **Exception:** các tên này chỉ được xuất hiện trong ghi chú lịch sử hoặc khi xác minh code cũ; không tạo compatibility code, query hoặc data migration cho model đã loại bỏ.

## Foreign Key and API Identifier Rules

- Python relationship có thể dùng `customer.account`, `product.category`, `product.brand`; tên object property vẫn English. Cột MySQL phải đúng `account_id`, `category_id`, `brand_id`, v.v.; dùng `db_column` khi cần.
- `Feedback.handled_by` và `Survey.created_by` nếu là ForeignKey phải map cột vật lý `handled_by` / `created_by` bằng `db_column`; không để tự sinh `handled_by_id` / `created_by_id`. Không gọi field FK `account_id` rồi vô tình tạo cột `account_id_id`.
- JSON domain IDs dùng nhất quán `account_id`, `customer_id`, `product_id`, `category_id`, `brand_id`, `preference_id`, `feedback_id`, `survey_id`, `question_id`, `option_id`, `recipient_id`, `response_id`, `answer_id`. Với quan hệ có tên nghiệp vụ, giữ `handled_by` / `created_by` chứa Account ID; ghi rõ trong contract, không đổi cột. IDs của Django Group/Permission dùng tên English theo contract riêng, không đổi PK domain thành `id`.
- Không expose field tiếng Việt; serializer/form/schema/fixture/tests mới phải dùng tên English tương ứng. Cardinality OneToOne/ForeignKey vẫn cần xác nhận; quy tắc naming không tự chốt cardinality.

# My Responsibility

Phạm vi chủ quản: accounts; authentication liên quan; account administration; permissions; backup/restore; `seed_data`; SQL export.

Phải phối hợp với `customers` (`account_id`), `feedbacks` (`handled_by`), `surveys` (`created_by`). Trong repo, app là `apps.feedback` số ít nhưng bảng chuẩn là `feedbacks`. Dự kiến catalog quản lý categories/brands/products; cần thống nhất với thành viên phụ trách trước sửa.

Không xóa hoặc sửa code thành viên khác nếu không cần thiết. Khi cần thay đổi cross-module, ghi contract/FK bị ảnh hưởng, phạm vi và regression tests; chỉ sửa phần cần cho task đã giao. Không tự tạo model của cả hệ thống chỉ để seed chạy.

# Repository First Rule

Trước khi code:

1. Đọc `AGENTS.md`, `plans.md`, kiểm tra `git status` và nhánh hiện tại; giữ nguyên thay đổi chưa commit của người khác.
2. Khảo sát cấu trúc thực tế bằng `rg --files`; đọc settings, models, URLs, migrations, `requirements.txt`, `.env.example`, tests liên quan.
3. Xác định auth model/backend, permission hiện có, API/response conventions, service layer và test runner. Không đoán FBV/CBV, DRF hoặc custom user từ tên thư mục.
4. Kiểm tra trạng thái DB/migration trên môi trường được chỉ định nếu task cần; không đọc/in secret từ `.env` vào báo cáo.
5. Nêu file ảnh hưởng, DB/API/security impact, test plan; ghi blockers thật sự. Chỉ hỏi khi thiếu quyết định làm thay đổi dữ liệu/nghiệp vụ/contract.

Hướng lệnh sau khi chọn đúng virtualenv, dependencies và DB phát triển/test (không tự chạy migrate/restore):

```powershell
python manage.py check
python manage.py showmigrations
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py test apps.accounts
python manage.py test
```

`showmigrations`/`migrate --plan` cần cấu hình DB phù hợp. Review migration và SQL (`sqlmigrate <app> <number>`) trước khi áp dụng. Không báo test pass nếu thiếu runtime hoặc chưa chạy.

# Database Rules

## Official Database Name

Database đích bắt buộc: `crm_db` theo quyết định mới nhất của chủ đồ án ngày 2026-09-29. Ví dụ cấu hình:

```dotenv
DB_NAME=crm_db
```

```sql
CREATE DATABASE crm_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE crm_db;
```

Đây là ví dụ setup, không phải lệnh được chạy trong task kiểm tra. `.env.example` và tên file `database/crm_db.sql` đã thống nhất với database `crm_db`. File SQL hiện có chứa lệnh `DROP DATABASE IF EXISTS crm_db`; không chạy lại trên DB đã có dữ liệu. Test/restore dùng DB riêng như `test_crm_db` hoặc `crm_db_import_test`, không trỏ nhầm DB dùng chung. Khi tạo dump portable sau này, xác định rõ phạm vi CREATE DATABASE/USE và smoke-test trên DB disposable do test chỉ định.

## Django technical tables — ACCEPTED

13 bảng chính thức là **business/domain schema**, không phải giới hạn tổng số bảng vật lý. Django được phép tạo bảng kỹ thuật cần cho migrations, sessions, content types, permissions, groups, many-to-many permission mappings và framework internals khác. Ví dụ: `django_migrations`, `django_session`, `django_content_type`, `auth_permission`, `auth_group` và các bảng M2M cần thiết. Những bảng này không vi phạm schema 13 bảng; không hỏi lại việc cho phép chúng.

Không tạo thêm BUSINESS/domain table khi chưa được chủ đồ án phê duyệt; không tạo bảng domain trùng chức năng để né schema chính thức. Quyền dùng bảng kỹ thuật không cho phép thêm cột nghiệp vụ hoặc cột Auth thừa vào `accounts`. Vẫn inventory bảng thực tế, thiết kế Groups/Permissions và xác định phạm vi SQL export phù hợp.

## Schema chính thức — 13 bảng

Các khối dưới đây là **danh mục schema**, không phải DDL thực thi; không ngầm định NULL, PK/FK, UNIQUE hay CASCADE ngoài các quyết định sẽ được ghi nhận. ID chính và các quan hệ phải được cụ thể hóa trong thiết kế migration được review.

```text
accounts
  account_id BIGINT
  email VARCHAR(255)
  password_hash VARCHAR(255)
  role VARCHAR(20)                 values: ADMIN, CUSTOMER
  status VARCHAR(20)               values: ACTIVE, LOCKED
  last_login_at DATETIME
  created_at DATETIME
  updated_at DATETIME

customers
  customer_id BIGINT
  account_id BIGINT
  full_name VARCHAR(150)
  phone VARCHAR(20)
  date_of_birth DATE
  gender VARCHAR(20)
  address VARCHAR(255)
  playing_level VARCHAR(30)
  status VARCHAR(20)               values: ACTIVE, DELETED
  created_at DATETIME
  updated_at DATETIME
  deleted_at DATETIME

products
  product_id BIGINT
  category_id BIGINT
  brand_id BIGINT
  product_name VARCHAR(200)
  description TEXT
  price DECIMAL(12,2)
  status VARCHAR(20)               values: ACTIVE, INACTIVE
  created_at DATETIME
  updated_at DATETIME

categories
  category_id BIGINT
  category_name VARCHAR(100)
  description VARCHAR(255)
  status VARCHAR(20)
  created_at DATETIME
  updated_at DATETIME

brands
  brand_id BIGINT
  brand_name VARCHAR(100)
  description VARCHAR(255)
  status VARCHAR(20)
  created_at DATETIME
  updated_at DATETIME

customer_preferences
  preference_id BIGINT
  customer_id BIGINT
  preference_type VARCHAR(50)
  preference_value VARCHAR(150)
  created_at DATETIME

feedbacks
  feedback_id BIGINT
  customer_id BIGINT
  product_id BIGINT
  rating TINYINT
  content TEXT
  status VARCHAR(20)
  manager_note TEXT
  handled_by BIGINT
  created_at DATETIME
  resolved_at DATETIME

surveys
  survey_id BIGINT
  title VARCHAR(200)
  description TEXT
  start_at DATETIME
  end_at DATETIME
  status VARCHAR(20)
  created_by BIGINT
  created_at DATETIME
  updated_at DATETIME

survey_questions
  question_id BIGINT
  survey_id BIGINT
  question_text TEXT
  question_type VARCHAR(30)
  is_required BOOLEAN
  sort_order INT

survey_options
  option_id BIGINT
  question_id BIGINT
  option_text VARCHAR(255)
  sort_order INT

survey_recipients
  recipient_id BIGINT
  survey_id BIGINT
  customer_id BIGINT
  status VARCHAR(20)
  sent_at DATETIME
  opened_at DATETIME
  completed_at DATETIME

survey_responses
  response_id BIGINT
  recipient_id BIGINT
  status VARCHAR(20)
  started_at DATETIME
  submitted_at DATETIME

survey_answers
  answer_id BIGINT
  response_id BIGINT
  question_id BIGINT
  option_id BIGINT
  answer_text TEXT
  rating_value TINYINT
  created_at DATETIME
```

## Quan hệ cần bảo toàn và xác nhận ràng buộc

- `customers.account_id → accounts.account_id`.
- `products.category_id → categories.category_id`; `products.brand_id → brands.brand_id`.
- `customer_preferences.customer_id → customers.customer_id`.
- `feedbacks.customer_id → customers.customer_id`; `product_id → products.product_id`; `handled_by → accounts.account_id`.
- `surveys.created_by → accounts.account_id`.
- `survey_questions.survey_id → surveys.survey_id`; `survey_options.question_id → survey_questions.question_id`.
- `survey_recipients.survey_id → surveys.survey_id`; `customer_id → customers.customer_id`.
- `survey_responses.recipient_id → survey_recipients.recipient_id`.
- `survey_answers.response_id → survey_responses.response_id`; `question_id → survey_questions.question_id`; `option_id → survey_options.option_id`.

FK không đủ bảo đảm logic survey: option phải thuộc question; question phải thuộc survey của recipient/response. Acceptance/test phải kiểm tra các quan hệ chéo này. Rating range và question types cần thống nhất, không tự lấy từ tài liệu cũ.

## Migration safety gates — bắt buộc trước thay đổi dữ liệu

Không có phê duyệt rõ ràng thì **không được** DROP database, DROP business table, xóa migration history, xóa migrations đã hoặc có thể đã chia sẻ, reset DB chung, rename bảng có dữ liệu theo cách phá hủy, truncate dữ liệu chung, hoặc recreate DB chỉ để migrations chạy qua. Việc xác định DB có thể reset an toàn không phải là quyền reset.

Trước phê duyệt có thể inspect, analyze, lập migration plan, tạo backup, tạo tests và đề xuất các bước SQL/Django migration trong phạm vi task; không tự áp dụng bước phá hủy. Task chỉ tài liệu vẫn chỉ sửa tài liệu.

Trước **mọi migration có thể rename, transform hoặc remove dữ liệu hiện có**, phải tạo **và xác minh** backup trước. Ghi DB nguồn, thời điểm/revision, phạm vi schema/data/technical tables, kết quả dump, integrity và bằng chứng khôi phục trên DB disposable được chỉ định theo Restore Rules. Backup thất bại hoặc chưa xác minh nghĩa là **không được tiếp tục migration**; ghi `[!] BLOCKED` và recovery plan. Không đợi service backup Phase 4 hoàn tất: có thể dùng quy trình backup vận hành được review với cùng guard credentials/DB đích.

Trước migration hoặc hard-delete account, inspect **tất cả FK thực tế** liên quan, kể cả bảng kỹ thuật; đối chiếu các quan hệ dự kiến trong schema. Mỗi quan hệ quan trọng phải có: FK source, FK target, nullable/required, expected ON DELETE và hậu quả nghiệp vụ. Ghi riêng hành vi DB hiện tại với Django `on_delete` dự kiến; chưa biết thì ghi UNKNOWN/BLOCKED, không tự điền CASCADE. Các quan hệ chưa implement cần contract được chủ module xác nhận.

## Migration và truy cập dữ liệu

- Không tự ý rename/drop bảng/cột; thay đổi để khớp schema phải có mapping, tác động dữ liệu và migration được review.
- Không sửa migration đã merge nếu có thể tạo migration mới. **Ngoại lệ đã được chủ đồ án quyết định ngày 2026-09-29:** thay thế `accounts/0001_initial.py` legacy khi read-only inspection xác nhận nó chưa apply và `crm_db` chỉ có schema SQL chính thức, không có business rows. Không dùng `--fake`, reset DB hoặc DROP làm cách sửa lỗi mặc định.
- Bảo toàn PK/FK và dữ liệu; xác định `on_delete`, NULL/default/index/unique theo requirement đã xác nhận. Không tự thêm bảng audit nghiệp vụ vào 13 bảng; logging file là lựa chọn ban đầu. Bảng kỹ thuật Django đã được cho phép, không cần duyệt lại quyền tồn tại.
- Dùng ORM khi phù hợp; raw SQL phải parameterized (identifier chọn từ allowlist). Dùng `transaction.atomic()` cho thay đổi nhiều bước cần tính nhất quán. Không hứa rollback toàn bộ một MySQL restore/DDL bằng Django transaction.
- Giữ Decimal cho giá; xử lý DATETIME nhất quán với `USE_TZ=True`; kiểm tra tiếng Việt/utf8mb4 sau import/export.

# Account Rules

## Historical legacy inventory — superseded by the owner decision

Mục này ghi lại khảo sát trước khi chủ đồ án loại bỏ hoàn toàn model cũ. Không thực hiện conversion hay giữ compatibility từ bảng/model legacy; foundation hiện tại dùng trực tiếp `crm_db.accounts`.

Trước quyết định cuối cùng, source từng có `TaiKhoan(AbstractUser)` dùng bảng `tai_khoan`, PK `id`, password `password(128)`, `last_login`, email 254 ký tự, `username`, `is_active`, `is_staff`, `is_superuser`, `date_joined`, cùng field legacy `ho_ten`, `so_dien_thoai`, `vai_tro`, `ly_do_khoa`, `ngay_khoa`. Role cũ gồm ADMIN/QUAN_LY/NV_CSKH/KHACH_HANG. Mục này chỉ là lịch sử; không có bảng legacy trong live `crm_db` và không có dữ liệu cần chuyển.

| CURRENT STATE — legacy source | TARGET STATE — official English naming / disposition |
| --- | --- |
| TaiKhoan / tai_khoan | Account / accounts |
| id | account_id; bảo toàn giá trị PK và FK |
| password / last_login | password_hash / last_login_at; thiết kế Auth adapter English, giữ hash hợp lệ |
| VaiTro / vai_tro | English role constants / role; chỉ ADMIN, CUSTOMER; chuyển enum theo policy được duyệt |
| is_active | status ACTIVE/LOCKED là nguồn nghiệp vụ; interface Auth nếu cần không tạo thêm cột |
| ho_ten / so_dien_thoai | Chỉ cân nhắc Customer.full_name / Customer.phone sau xác nhận profile mapping; không thêm vào Account |
| ly_do_khoa / ngay_khoa | Không có field target; bảo toàn/archive hoặc loại bỏ theo quyết định, không tự thêm cột |
| username / first_name / last_name / date_joined / is_staff / is_superuser | Không sao chép nguyên schema kế thừa; thiết kế mapping/interface và xử lý dữ liệu rõ trước migration |

Đây là **HISTORICAL LEGACY INVENTORY**, không phải hướng dẫn chuyển dữ liệu. **CURRENT:** `Account`, `accounts`, official English fields, `AUTH_USER_MODEL='accounts.Account'`. Tên thuộc tính framework `password`/`last_login` dùng Django `db_column` để map trực tiếp tới `password_hash`/`last_login_at`; không có cột thừa.

Chuyển `AUTH_USER_MODEL` đã hoàn thành sau khi live inspection xác nhận migration legacy chưa apply, bảng SQL `accounts` đã tồn tại, 13 bảng nghiệp vụ đều có 0 rows và không có bảng legacy. Không xây conversion hoặc compatibility cho model cũ. Các thay đổi Auth sau này vẫn cần kiểm tra migration/data state trước khi áp dụng.

`AbstractBaseUser`/`PermissionsMixin` cung cấp Django Auth; `is_active`, `is_staff`, `is_superuser` là properties, không tạo cột trong `accounts`. ACTIVE ADMIN có quyền framework-level superuser; LOCKED bị từ chối xác thực. Django Groups/Permissions dùng bảng kỹ thuật riêng. `Account.role` chỉ ADMIN/CUSTOMER; profile thuộc Customer, không thêm vào Account.

## AUTH_USER_MODEL inspection gate

**Never change AUTH_USER_MODEL blindly.** Trước sửa Account/Auth model, bắt buộc:

1. Inspect `config/settings.py`, xác minh `AUTH_USER_MODEL` và auth backend/config thực tế.
2. Inspect model auth hiện tại (model legacy được mô tả trong mục Conflict ở trên) và mapping tới Account.
3. Inspect migration files, graph/dependencies và lịch sử Git/chia sẻ.
4. Dùng `showmigrations`, `migrate --plan` và inspect DB tables khi có quyền truy cập để xác định migrations đã apply, đặc biệt `accounts/0001_initial.py`.
5. Xác định dữ liệu cần giữ, PK/FK/hash/profile/permission/session và yêu cầu backup/recovery.
6. Xác định DB có shared với đồng đội không, ai sở hữu và có thể reset an toàn hay không; không coi kết luận này là approval reset.

Nếu migration state chưa rõ ở các thay đổi sau: **STOP destructive migration**, ghi task và các task phụ thuộc là `[!] BLOCKED` trong `plans.md`. Với foundation hiện tại, fresh test DB và live SQL-owned `accounts` đều đã được kiểm tra; không có legacy data upgrade theo quyết định cuối cùng của chủ đồ án.

## Password mapping — accounts.password_hash

Cột vật lý chính thức luôn là `accounts.password_hash`; không đổi thành `password` chỉ vì mặc định framework. Trước implementation/migration, inspect kiến trúc Auth hiện tại và ghi thiết kế mapping từ Django password handling tới cột này trong `plans.md` (GATE-C).

Dùng Django-supported `set_password()` và `check_password()`; **không tự viết thuật toán hash**, không lưu plaintext, không gán raw password vào `password_hash`, không expose hash qua API, không log password/hash. Model save từ chối raw password trực tiếp; manager dùng password validators và Django hashing. Foundation đã kiểm thử create/login/check_password, last_login, LOCKED session và direct raw-password rejection. Reset flow/API là task sau GATE-J; không có legacy hash migration vì không có legacy table/data.

## Nghiệp vụ

- Normalize email qua một policy thống nhất cho create/login/seed; email không được thay đổi sau khi tạo Account. Django email normalization không thay thế quyết định uniqueness. Enforce cả validation và DB, xử lý race duplicate rõ ràng.
- Normalize input Account role/status bằng `strip().upper()` trước validation; chỉ lưu ADMIN/CUSTOMER và ACTIVE/LOCKED. Áp dụng cho create, role action, list filters, HTML forms, API và service/manager/model entry points. Không đổi SQL CHECK constraints.
- Password luôn hash bằng cơ chế Django tương thích (`set_password`/API tương đương), chạy password validators trong service reset/create; không gán plaintext vào `password_hash`, không log/trả hash hoặc password trong API, không hard-code password sản xuất.
- Reset qua API/service phải xác minh ADMIN và permission phù hợp ở backend, dùng Django hashing/validation, chỉ log actor/target/action, không lưu plaintext hoặc trả password_hash. Chốt rõ một trong ba flow: (a) admin cung cấp mật khẩu tạm, (b) hệ thống sinh mật khẩu tạm, (c) reset link/token; không âm thầm chọn UX. Ghi quyết định GATE-J/ADR-005 trong plans.md trước triển khai. Không gửi mật khẩu qua URL. Nếu flow cho phép, test mật khẩu cũ không đăng nhập được và mật khẩu mới đăng nhập được; chốt ảnh hưởng session hiện có.
- Khóa dùng `status=LOCKED`, mở khóa `status=ACTIVE`. Backend phải từ chối login và request được bảo vệ của account đã khóa, kể cả session cũ. Không chỉ đổi UI hoặc `is_active` legacy mà quên trạng thái chuẩn.
- `last_login_at` cập nhật khi login thành công; không cập nhật khi sai password, bị khóa hoặc chỉ xem detail.
- Whitelist field được phép nhận/trả; không mass assign role/quyền từ payload người dùng thường. Các field audit/ID do backend quản lý.
- Chốt quy tắc tự khóa/tự xóa và ADMIN cuối cùng trước code; không âm thầm đổi nghiệp vụ.

# Authorization Rules

Authentication = người dùng là ai. Authorization = người dùng được làm gì.

- Mỗi API quản trị kiểm tra quyền ở backend; ẩn button không phải permission. Account chưa đăng nhập/bị khóa không được thao tác. Bắt buộc ADMIN-only cho GET accounts, GET account detail, POST account, DELETE account, POST role, POST lock, POST unlock, POST reset-password và toàn bộ group/permission administration; kiểm tra trên từng method/action, kể cả API chưa có UI. Account PATCH không tồn tại.
- Quy tắc bắt buộc: trạng thái ACTIVE + `role=ADMIN` là cổng vào API quản trị; nếu dùng quyền chi tiết, phải có thêm permission thích hợp. CUSTOMER không được vào dù vô tình có group/permission. Không cho cờ legacy `is_staff`/`is_superuser` bỏ qua policy một cách ngầm định.
- Nguồn quyền: role là phân loại ADMIN/CUSTOMER; Groups gom permission; permissions là quyền thao tác chi tiết theo action; backend/check tập trung kết hợp chúng. Chốt ADMIN có toàn quyền hay cần permission chi tiết, đặc biệt với gán quyền/reset/restore. Không tạo role DB mới cho quản lý/CSKH; ưu tiên Groups nếu kiến trúc cho phép.
- Django contrib auth/contenttypes đã được cài và model hiện có Groups/Permissions, nhưng **chưa có permission guard nghiệp vụ**. Các bảng kỹ thuật Django/M2M nằm ngoài 13 bảng nghiệp vụ và đã được cho phép. Chỉ chiến lược quyền chi tiết/mapping và phạm vi dữ liệu SQL export còn cần thiết kế.
- Test mọi HTTP method/action, không chỉ list; kiểm tra quyền lại ngay trước thao tác nhạy cảm. Log thay đổi role/group/permission; kiểm soát gán quyền cao hơn phạm vi được phép.

# API Conventions

Account API hiện dùng Django Ninja dưới `/api/accounts/`, session authentication và CSRF; auth API dùng `/api/auth/`. Các đề xuất API cũ trong mục này chỉ là lịch sử cho module chưa triển khai. Không thêm DRF nếu không có quyết định mới.

- Account API hiện dùng GET đọc, POST tạo/action và DELETE xóa theo policy; không có generic Account PATCH. GET không làm thay đổi trạng thái.
- Nếu đã xuất hiện convention được nhóm duyệt, giữ convention đó; không đổi contract trong task UI/bugfix mà không báo.
- Response đề xuất (không phải API đã tồn tại):

```json
{"success": true, "data": {}}
```

```json
{"success": false, "error": {"code": "VALIDATION_ERROR", "message": "Dữ liệu không hợp lệ", "fields": {"email": ["Email không hợp lệ"]}}}
```

- List đề xuất: `data={"items": [...], "pagination": {"page": 1, "page_size": 20, "total": 0}}`; giới hạn page_size (đề xuất tối đa 100), sort ổn định có khóa phụ `account_id`. Chốt search `q` theo email; tên nằm ở customers nên chỉ join/search khi có requirement. Filter `role`, `status` theo enum; invalid query trả lỗi rõ, không silent fallback. Chốt fields/sort cho phép.
- Status: 200 đọc/cập nhật/action; 201 tạo; 204 xóa không có body hoặc 200 envelope theo contract đã chốt; 400 malformed/validation; 401 chưa xác thực; 403 thiếu quyền/CSRF; 404 không tồn tại; 405 sai method; 409 conflict đã định nghĩa như duplicate/protected delete; 500 lỗi nội bộ đã sanitize. Không trả HTML login redirect cho JSON API nếu contract yêu cầu 401.
- Lỗi từng field rõ ràng; không leak stack trace, SQL, đường dẫn máy hay secret. Django session + CSRF cần test cả client gửi và thiếu CSRF token.

# Candidate Account APIs

Đây là **đề xuất lịch sử** dưới `/api/admin/` cho các module chưa triển khai. Account API thực tế nằm dưới `/api/accounts/` với GET/POST list, GET/DELETE detail, và POST role/lock/unlock/reset-password; không có Account PATCH.

```text
GET    /api/admin/accounts/
GET    /api/admin/accounts/{account_id}/
POST   /api/admin/accounts/
DELETE /api/admin/accounts/{account_id}/
POST   /api/admin/accounts/{account_id}/role/
POST   /api/admin/accounts/{account_id}/lock/
POST   /api/admin/accounts/{account_id}/unlock/
POST   /api/admin/accounts/{account_id}/reset-password/

GET    /api/admin/groups/
POST   /api/admin/groups/
PATCH  /api/admin/groups/{id}/
DELETE /api/admin/groups/{id}/
POST   /api/admin/groups/{id}/permissions/
```

Gán account vào group cần contract riêng; không có generic Account PATCH. Backup/restore API dự kiến POST `/api/admin/backups/`, POST `/api/admin/restores/`; service và permission được kiểm thử trước UI.

# Delete Strategy

- Accounts có status ACTIVE/LOCKED, **không có DELETED/deleted_at**. Customers có ACTIVE/DELETED và deleted_at; hai nghiệp vụ khác nhau.
- Trước DELETE, kiểm tra FK thực và `customers.account_id`, `feedbacks.handled_by`, `surveys.created_by`, cả M2M/auth/admin log liên quan. Không mặc định cascade.
- Normal account deactivation dùng `status=LOCKED` cho tới khi hard-delete behavior được xác nhận rõ. LOCKED khác deleted; không âm thầm biến DELETE thành lock. DELETE bị BLOCKED nếu chưa chốt policy (GATE-H/ADR-005); contract và tests phải bảo vệ lịch sử theo FK inventory.
- Nếu physical delete được cho phép, xác định account nào đủ điều kiện, rollback khi FK bảo vệ, response conflict và ảnh hưởng customer/profile. Chưa chốt policy thì task DELETE BLOCKED, các task độc lập vẫn tiếp tục.

# Backup Rules

- Service dùng `mysqldump`, lấy DB config từ settings/.env; resolve executable từ `MYSQL_BIN` hoặc PATH theo cấu hình đã validate. Không hard-code credentials hoặc giả định MySQL đã có PATH.
- Đề xuất `--single-transaction --no-tablespaces --default-character-set=utf8mb4`; xác minh engine InnoDB/phạm vi tính nhất quán, tránh DDL đồng thời khi dump. Đầu ra chứa structure + data theo mục đích backup.
- Thư mục mặc định đề xuất `database/backups/` (đã gitignore); tên `crm_db_YYYYMMDD_HHMMSS_<unique>.sql` tránh ghi đè. Dùng file tạm rồi publish khi exit code thành công và output hợp lệ; không để file lỗi được liệt kê như backup tốt.
- Ưu tiên option file MySQL tạm với quyền đọc hạn chế hoặc login-path; không đặt password trực tiếp trong command line/log. Dọn file credential kể cả thất bại. Không tự tạo cơ chế parse `.env` bằng thực thi shell.
- `subprocess` dùng argv, `shell=False`, timeout hợp lý, binary I/O giữ nguyên SQL; kiểm tra returncode, executable thiếu, config thiếu, output/permission/disk errors. Không báo thành công nếu command fail.
- Log actor, thời điểm, backup ID/tên an toàn, kết quả, duration và lỗi đã che secret; API ADMIN. Chưa có thiết kế bảng history nên dùng logging/file được cấu hình, không tự thêm bảng DB.

# Restore Rules

Restore là thao tác phá hủy dữ liệu. Phải kiểm tra ADMIN ở backend, xác nhận rõ backup và DB đích ngay trước khi chạy; câu đồng ý chung trước đó không thay cho xác nhận đúng DB/file của lần restore cụ thể.

- Validate file tồn tại, regular file, kích thước, đuôi/định dạng; `.sql` không chứng minh dump an toàn. Ưu tiên chỉ nhận backup do hệ thống tạo/dump demo tin cậy; nếu cho upload SQL bất kỳ phải chốt mô hình tin cậy và giới hạn. Không hứa một regex có thể làm SQL tùy ý an toàn.
- Resolve/canonicalize path rồi xác minh nằm trong backup root; chặn `..`, absolute path ngoài root, symlink/junction vượt root. Tốt nhất API nhận backup ID do server ánh xạ; không nhận executable/DB host/command tùy ý từ user.
- Dùng `mysql`, config như backup, argv không shell, SQL qua stdin file; kiểm tra exit code/timeout, log start/success/failure. Không expose DB password, raw stderr nhạy cảm hoặc trả success trước command kết thúc.
- Có pre-restore backup và kế hoạch recovery phù hợp; MySQL restore có thể áp dụng một phần khi lỗi, không giả định atomic. Xác định maintenance window/ngăn ghi đồng thời; log restore không chỉ lưu trong DB đang bị thay thế.
- Test subprocess bằng mock; integration restore chỉ trên database test/disposable với guard từ chối DB dev chung/production. Kiểm tra dump không có `USE`/`CREATE DATABASE` trỏ về DB thật và các tham chiếu ngoài DB đích. Không tự restore production khi test.

# Batch Script Rules

`scripts/backup.bat`, `scripts/restore.bat` là wrapper mỏng cho cùng backend/management command sẽ được thiết kế; không nhân đôi logic credentials/validation. Hiện hai file chưa tồn tại.

- Resolve project root theo `%~dp0`, dùng `setlocal`, `set "NAME=value"`, quote đường dẫn và biến; hỗ trợ cwd khác và `C:\Program Files\...`.
- Chọn Python/virtualenv rõ ràng; load cấu hình qua Python/settings, không `call` từng dòng `.env` như lệnh shell. Không nhúng password plaintext vào batch, echo hoặc argv.
- Kiểm tra `ERRORLEVEL` ngay sau command; giữ exit code lỗi qua `endlocal`, thông báo thành công/thất bại rõ và `exit /b` đúng. Không luôn trả 0 hoặc pause làm automation treo.
- Restore phải nêu file + DB đích và yêu cầu xác nhận; wrapper không bỏ qua guard của service. Test Windows với path có khoảng trắng, file thiếu, executable thiếu, config sai và subprocess fail.

# Seed Data Rules

- Entry point: `python manage.py seed_data`, management command đặt trong app được thống nhất (đề xuất `apps.admin_portal/management/commands/seed_data.py`). Đây là đường dẫn dự kiến.
- Deterministic hợp lý: fixed random seed/natural keys demo, thứ tự ổn định; `get_or_create`/`update_or_create` với unique policy đã chốt. Không sinh duplicate vô hạn và không ghi đè người dùng thật trùng email âm thầm.
- Bao phủ đủ 13 bảng, tạo theo FK: categories/brands và accounts → customers/products → customer_preferences/feedbacks/surveys → survey_questions → survey_options → survey_recipients → survey_responses → survey_answers. Surveys cần creator, feedback đã xử lý cần handler hợp lệ.
- Có ADMIN ACTIVE, CUSTOMER ACTIVE và LOCKED; nhiều khách hàng, sản phẩm cầu lông, feedback, survey ở các trạng thái đã duyệt, câu trả lời text/option/rating theo question types đã chốt. Không tự mở rộng enums để demo.
- Mật khẩu demo rõ nhãn và tách khỏi production; dùng `set_password`/API tương đương, không gán trực tiếp password_hash. Chạy lại không tự đổi password account thật hoặc reset quyền ngoài bộ demo.
- `--reset` nếu cần: cảnh báo phạm vi, xác nhận rõ (cờ xác nhận cho automation test), chỉ xóa bộ demo theo thứ tự FK đảo; guard môi trường. Không `flush` toàn DB nhóm. Dùng transaction cho seed/reset nhất quán khi phù hợp.
- Chưa có model ở apps khác: ghi dependency BLOCKED; không seed bằng raw SQL bỏ qua model hoặc tự sửa schema của thành viên khác. Tổng kết created/updated/skipped, count theo bảng, không log credentials; test chạy hai lần, rollback khi lỗi, reset có kiểm soát và quan hệ survey.

# SQL Export Rules

- Deliverable được version-control: `database/crm_db.sql`, chỉ structure + **demo data**; khác backup vận hành trong `database/backups/` không commit.
- Export từ DB demo sạch đã migrate/seed đúng revision; không dump DB cá nhân/production. Charset utf8mb4, kiểm tra dữ liệu tiếng Việt, hash password demo, không có credentials thật, secret/token/session thật.
- Chốt phạm vi bảng kỹ thuật Django (auth/contenttypes/M2M/migrations/session/admin log) và thứ tự import; script phải đủ để ứng dụng hoạt động theo phạm vi được duyệt. Không đưa `CREATE USER`, `GRANT`, database password hoặc definer đặc thù máy vào dump.
- Ưu tiên dump không gắn tên database cố định để có thể import vào DB rỗng khác tên. Smoke-test bắt buộc trên DB dùng một lần: import → kiểm tra structure/FK/count → đăng nhập demo → API đại diện → kiểm tra migration state. Không import và migrate trùng schema mù quáng; tài liệu phân biệt luồng migrate+seed và luồng import dump.
- Ghi command/revision và kết quả validation; chưa import kiểm chứng thì chưa DONE, không viết tay SQL giả để đánh dấu đủ deliverable.

# Security Rules

- Hash/validate password; auth và quyền ở backend; kiểm tra trạng thái LOCKED trong login và request.
- Session mutations cần CSRF; không dùng `csrf_exempt` để chữa lỗi integration. Validate input/query/upload, whitelist writable fields, giới hạn kích thước/page_size.
- ORM/parameterized SQL; không log credentials/password/hash; không expose hash trong JSON kể cả lỗi, export API, nested customer hay log debug.
- Không commit `.env`, file credentials, dữ liệu thật hay backup; `.env.example` hiện có giá trị password mẫu nên phải làm rõ/chuyển placeholder trong task sau, không coi là secret sản xuất dùng được.
- Chặn path traversal, command injection; dùng argv và `shell=False`, executable tin cậy, timeout/exitcode. Không ghép shell string từ input.
- Lỗi API không leak traceback; cấu hình demo chia sẻ không bật DEBUG bừa bãi. Không thêm quy trình hoặc package bảo mật quá mức nhu cầu; xử lý rủi ro thực tế của chức năng.

# Testing Rules

Repo hiện có `django.test.TestCase` scaffold, chưa có test cases. Dùng Django test runner trước; không mặc định pytest/DRF. Test data riêng, không chạy trên DB nhóm. Test liên quan MySQL/constraints trên MySQL, mock subprocess không thay thế import smoke-test thật.

Mỗi backend feature cân nhắc unit/service, permission, validation, success/failure, unauthorized (401), forbidden (403), not found (404), duplicate/conflict, LOCKED, CSRF/session và rollback nhiều bước. Chỉ thêm test có giá trị, không viết test sao chép implementation.

| Phạm vi | Kiểm thử tối thiểu |
| --- | --- |
| Accounts | Create/list/detail/update; search/filter/pagination; duplicate/invalid email/role/status; không mass assign; lock/unlock; old/new password sau reset; delete policy và FK/history |
| Auth/permission | Anonymous/CUSTOMER/LOCKED không quản trị; ADMIN theo policy; session cũ sau lock/reset; không tự nâng quyền; group assignment và revoke; hash không lộ trên mọi response |
| Backup | Command success/failure; thiếu mysqldump; invalid config; timeout/output permissions; file lỗi không publish; credentials không lộ |
| Restore | Unauthorized/forbidden; thiếu confirmation; invalid/untrusted file; traversal; subprocess fail/timeout; successful path mock và integration DB test có guard |
| Seed/export | Chạy hai lần không tăng duplicate; reset guard/rollback; đủ 13 bảng/FK; SQL import DB rỗng và smoke-test |

Chạy targeted tests rồi regression tương ứng dependency; ghi chính xác command/kết quả hoặc lý do chưa chạy. Không coi zero tests là đã xác minh feature. Sau khi checks phù hợp pass, không lặp test vô ích.

# Debugging Protocol

Khi fix bug, làm theo thứ tự:

1. Đọc lỗi nguyên văn, che secret khi trích lại.
2. Xác định cách reproduce và môi trường/revision.
3. Xác định expected vs actual.
4. Tìm request/response, URL/method/body/status và actor liên quan.
5. Kiểm tra logs/traceback.
6. Tìm file/function có khả năng liên quan, trace luồng gọi.
7. Chứng minh root cause bằng evidence trong code/log/test; phân biệt giả thuyết chưa kiểm chứng.
8. Nêu file cần sửa và patch nhỏ nhất hợp lý rồi implement trong phạm vi được giao.
9. Chạy test liên quan, thêm regression test tái hiện lỗi nếu có giá trị.
10. Chạy regression theo module/FK/API bị ảnh hưởng.
11. Báo file đã sửa.
12. Báo nguyên nhân lỗi.
13. Báo cách xác minh đã fix và hạn chế còn lại; cập nhật Bug Log/task.

Không sửa random nhiều file; không swallow exception bằng try/except rộng; không bỏ validation hoặc xóa test fail; không hard-code dữ liệu chỉ để demo chạy; không thay schema khi chưa chứng minh bug do schema. **Do not fix a bug by reintroducing legacy Vietnamese schema names.** Do not fix a bug by bypassing authentication, permissions, validation, foreign keys, or the official English schema. Do not delete migrations or reset the database just to make the error disappear. Khi chưa reproduce được, báo evidence còn thiếu và tiếp tục phần điều tra độc lập.

# Error Investigation Checklist

| Lỗi | Kiểm tra theo evidence trước khi patch |
| --- | --- |
| 400 | Content-Type/JSON parse, field bắt buộc/enum/length, query pagination/filter, validation fields; đối chiếu payload contract |
| 401 | Session/cookie/header, login route/backend, credentials đúng môi trường; API có redirect HTML ngoài contract không |
| 403 | Actor/status/role/group/codename; CSRF token/cookie/origin; phân biệt CSRF và permission; không mở quyền để chữa |
| 404 | Prefix/include/namespace/trailing slash, ID có tồn tại, queryset filtering; LOGIN_URL hiện chưa có route |
| 405 | HTTP method và allowed methods, client form/fetch, redirect do slash; không đổi GET thành mutation |
| 409 | Duplicate email/collation, FK protected delete, race hoặc business invariant; xác nhận đúng contract conflict |
| 500 | Traceback frame đầu thuộc project, request đã sanitize, DB/service/subprocess failure; reproduce tối thiểu, không trả raw traceback |
| Migration | `showmigrations`, `migrate --plan`, graph/dependency, model state vs DB thật, migration trong Git; không xóa/fake trước root cause |
| FK | Parent tồn tại, kiểu ID, NULL/on_delete, thứ tự seed/import/delete, response-question-option cùng survey; không tắt FK để che lỗi |
| MySQL connection | DB_NAME/HOST/PORT/USER đúng (không in password), service/network, client driver, charset, quyền DB/test DB; phân biệt timeout/access denied/unknown DB |
| Permission | Guard backend trên từng endpoint/method, trạng thái khóa, group assignment/cache, superuser bypass, direct API từ CUSTOMER |
| Password/auth | Hash API/mapping cột, USERNAME_FIELD/backend/manager, email normalization, validators, last_login mapping và session invalidation |
| Backup/restore subprocess | Executable/MYSQL_BIN, path khoảng trắng, argv/options/config, returncode/stderr đã che secret, timeout, file/dir quyền ghi, DB đích và dump encoding |

# Logging

Log account create/update/lock/unlock, password reset **action** (không password/hash), permission changes, backup/restore start/end/failure, seed summary. Ghi actor ID, target ID, action, timestamp, outcome và request/job ID nếu đã có. Hạn chế PII, không log toàn payload/SQL/command có credentials. Python/Django logging là hướng ban đầu vì chưa có history model; file log không commit. Không nuốt lỗi hoặc log success trước khi thao tác thực sự hoàn tất.

# Coding Style

Code dễ đọc hơn clever; function nhỏ, tên rõ, type hints khi hữu ích, docstring cho service quan trọng. Business logic không nhét hết vào view; repo chưa có service layer nên có thể thêm module service nhỏ theo nhu cầu, không dựng framework nội bộ. Giữ style repo, UTF-8 và thông báo tiếng Việt nhất quán. Không over-engineer đồ án sinh viên.

# Git Rules

Branch theo feature; tại audit đang ở `feature/admin-user-management`. Commit nhỏ và có ý nghĩa; không tự push/commit nếu task chưa yêu cầu. Không commit `.env`, backup DB, credential tạm hoặc dữ liệu thật; `database/crm_db.sql` demo được duyệt là ngoại lệ có chủ đích với SQL backup. Không sửa migration đã merge khi có thể thêm migration. Trước kết thúc xem `git status`, `git diff` (cả file mới), `git diff --check`; không ghi đè thay đổi người khác.

# Definition of Done

Feature DONE khi đúng requirement và schema; permission/validation/error handling đầy đủ; relevant tests pass có evidence; không lộ secret, không phá chức năng cũ; migration được review nếu có; API usage/contract được ghi khi cần; `plans.md` cập nhật trạng thái, test evidence, bug/decision liên quan. Thiếu runtime hoặc dependency cần thiết thì ghi BLOCKED/TODO đúng thực tế, không đánh DONE dựa trên code review.

Task chỉ viết tài liệu: kiểm tra đủ yêu cầu, nhất quán giữa ba file, phân biệt hiện trạng/đề xuất, kiểm tra diff và chỉ sửa file được giao. Không implement feature để minh họa tài liệu.

## Independent Module Development

This module may be developed before other team modules are available.

When related models/modules do not yet exist:

- do not invent their implementation;
- do not duplicate their business logic;
- use the official database schema to define expected integration points;
- keep dependencies minimal;
- isolate integration assumptions;
- record unresolved integration points in plans.md;
- do not block standalone implementation unless the missing dependency is technically required.

The module must be designed so it can be integrated into the full project later with minimal changes.

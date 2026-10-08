# Living plan — CRM cầu lông

**Latest verification — TV1, 2026-10-08:** source develop uses Account English;
live `crm_db` on the current machine still has legacy auth tables. Do not treat
older live alignment notes below as evidence for this machine. TV1 changes and
144-test MySQL verification are recorded in the final dated section. Live DB
alignment remains a separate owner-reviewed task; no live mutation was made.

**CURRENT ACTIVE ACCOUNT STATE (2026-09-29):** `TaiKhoan` / `tai_khoan` = **REMOVED LEGACY IMPLEMENTATION**. `Account` / `accounts` = **ONLY SUPPORTED ACCOUNT IMPLEMENTATION**. `AUTH_USER_MODEL='accounts.Account'`; live `crm_db.accounts` has the eight official columns and zero rows; `accounts/0001_initial` is applied. Historical audit and migration proposals below are retained as dated evidence, not active instructions to restore or convert the removed model.

Cập nhật khảo sát: **2026-09-28**. Baseline Git: `1d076ac`, nhánh `feature/admin-user-management`. Phạm vi lần lập kế hoạch này: chỉ `AGENTS.md`, `prompts.md`, `plans.md`; không implement feature, không đổi settings/models/migrations, không kết nối hay thay đổi DB.

Schema English chính thức do chủ đồ án cung cấp được ghi tại [AGENTS.md](AGENTS.md). Prompt theo tác vụ: [prompts.md](prompts.md). Mục tiêu xuyên suốt: requirements → database → backend/API → test/debug → frontend → integration → demo → sửa lỗi → báo cáo.

Ưu tiên source of truth: (1) official English schema của chủ đồ án → (2) explicit owner decisions sau schema → (3) AGENTS.md architecture rules → (4) plans.md approved decisions → (5) current implementation → (6) old project/assignment documents. Code/migrations legacy chỉ là evidence CURRENT STATE. ADR-008 ghi correction bắt buộc; mọi đề xuất cũ giữ model label legacy làm target bị thay thế.

## Cách duy trì kế hoạch

- `[ ] TODO`: chưa bắt đầu, có thể đang chờ dependencies bình thường.
- `[~] IN PROGRESS`: đang thực hiện, ghi người phụ trách và bước tiếp trong Notes.
- `[x] DONE`: acceptance đạt và có evidence review/test phù hợp.
- `[!] BLOCKED`: có trở ngại cụ thể ngoài task; Notes nêu lý do và điều kiện mở chặn.
- Mỗi dòng task có ID, nội dung, dependencies, acceptance criteria, test required và notes. `—` nghĩa là không có dependency, không có nghĩa bỏ qua AGENTS.md.
- Chỉ chuyển DONE khi có kết quả thật. Khi bắt đầu/kết thúc task, cập nhật trạng thái, evidence command/result/ngày trong Notes hoặc Verification Log; liên kết BUG/ADR nếu có.
- Giữ ID ổn định. Task lớn có thể tách `Pxx-nna`/`Pxx-nnb` và ghi dependency; không xóa lịch sử blocker/quyết định. Sửa roadmap theo code mới được duyệt, không theo tài liệu legacy.
- Tất cả task chưa ghi owner mặc định thuộc người phụ trách quản trị; `EXT-*` cần phối hợp thành viên chủ quản. Không viết thay module khác chỉ để vượt dependency.

## Repository findings — HISTORICAL LEGACY BASELINE (superseded 2026-09-29)

| Hạng mục | Hiện trạng đã đọc từ source |
| --- | --- |
| Cấu trúc | `manage.py`, `config/`, 7 apps: accounts, shop, catalog, admin_portal, customers, feedback, surveys |
| Dependencies | `requirements.txt`: Django 5.2.17, mysqlclient 2.3.0, python-dotenv 1.2.3; không DRF/pytest |
| DB settings (CURRENT STATE) | `config/settings.py`: MySQL, utf8mb4, strict mode, đọc `.env`; timezone Asia/Ho_Chi_Minh, USE_TZ=True; `.env.example` dùng DB_NAME=crm_db đúng quyết định mới nhất |
| Auth (LEGACY IMPLEMENTATION) | `AUTH_USER_MODEL='accounts.TaiKhoan'`, legacy `TaiKhoan(AbstractUser)` / `tai_khoan`; Groups/user_permissions kế thừa; chưa có guard nghiệp vụ; không phải target |
| Models | Chỉ accounts có model; models của 6 apps khác là scaffold |
| Migrations | Chỉ `apps/accounts/migrations/0001_initial.py` có operation; các app khác chỉ `__init__.py`; chưa biết trạng thái DB thật |
| URLs/views | `config/urls.py` chỉ `/admin/`; mọi `views.py` scaffold, chưa có app URLconf; LOGIN_URL trỏ `accounts:login` chưa tồn tại |
| Tests | Mọi `tests.py` chỉ import TestCase và comment; chưa có test cases; chưa cấu hình test DB riêng |
| Env/tools | Có `.env.example`, chưa có `.env` trong checkout. Python đang resolve tới MSYS2 3.12.7; pip/Django/MySQLdb/dotenv không có trong interpreter này; mysql/mysqldump không trên PATH |
| Assets/tooling | Chưa có scripts/database/templates/static/service/API docs/seed; MYSQL_BIN có trong env example nhưng chưa được code tiêu thụ |
| Git/docs | README chỉ tên repo; gitignore đã có .env, database/backups/, *.log, venv; working tree sạch ở audit ban đầu. Review correction thấy 3 guidance files và badminton_crm_db.db đều untracked; giữ nguyên file DB ngoài scope |

Không suy ra MySQL chưa cài chỉ từ PATH, không suy ra DB chưa migrate chỉ từ checkout hoặc file `badminton_crm_db.db`, không báo backend test pass dựa trên đọc source. Các phiên bản dependency ghi ở đây là nội dung file, chưa kiểm chứng cài đặt thành công trên máy Windows này.

## CURRENT STATE — Official English Architecture

- `Account` / `accounts` / official English fields; auth setting `accounts.Account` đã align với live SQL schema. Không khôi phục model label legacy.
- Đủ 13 mapping chính thức: `Account→accounts`, `Customer→customers`, `Product→products`, `Category→categories`, `Brand→brands`, `CustomerPreference→customer_preferences`, `Feedback→feedbacks`, `Survey→surveys`, `SurveyQuestion→survey_questions`, `SurveyOption→survey_options`, `SurveyRecipient→survey_recipients`, `SurveyResponse→survey_responses`, `SurveyAnswer→survey_answers`.
- Tên classes/fields/tables/columns/routes/payloads/services/helpers/constants/permissions/tests/fixtures/seed/migrations mới và ví dụ kỹ thuật đều English. Tiếng Việt dành cho labels/messages/comments/báo cáo. `Meta.db_table`/`db_column` giữ tên vật lý chuẩn; `handled_by`/`created_by` không đổi thành cột có hậu tố `_id`.
- Database chính thức `crm_db`, `DB_NAME=crm_db`, charset `utf8mb4`, collation `utf8mb4_unicode_ci`; setup DDL trong AGENTS.md. File deliverable vẫn `database/crm_db.sql`. Test/restore chỉ DB disposable riêng, không tự chạy DDL ở bước tài liệu.
- `Account.role` chỉ ADMIN/CUSTOMER; ACTIVE ADMIN có framework superuser permissions, CUSTOMER không có quyền quản trị mặc định, LOCKED bị từ chối login/session. Groups/Permissions dùng bảng kỹ thuật. Account foundation đã hoàn thành; CRUD còn chờ policy delete/reset và backend permission guards.

## Conflicts / blockers đã ghi nhận

| ID | Conflict / evidence | Tác động và cách mở chặn |
| --- | --- | --- |
| C-01 | HISTORICAL: legacy model/table từng khác official SQL schema | RESOLVED: owner loại bỏ legacy; active model/migration dùng `Account` / `accounts` |
| C-02 | HISTORICAL: role legacy từng khác official `role` | RESOLVED: live DB không có legacy table/data; Account chỉ ADMIN/CUSTOMER, không data conversion |
| C-03 | HISTORICAL: AbstractUser từng thêm Auth columns ngoài schema | RESOLVED: AbstractBaseUser/PermissionsMixin dùng `db_column` và properties; live `accounts` chỉ tám cột; technical M2M đã tạo |
| C-04 | Schema chưa định nghĩa đầy đủ NULL/default/unique/index/FK/on_delete/rating range và enum một số bảng | Chốt ràng buộc theo module trước migration; không tự suy luận cascade hay email unique đã tồn tại |
| C-05 | HISTORICAL: applied migration/data state unknown | RESOLVED: live 13 business tables zero rows; old accounts migration was unapplied; new accounts 0001 applied and no pending plan |
| C-06 | HISTORICAL: runtime and local credentials unavailable | RESOLVED: Windows CPython 3.12.10, pinned dependencies, local ignored `.env`, live MySQL and separate `test_crm_db` verified |
| C-07 | LOGIN_URL `accounts:login` nhưng chỉ có route admin | Framework authentication foundation works; resolve user-facing login URL during frontend/integration before using redirect-based protected views |
| C-08 | `.env.example` trước P00-08 có password mẫu cụ thể và SECRET_KEY placeholder | Password mẫu đã đổi sang placeholder; SECRET_KEY vẫn là placeholder cần thay trong .env riêng, không commit credential |
| C-09 | Chưa có model customers/catalog/feedback/surveys | Full seed, FK/delete integration và SQL export phụ thuộc EXT-*; không tự triển khai module đồng đội ở bước này |
| C-10 | Quyết định trước từng dùng tên database khác; chủ đồ án xác nhận database chính thức là `crm_db` ngày 2026-09-29 | RESOLVED: `.env.example`, guidance và SQL filename thống nhất `crm_db`; không thay đổi DB thật |

Historical audit only: legacy identifiers formerly existed in source. Active `apps/` and `config/` Python files no longer reference the removed model/table; do not add compatibility or data conversion.

## Gate chuyển giai đoạn

1. Phase 0 runtime/live DB audit, Account Foundation và P00-10 business rules đã hoàn tất. GATE-H/J được chốt theo owner instruction 2026-09-30; Account CRUD backend là task tiếp theo. Không khôi phục legacy model hoặc migration/data-conversion path.
2. Phase 2/3 có thể xen kẽ: hoàn thiện permission gate trước khi expose account mutations; không để endpoint tạm mở cho CUSTOMER.
3. Backup/restore có thể làm service/mock tests sau foundation/config; chạy thật cần DB demo/test và xác nhận restore đúng đích. Không phụ thuộc UI.
4. Seed đầy đủ chờ models/migrations do thành viên phụ trách cung cấp. SQL export chỉ sau seed/migration ổn định.
5. Phase 10 bắt đầu khi backend/API tương ứng đạt Phase 8 và contract Phase 9 đã ghi; frontend không đổi schema/API tùy tiện.
6. Mọi integration/demo destructive chỉ trên DB được chỉ định, có guard/xác nhận và recovery. Đánh DONE demo khi đã chạy, không chỉ có checklist.

## Dependencies phối hợp ngoài phạm vi quản trị

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] EXT-01 | Thống nhất models customers/preferences với chủ module | ADR-003; P01-01 | Bảng/cột chuẩn, account FK và delete/profile policy được duyệt | FK, status DELETED, uniqueness đã chốt | Hiện apps.customers scaffold; không tự làm thay; BLOCKED bởi P01-01; mở khi dependency đạt |
| [ ] EXT-02 | Thống nhất categories/brands/products với chủ catalog | ADR-003 | Đủ 3 models/migrations theo schema, Decimal price | FK category/brand, length/status/price | Hiện apps.catalog scaffold |
| [!] EXT-03 | Thống nhất feedbacks với chủ feedback | EXT-01; EXT-02; P01-01 | FK customer/product/handled_by, rating/status được duyệt | Handler/history, rating, delete protection | App apps.feedback, bảng feedbacks; BLOCKED bởi EXT-01, P01-01; mở khi dependency đạt |
| [!] EXT-04 | Thống nhất 6 bảng survey với chủ surveys | EXT-01; P01-01; ADR-003 | Questions/options/recipients/responses/answers đúng quan hệ, creator FK | Question-option-survey invariants, status/timestamp | Hiện apps.surveys scaffold; BLOCKED bởi EXT-01, P01-01; mở khi dependency đạt |

## PHASE 0 — Repository Audit

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [x] P00-01 | Xác định project structure | — | Entry points/7 apps/ownership và scaffold được liệt kê | Đối chiếu rg --files, git ls-files | V-001; source audit đã hoàn tất |
| [x] P00-02 | So sánh schema source với schema chính thức | P00-01 | Ghi đủ C-01 đến C-04 và C-09; không đổi code | Đọc models và 0001_initial | V-001; chưa là xác minh DB thật |
| [x] P00-03 | Audit auth architecture | P00-01 | Custom user, inherited fields/Groups, middleware, login URL rõ | Đối chiếu settings/model/migration | C-01/02/03/07; V-001 |
| [x] P00-04 | Audit migrations trong repository | P00-01 | Đúng danh sách migration/dependencies, phân biệt apply state | Đọc migrations, git history | Chỉ accounts 0001; C-05 còn mở |
| [x] P00-05 | Audit URL/API structure | P00-01 | Chỉ admin URL, chưa API convention/service/FBV/CBV nghiệp vụ | Đọc config/urls và views | Không giả định DRF; V-001 |
| [x] P00-06 | Audit test setup hiện có | P00-01 | Ghi tests scaffold, Django runner đề xuất, chưa test DB | Đọc 7 tests.py/requirements | Không có test nghiệp vụ đã pass |
| [x] P00-07 | Audit dependency/.env setup từ source | P00-01 | Pin deps/config vars/gitignore/tools gap được ghi | Đọc requirements/.env.example, kiểm tra interpreter/PATH | V-001; không in lại credential mẫu |
| [x] P00-08 | Chuẩn bị và xác minh runtime Windows/dev/test config | P00-07; ADR-008 | Đúng venv/deps, config DB_NAME=crm_db, utf8mb4/utf8mb4_unicode_ci, MySQL tools xác minh, test DB tách biệt | python --version; manage.py check; tool --version; kết nối test | DONE 2026-09-29: Windows CPython 3.12.10 x64, full pinned deps, ignored `.env`, MySQL80 và `test_crm_db`; check pass với static warning |
| [x] P00-09 | Xác minh DB thật/migrations/data cần giữ | P00-04; P00-08 | Read-only schema/state, phiên bản MySQL, dữ liệu/FK hiện có được báo; DB đích rõ | showmigrations; migrate --plan; schema inspection an toàn | DONE 2026-09-29: `crm_db` có 13 business tables/0 rows, `accounts` đúng tám cột/constraints, không legacy table; old 0001 unapplied trước alignment |
| [x] P00-10 | Account business rules and permission contract | P00-02; P00-03; P00-09 | ACTIVE ADMIN guard, self/last ADMIN, lock/unlock, role, reset, FK-safe hard delete | 21 Account tests, check, makemigrations dry-run | DONE 2026-09-30; services/selectors/errors and transaction locking implemented |
| [x] ACCOUNT CRUD BACKEND | Django HTML Account administration backend | P00-10 | Namespaced routes, explicit forms, safe selectors/services, POST mutations, CSRF, minimal templates | 35 Account tests, check, migration dry-run | DONE 2026-09-30; `/admin-portal/accounts/` routes; email-only edit plus dedicated role/status actions; no REST API added |

## PHASE 1 — Account Foundation

Không phá database của thành viên khác. Ngoại lệ owner 2026-09-29 đã cho thay initial legacy migration sau khi kiểm chứng live SQL schema và zero rows; không dùng `--fake` hoặc DROP.

### Pre-CRUD decision gates A–J

Tên Account/accounts/crm_db và 13 bảng nghiệp vụ đã FINAL. Gate-I là quyết định đã hoàn tất; các gate còn lại không mở lại naming. Trước sửa model Phase 1 phải inspect settings/model/migration files, `showmigrations`, `AUTH_USER_MODEL`, DB tables nếu truy cập được và migration legacy đã apply hay chưa. Trước CRUD, GATE-A..J phải DONE và ALN-11/P01-07 có evidence. Thiếu evidence thì không đánh Account migration DONE.

`[!] BLOCKED` dưới đây chặn implementation phụ thuộc; vẫn được chuẩn bị inventory, mapping, đề xuất/test plan độc lập. Khi decision chặn một task, đánh BLOCKED cả các task phụ thuộc trực tiếp/gián tiếp; Notes ghi dependency mở chặn. Không coi trạng thái BLOCKED là cấm khảo sát hoặc lập phương án.

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [x] GATE-A | A. Current migration state | ALN-02 | Có showmigrations, files/graph, DB tables thật, AUTH_USER_MODEL và trạng thái accounts/0001_initial.py | Đối chiếu source với DB read-only | DONE: old 0001 unapplied; new Account 0001 applied, no pending migration |
| [x] GATE-B | B. Shared data preservation | GATE-A; ALN-03 | Xác định dữ liệu Account cần giữ trước alignment | Inventory counts/PK/FK, dữ liệu lỗi đã sanitize | DONE: 13 business tables zero rows; legacy table absent; no legacy data conversion or reset |
| [x] GATE-C | C. Django Auth → accounts.password_hash mapping | P00-03 | Thiết kế mapping/adapter an toàn được review trước migration; set_password/check_password hoặc Django equivalent, không thêm cột | Plan create/login/reset, persisted hash và session compatibility | DONE: Django `password` field uses `db_column=password_hash`; `last_login` maps `last_login_at`; tests pass |
| [x] GATE-D | D. Account migration alignment | GATE-A; GATE-B; GATE-C; GATE-I | Existing SQL table retained, fresh test DB created from official DDL, no legacy conversion | Migration plan and live/test verification | DONE: owner explicitly removed legacy; 0001 validates existing accounts and creates technical M2M; applied without changing eight columns |
| [x] GATE-E | E. Legacy profile disposition | GATE-B | No legacy profile data exists or is migrated into Account | Read-only live inventory | N/A resolved: no legacy table or rows; Customer remains teammate module |
| [x] GATE-F | F. Role migration decision | GATE-B | Only ADMIN/CUSTOMER in Account; no legacy role conversion | Choice and SQL CHECK tests | N/A conversion: no legacy table/data; official two-role schema enforced |
| [x] GATE-G | G. Django Groups/Permissions strategy | GATE-I | ACTIVE ADMIN framework superuser; technical M2M; backend API guard later | Permission and locked tests | DONE foundation: properties derive from role/status; Groups/Permissions technical tables verified; CRUD guards remain Phase 3 |
| [x] GATE-H | H. Account hard-delete policy | GATE-B | Chốt hard-delete có được phép và điều kiện; self/last ADMIN, FK/history consequences, contract riêng LOCKED/delete | Review relation matrix; P02-08 kiểm lại FK thực trước implementation | Owner 2026-09-30: hard delete only without protected references; self/final ADMIN protected; use LOCKED otherwise. Live FK inventory includes customers RESTRICT, feedbacks SET NULL, surveys RESTRICT, django_admin_log NO ACTION and technical M2M NO ACTION. |
| [x] GATE-I | I. Django technical tables allowance | ADR-003 | Framework tables ngoài 13 business tables được phép, không domain table bổ sung/trùng chức năng | Đối chiếu explicit owner instruction và ba tài liệu | DONE 2026-09-28; chỉ quyết định allowance, chưa tạo/verify tables |
| [x] GATE-J | J. Password reset flow | P00-03 | Admin supplies new password to service; no email/token/generated secret | Django validators/hash and old/new password tests | Owner 2026-09-30 specified service input `new_password`; service returns ID only. Django session auth hash invalidates prior target sessions after password change. UI/delivery contract remains for Account CRUD backend, without email. |

### Historical legacy field inventory — superseded by owner removal decision

This table was a pre-decision analysis. No source table or business rows exist in live `crm_db`; do not use it as an instruction to query or migrate the removed model.

Phân loại dưới đây là **inventory/đề xuất mapping**, không phải lệnh chuyển dữ liệu hoặc approval bỏ dữ liệu. Với mỗi field phát hiện thêm khi inspect DB, bổ sung một dòng. Nhãn dùng thống nhất: `maps directly`, `maps to Customer`, `transforms`, `deprecated`, `requires owner decision`. Nhãn deprecated không cho phép xóa dữ liệu; phải chốt bảo toàn/archive trước.

Account target giữ đúng 8 field: account_id, email, password_hash, role, status, last_login_at, created_at, updated_at. Customer target giữ đúng customer_id, account_id, full_name, phone, date_of_birth, gender, address, playing_level, status, created_at, updated_at, deleted_at; không suy diễn giá trị các field chưa có source.

| Legacy source field / relation | Classification | Target / disposition cần xác minh |
| --- | --- | --- |
| TaiKhoan.id | maps directly | Account.account_id; giữ PK và mọi FK, không re-number |
| TaiKhoan.email | transforms | Account.email; normalize/unique/collation và duplicate/blank policy chưa chốt |
| TaiKhoan.password | maps directly | Account.password_hash; giữ encoded hash hợp lệ, không rehash hash; qua GATE-C |
| TaiKhoan.last_login | maps directly | Account.last_login_at; xác minh NULL và timezone |
| TaiKhoan.ho_ten | maps to Customer | Candidate Customer.full_name; GATE-E/owner phải duyệt trước chuyển |
| TaiKhoan.so_dien_thoai | maps to Customer | Candidate Customer.phone; GATE-E/owner phải duyệt trước chuyển |
| TaiKhoan.vai_tro | transforms | Account.role ADMIN/CUSTOMER; GATE-F chốt từng ADMIN/QUAN_LY/NV_CSKH/KHACH_HANG, không tự nâng quyền |
| TaiKhoan.is_active | transforms | Candidate True→ACTIVE, False→LOCKED; xác minh mâu thuẫn dữ liệu và policy trước chuyển |
| TaiKhoan.ly_do_khoa | requires owner decision | Không có cột target; owner chốt archive/preservation/disposition, không tự bỏ |
| TaiKhoan.ngay_khoa | requires owner decision | Không có cột target; owner chốt archive/preservation/disposition, không tự bỏ |
| TaiKhoan.username | deprecated | Không có cột target; inventory unique/login references và cách bảo toàn trước loại runtime field |
| TaiKhoan.first_name | requires owner decision | Không tự gộp/ghi đè Customer.full_name; chốt ưu tiên source/profile matching |
| TaiKhoan.last_name | requires owner decision | Không tự gộp/ghi đè Customer.full_name; chốt ưu tiên source/profile matching |
| TaiKhoan.date_joined | transforms | Candidate Account.created_at; xác minh ý nghĩa/timezone, không giả định là updated_at |
| TaiKhoan.is_staff | requires owner decision | Không có cột target; auth/admin adapter theo policy, không tự suy ra role ADMIN |
| TaiKhoan.is_superuser | requires owner decision | Không có cột target; không tự chuyển thành ADMIN/bypass quyền |
| TaiKhoan.groups | transforms | Giữ membership qua technical M2M theo GATE-F/G, remap model/contenttypes nếu cần |
| TaiKhoan.user_permissions | transforms | Giữ quyền hợp lệ theo GATE-G, không sao chép quyền dẫn tới escalation |

Target Account.updated_at chưa có source trực tiếp; timestamp backfill cần quyết định và evidence. Tương tự, không tự tạo Customer cho mọi account hoặc bịa các field profile thiếu. GATE-E/F chỉ DONE khi toàn inventory có disposition và preservation policy được review.

### Migration / deletion — relationship safety inventory

ALN-02/03 phải liệt kê **mọi FK thực tế**, mở rộng bảng này cho tất cả quan hệ chính thức và framework tables phát hiện được. Không coi ba quan hệ mẫu là toàn bộ FK. UNKNOWN không phải nullable hoặc CASCADE mặc định. GATE-D/H chỉ đóng sau khi các quan hệ ảnh hưởng được chốt; P02-08 đối chiếu lại DB/models trước hard-delete.

| FK source | FK target | Nullable / required | Expected ON DELETE | Business consequence |
| --- | --- | --- | --- | --- |
| customers.account_id | accounts.account_id | UNKNOWN — owner customers chốt | UNKNOWN — không giả định CASCADE | Có thể mất liên kết profile/account; cần policy giữ lịch sử |
| feedbacks.handled_by | accounts.account_id | UNKNOWN — owner feedback chốt | UNKNOWN — không giả định CASCADE | Có thể mất attribution xử lý feedback |
| surveys.created_by | accounts.account_id | UNKNOWN — owner surveys chốt | UNKNOWN — không giả định CASCADE | Có thể mất attribution tạo survey |
| Framework FK/M2M thực tế — chờ inventory | Auth PK/model/contenttypes thực tế | UNKNOWN — inspect schema | UNKNOWN — inspect DB và Django on_delete riêng | Membership/permission/admin history có thể mất hoặc trỏ sai |

### Account alignment — historical proposal and completed SQL-first implementation

**Historical only — REMOVED LEGACY IMPLEMENTATION:** the former model/table and auth setting were never applied to live `crm_db`.

**Current — ONLY SUPPORTED:** `Account` / `accounts` / official English fields, `AUTH_USER_MODEL='accounts.Account'`.

Owner quyết định thay migration foundation khi live inspection xác nhận SQL-owned `accounts` đúng schema, zero business rows, legacy table absent, và old 0001 chưa apply. New 0001 validates existing table, creates only technical M2M, and also builds official table in a fresh disposable MySQL test DB. No legacy conversion, reset, fake migration, or destructive SQL was run.

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [x] ALN-01 | Inspect migration history | P00-04 | Dependency graph, auth swappable references, migrations đã chia sẻ và references legacy được liệt kê | Source/Git graph review | DONE 2026-09-29: source-only MigrationLoader graph, accounts 0001 committed in d8a2f2a, depends auth 0012; admin 0001 swappable dependency resolves accounts __first__; applied state UNKNOWN, ALN-02 remains blocked |
| [x] ALN-02 | Determine applied migrations and live state | ALN-01; P00-09 | Source graph and live DB state known | showmigrations, migrate --plan, read-only inspection | DONE: old accounts 0001 unapplied; 13 official tables/zero rows, no legacy table |
| [x] ALN-03 | Determine preservation scope | ALN-02 | Existing data at risk identified | Counts and FK inventory | DONE: all 13 business tables zero rows; FKs to accounts from customers/feedbacks/surveys; no legacy data to move |
| [x] ALN-04 | Design safe alignment strategy | ALN-01; ALN-02; ALN-03; GATE-D | Existing SQL table retained, fresh test path works | Migration source/plan and live/test verification | DONE: state-only CreateModel plus guarded existing-or-fresh SQL schema; no data conversion |
| [x] ALN-05 | Align model naming | ALN-04; P01-01 | Runtime registry and setting resolve Account | get_user_model and naming scan | DONE: only Account in active Python; `AUTH_USER_MODEL='accounts.Account'` |
| [x] ALN-06 | Align table naming | ALN-05 | db_table=accounts, technical M2M valid | Live/test introspection | DONE: `accounts` retained; M2M `accounts_groups`/`accounts_user_permissions` created |
| [x] ALN-07 | Align columns and choices | ALN-06; P01-02; P01-04; P01-05 | Exactly eight official columns and two role/status values | Live schema/index/CHECK inspection, model tests | DONE: live columns unchanged; password/last-login db_column mapping verified |
| [x] ALN-08 | Verify authentication | ALN-07; P01-03; P01-06 | Email login/hash/last-login/status/session behavior | MySQL Account tests | DONE: correct/wrong password, ACTIVE/LOCKED, last login and old-session denial pass |
| [x] ALN-09 | Verify permissions | ALN-08; ADR-003 | ADMIN framework permission and technical M2M behavior | MySQL Account tests and live table inspection | DONE: ADMIN superuser property and group mapping pass; API guards remain Phase 3 |
| [x] ALN-10 | Verify existing data | ALN-09; ALN-03 | No business data changed by alignment | Before/after counts and schema | DONE: accounts zero before/after; official eight columns retained |
| [x] ALN-11 | Run migration tests and alignment gate | ALN-10; P01-06 | Fresh test DB and existing SQL-owned live table both align | 10 targeted MySQL tests; showmigrations; migrate --plan | DONE: test DB migration pass; live 0001 applied; no pending operations or legacy table |
| [x] ALN-12 | Pre-migration backup applicability | ALN-04; GATE-B | Backup before rename/transform/remove of existing data | Review mutation scope and counts | N/A with evidence: zero business rows, no rename/transform/remove; migration only adds Django technical tables and records |

### Account Foundation — completed 2026-09-29

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [x] P01-01 | Account model mapping | ALN-04; ADR-008 | Account/Auth ↔ exact eight `accounts` columns | Model state and live schema review | DONE: `get_user_model()` Account; `db_table=accounts`; physical columns exact |
| [x] P01-02 | Manager/email/password adapter | P01-01 | Email login, normalize, Django hashing, required validation | MySQL manager/password tests | DONE: create_user/create_superuser, trim/lower, duplicate and weak-password rejection |
| [x] P01-03 | Authentication foundation | P01-02; P01-04; ALN-05 | Email/password authentication, last_login_at, locked login/session denial | MySQL auth/session tests | DONE: framework auth verified; user-facing login route remains separate frontend/integration task |
| [x] P01-04 | Status constants and auth mapping | P01-01 | ACTIVE/LOCKED controls is_active | Locked login/existing session tests | DONE: status property and backend denial pass |
| [x] P01-05 | Role constants and permissions | P01-01; ADR-008 | ADMIN/CUSTOMER only; derived framework permissions | Admin/Customer/invalid role tests | DONE: no legacy role conversion; ACTIVE ADMIN is_staff/is_superuser |
| [x] P01-06 | SQL-owned migration alignment | ALN-07; P00-09 | Existing accounts retained; fresh MySQL test creation; state accurate | makemigrations check, test DB, live migrate/plan | DONE: old 0001 was unapplied; owner-authorized replacement applied without altering official columns |
| [x] P01-07 | Foundation tests | P01-03; P01-06; ALN-11 | Account auth/model/manager/DB mapping passes on MySQL | Django accounts suite | DONE: 10 targeted tests pass; live Account 0001 applied, no pending migrations |

## PHASE 2 — Account Management Backend

Pre-CRUD gate: GATE-A..J và ALN-11/P01-07 đã DONE. Django HTML Account CRUD backend is complete; Phase 2 rows below describe the older proposed JSON API contract and remain separate future work. Their Notes claiming GATE-H/J blockers are historical and no longer current blockers.

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P02-01 | List accounts/pagination | P01-07; P03-01; ADR-004; GATE-A..J | List đúng envelope, page size có giới hạn, order ổn định, không hash | Empty/multiple pages, invalid page, non-admin | Candidate GET /api/admin/accounts/; BLOCKED bởi P01-07, P03-01, GATE-A, GATE-B, GATE-C, GATE-D, GATE-E, GATE-F, GATE-G, GATE-H, GATE-J; mở khi dependency đạt |
| [!] P02-02 | Search email | P02-01 | q normalize, đúng kết quả, không search field legacy | Empty/no match/case/Unicode input | Search full_name chỉ khi thêm requirement join customers; BLOCKED bởi P02-01; mở khi dependency đạt |
| [!] P02-03 | Filter role | P02-01 | ADMIN/CUSTOMER được lọc, giá trị sai có lỗi rõ | Từng role + invalid + search kết hợp | Chỉ nhận field role chính thức; BLOCKED bởi P02-01; mở khi dependency đạt |
| [!] P02-04 | Filter status | P02-01 | ACTIVE/LOCKED được lọc, kết hợp query nhất quán | Từng status + invalid + pagination | Không dùng DELETED cho account; BLOCKED bởi P02-01; mở khi dependency đạt |
| [!] P02-05 | Account detail | P01-07; P03-01; ADR-004; GATE-A..J | Detail ID tồn tại, chỉ fields cho phép, 404 đúng | 200/401/403/404, hash không lộ | accounts.account_id; BLOCKED bởi P01-07, P03-01, GATE-A, GATE-B, GATE-C, GATE-D, GATE-E, GATE-F, GATE-G, GATE-H, GATE-J; mở khi dependency đạt |
| [!] P02-06 | Create account | P01-07; P03-01; ADR-004; GATE-A..J | Validate email/password/role, duplicate conflict, hash đúng | Valid/invalid/duplicate/race constraint/permission | Customer profile là nghiệp vụ riêng nếu có; BLOCKED bởi P01-07, P03-01, GATE-A, GATE-B, GATE-C, GATE-D, GATE-E, GATE-F, GATE-G, GATE-H, GATE-J; mở khi dependency đạt |
| [!] P02-07 | Update account | P02-06 | PATCH whitelist, normalize, audit timestamps đúng | Partial update, duplicate, immutable fields, permission | Không cho lách reset qua password_hash; BLOCKED bởi P02-06; mở khi dependency đạt |
| [!] P02-08 | Chốt delete rule | P00-10; EXT-01; EXT-03; EXT-04; ADR-005; GATE-H | Ma trận FK/history, self-delete/last ADMIN, contract được duyệt | Review relation/on_delete thực tế | Nếu models chưa có, quyết định sơ bộ chưa đủ để triển khai xóa; BLOCKED bởi P00-10, EXT-01, EXT-03, EXT-04, GATE-H; mở khi dependency đạt |
| [!] P02-09 | Implement delete behavior | P02-08; P03-01 | Theo policy, không mất lịch sử, conflict rõ | Protected FK, eligible delete, rollback, 404/403 | Không âm thầm DELETE=lock; BLOCKED bởi P02-08, P03-01; mở khi dependency đạt |
| [!] P02-10 | Lock account | P01-04; P03-01; ADR-005; GATE-A..J | LOCKED, log actor, session/login bị chặn, policy self/last admin | Lock lặp, session cũ, last ADMIN, 403/404 | Không thêm cột ngoài schema; BLOCKED bởi P01-04, P03-01, GATE-A, GATE-B, GATE-C, GATE-D, GATE-E, GATE-F, GATE-G, GATE-H, GATE-J; mở khi dependency đạt |
| [!] P02-11 | Unlock account | P02-10 | ACTIVE, có thể login lại, action idempotency đã chốt | Unlock lặp, login sau unlock, 403/404 | Log outcome; BLOCKED bởi P02-10; mở khi dependency đạt |
| [!] P02-12 | Reset password | P01-03; P03-01; ADR-005; GATE-A..J | Flow có validators/hash, permission/log, không password/hash response | Old/new password, weak input, LOCKED, session policy, 403/404 | GATE-J: admin cung cấp hoặc hệ thống sinh mật khẩu tạm, hoặc reset link/token; BLOCKED bởi P01-03, P03-01, GATE-A, GATE-B, GATE-C, GATE-D, GATE-E, GATE-F, GATE-G, GATE-H, GATE-J; mở khi dependency đạt |
| [!] P02-13 | Account API/service tests | P02-01..12; P03-02 | Tất cả account flows, error contract, no hash exposure pass | Targeted + account regression, CSRF | Không bỏ qua DELETE nếu còn blocked để claim toàn phase DONE; BLOCKED bởi P02-01, P02-02, P02-03, P02-04, P02-05, P02-06, P02-07, P02-08, P02-09, P02-10, P02-11, P02-12, P03-02; mở khi dependency đạt |

## PHASE 3 — Authorization

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [x] P03-01 | ADMIN access guard | P01-07; ADR-003; ADR-004 | Guard tập trung role/status cho Account management, dùng được trước Phase 2 API | ADMIN/anonymous/CUSTOMER/LOCKED | DONE in P00-10: `require_active_admin` reloads current DB state; HTTP wiring and detailed Group permissions belong to later tasks. |
| [!] P03-02 | CUSTOMER restriction | P03-01 | CUSTOMER không gọi được mọi method/action quản trị | Direct API kể cả có group/admin-looking payload | Không dựa UI; BLOCKED bởi P03-01; mở khi dependency đạt |
| [!] P03-03 | Groups CRUD | P03-01; ADR-003 | Group names/CRUD validate, không thêm role DB | Duplicate/name invalid/assigned group delete policy | Dùng Django Groups nếu ADR cho phép; BLOCKED bởi P03-01; mở khi dependency đạt |
| [!] P03-04 | Permissions catalog/action matrix | P03-03 | Action ↔ codename rõ, list chỉ permission được phép quản lý | Allowed/unknown permission, contenttype mapping | Mapping theo model label đã chốt; BLOCKED bởi P03-03; mở khi dependency đạt |
| [!] P03-05 | Permission/group assignment | P03-04 | Assign/revoke group permissions và membership account theo contract | Add/remove, invalid IDs, atomic failure, no escalation | Log actor/target/change; BLOCKED bởi P03-04; mở khi dependency đạt |
| [!] P03-06 | Permission checks toàn backend | P03-05; P02-13 | Action kiểm tra role gate + quyền chi tiết đúng policy | Missing/revoked rights, each HTTP method | Backup/restore bổ sung khi endpoints có; BLOCKED bởi P03-05, P02-13; mở khi dependency đạt |
| [!] P03-07 | Authorization tests | P03-06 | Permission matrix pass, session/status không bypass | Full auth/account suites + CSRF | Ghi matrix và evidence; BLOCKED bởi P03-06; mở khi dependency đạt |

## PHASE 4 — Backup

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P04-01 | Service/command interface | P00-08; ADR-006 | Module/command nhỏ, input/output contract rõ, dùng lại cho API/batch | Unit interface, invalid args | Dự kiến apps.admin_portal; chưa tồn tại; BLOCKED bởi P00-08; mở khi dependency đạt |
| [!] P04-02 | Backup filename | P04-01 | Timestamp + uniqueness, không ghi đè, tên server sinh | Hai backup cùng giây, invalid name | crm_db_<timestamp>_<unique>.sql; BLOCKED bởi P04-01; mở khi dependency đạt |
| [!] P04-03 | Backup directory/file lifecycle | P04-02 | database/backups; tạm → publish thành công; cleanup fail | Missing dir/permission/output fail | Đã gitignore; không commit dumps; BLOCKED bởi P04-02; mở khi dependency đạt |
| [!] P04-04 | DB/executable/credentials config | P04-01 | Đọc settings/MYSQL_BIN, validate sớm; password không argv/log | Missing config/tool, path khoảng trắng | Option file/login-path; dọn credentials tạm; BLOCKED bởi P04-01; mở khi dependency đạt |
| [!] P04-05 | mysqldump subprocess | P04-03; P04-04 | argv/no shell, utf8mb4, single transaction/no tablespaces, timeout/exitcode | Mock success/failure/timeout | Xác minh InnoDB/DDL caveat trong runbook; BLOCKED bởi P04-03, P04-04; mở khi dependency đạt |
| [!] P04-06 | Error handling | P04-05 | Lỗi ổn định, không fake success, stderr sanitize | Nonzero, tool missing, disk/permission failure | Giữ nguyên exception cause trong log an toàn; BLOCKED bởi P04-05; mở khi dependency đạt |
| [!] P04-07 | Logging và ADMIN API | P04-06; P03-01 | Log action/result ngoài secret, endpoint POST có guard | 401/403/CSRF, log capture, output contract | Không tự thêm bảng history; BLOCKED bởi P04-06, P03-01; mở khi dependency đạt |
| [!] P04-08 | scripts/backup.bat | P04-07 | Wrapper path-safe, env qua Python, ERRORLEVEL/exitcode đúng | Windows cwd/path có khoảng trắng, failure propagation | Không pause vô điều kiện; BLOCKED bởi P04-07; mở khi dependency đạt |
| [!] P04-09 | Backup tests | P04-08 | Unit/mock pass và smoke dump DB demo phù hợp | Success/failure/missing mysqldump/config | Không tạo backup dữ liệu thật trong test; BLOCKED bởi P04-08; mở khi dependency đạt |

## PHASE 5 — Restore

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P05-01 | Restore service/recovery contract | P04-09; ADR-006 | Input, result, partial failure, pre-backup và maintenance policy rõ | Unit contract, recovery failure simulation | Restore không atomic toàn dump; BLOCKED bởi P04-09; mở khi dependency đạt |
| [!] P05-02 | File validation/trust | P05-01 | Regular file/size/format/nguồn tin cậy; không chỉ check .sql | Missing/empty/oversize/untrusted SQL | Chốt upload hay server backup ID; BLOCKED bởi P05-01; mở khi dependency đạt |
| [!] P05-03 | Permission và confirmation | P05-01; P03-01 | ADMIN, confirm file + DB đích, cancel không có side effect | 401/403/no confirmation/mismatched target | Xác nhận từng thao tác restore thực tế; BLOCKED bởi P05-01, P03-01; mở khi dependency đạt |
| [!] P05-04 | Safe path handling | P05-02 | Canonical containment, không traversal/symlink/junction escape | ../, absolute outside, Windows paths, link escape | Không nhận executable từ request; BLOCKED bởi P05-02; mở khi dependency đạt |
| [!] P05-05 | mysql subprocess/API | P05-03; P05-04; P04-04 | stdin SQL, no shell, exitcode/timeout/log, error rõ, guard đích | Success/fail/timeout, secret redaction, partial import | Kiểm tra USE/CREATE DATABASE trong dump; BLOCKED bởi P05-03, P05-04, P04-04; mở khi dependency đạt |
| [!] P05-06 | scripts/restore.bat | P05-05 | Quote paths, target confirmation, ERRORLEVEL, thông báo đúng | Cancel/file missing/command fail/space path | Wrapper cùng service; BLOCKED bởi P05-05; mở khi dependency đạt |
| [!] P05-07 | Restore tests | P05-06 | Mock suite pass; success path thật trên DB disposable có xác nhận | Invalid file/permission/traversal/failure/safe target success | Tuyệt đối không production trong tests; BLOCKED bởi P05-06; mở khi dependency đạt |

## PHASE 6 — Seed Data

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P06-01 | Seed command architecture | P01-07; ADR-007 | manage.py seed_data, transaction, deterministic keys, env guard | Command discovery, failure rollback | Dự kiến apps.admin_portal/management/commands; BLOCKED bởi P01-07; mở khi dependency đạt |
| [!] P06-02 | Seed accounts | P06-01; P03-07 | ADMIN ACTIVE/CUSTOMER ACTIVE/LOCKED, hash đúng, demo-only | Login fixtures, no duplicate/hash plaintext | Không ghi đè account thật; BLOCKED bởi P06-01, P03-07; mở khi dependency đạt |
| [!] P06-03 | Seed customers | P06-02; EXT-01 | Profile đúng FK account/status và trường chuẩn | FK/status/date/length | Bao gồm dữ liệu phù hợp demo module khách hàng; BLOCKED bởi P06-02, EXT-01; mở khi dependency đạt |
| [!] P06-04 | Seed categories | P06-01; EXT-02 | Categories cầu lông ổn định theo unique key đã chốt | Count/idempotency/status | Không đoán enum chưa duyệt; BLOCKED bởi P06-01; mở khi dependency đạt |
| [!] P06-05 | Seed brands | P06-01; EXT-02 | Brands phục vụ sản phẩm demo | Count/idempotency/length | Không dùng dữ liệu riêng tư; BLOCKED bởi P06-01; mở khi dependency đạt |
| [!] P06-06 | Seed products | P06-04; P06-05 | Vợt/giày/phụ kiện demo, FK đúng, Decimal price | FK/price/status/idempotency | Theo models catalog; BLOCKED bởi P06-04, P06-05; mở khi dependency đạt |
| [!] P06-07 | Seed customer_preferences | P06-03 | Preference type/value hợp lệ, gắn đúng customer | FK/idempotency | Không thêm field từ docs cũ; BLOCKED bởi P06-03; mở khi dependency đạt |
| [!] P06-08 | Seed feedbacks | P06-03; P06-06; EXT-03 | Feedback theo rating/status duyệt, handler hợp lệ | FK/rating/handled_by/resolved_at | Bao phủ tình huống chưa/đã xử lý nếu enum hỗ trợ; BLOCKED bởi P06-03, P06-06, EXT-03; mở khi dependency đạt |
| [!] P06-09 | Seed surveys | P06-03; EXT-04 | Creator tồn tại, thời gian/status nhất quán | Creator FK/date ranges | Không giả định enum trạng thái; BLOCKED bởi P06-03, EXT-04; mở khi dependency đạt |
| [!] P06-10 | Seed survey_questions | P06-09 | Types/is_required/sort_order theo contract | FK/type/order | Text/option/rating nếu types đã chốt; BLOCKED bởi P06-09; mở khi dependency đạt |
| [!] P06-11 | Seed survey_options | P06-10 | Options đúng question, sort ổn định | Question FK/order/idempotency | Không gắn option sai type; BLOCKED bởi P06-10; mở khi dependency đạt |
| [!] P06-12 | Seed survey_recipients | P06-09; P06-03 | Survey/customer đúng, status/timestamps hợp lệ | FK và duplicate policy | Cần chốt một recipient/customer/survey hay khác; BLOCKED bởi P06-09, P06-03; mở khi dependency đạt |
| [!] P06-13 | Seed survey_responses | P06-12 | Recipient đúng, started/submitted/status nhất quán | FK/cardinality đã chốt | Không đoán mỗi recipient chỉ một response; BLOCKED bởi P06-12; mở khi dependency đạt |
| [!] P06-14 | Seed survey_answers | P06-11; P06-13 | Option/question/response cùng survey, text/rating đúng type | FK chéo/rating/required questions | Không chỉ kiểm tra ID tồn tại; BLOCKED bởi P06-11, P06-13; mở khi dependency đạt |
| [!] P06-15 | Idempotency/reset | P06-02..14 | Chạy lại không duplicate, reset chỉ demo, confirmation/rollback | Run twice, collision data thật, reset cancel/fail | Không flush DB nhóm; BLOCKED bởi P06-02, P06-03, P06-04, P06-05, P06-06, P06-07, P06-08, P06-09, P06-10, P06-11, P06-12, P06-13, P06-14; mở khi dependency đạt |
| [!] P06-16 | Seed validation/summary | P06-15 | Đủ 13 bảng + dữ liệu demo hữu ích, log count không credentials | Counts/FK/business validation/login | Ghi thống kê và cách tái tạo; BLOCKED bởi P06-15; mở khi dependency đạt |

## PHASE 7 — SQL Export

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P07-01 | Export command/script | P06-16; P04-09; ADR-003; ADR-007 | Dump demo DB sạch, utf8mb4, scope bảng kỹ thuật rõ, tái lập được | Mock failures + inspect args/output | Không dùng backup DB thật làm deliverable; BLOCKED bởi P06-16, P04-09; mở khi dependency đạt |
| [!] P07-02 | database/crm_db.sql | P07-01 | Structure + demo data, không secret/definer riêng/DB đích cố định | Schema columns/FK/count, scan secrets | File demo có chủ đích được commit; BLOCKED bởi P07-01; mở khi dependency đạt |
| [!] P07-03 | Import test vào DB rỗng | P07-02; P05-07 | Import thành công DB disposable khác tên, FK/tiếng Việt đúng | Real MySQL import, exitcode, counts | Có guard DB đích; không fake success; BLOCKED bởi P07-02, P05-07; mở khi dependency đạt |
| [!] P07-04 | SQL smoke test | P07-03 | App chạy/login/API mẫu, migration state hợp lệ | Demo login, account list, survey/feedback read | Ghi rõ migrate+seed khác luồng import dump; BLOCKED bởi P07-03; mở khi dependency đạt |

## PHASE 8 — Backend Hardening

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P08-01 | API tests/contract audit | P02-13; P03-07; P04-09; P05-07 | Status/envelope/method/pagination nhất quán, error sanitize | Accounts + backup/restore API suites | Kiểm cả wrong method và malformed JSON; BLOCKED bởi P02-13, P03-07, P04-09, P05-07; mở khi dependency đạt |
| [!] P08-02 | Permission audit | P08-01 | Mọi endpoint/action guard đúng, no escalation | Anonymous/CUSTOMER/LOCKED/ADMIN matrix | Kiểm session cũ và revoke quyền; BLOCKED bởi P08-01; mở khi dependency đạt |
| [!] P08-03 | Validation audit | P08-01; P06-16 | Email/password/enum/length/path/query/FK chéo có validation | Boundary/duplicate/invalid input tests | Không chỉ happy path; BLOCKED bởi P08-01, P06-16; mở khi dependency đạt |
| [!] P08-04 | Security audit | P08-02; P08-03 | Hash/CSRF/secrets/upload/path/subprocess/log đạt AGENTS | CSRF client tests, leak/traversal/injection tests | Không scan/in secret thật vào output; BLOCKED bởi P08-02, P08-03; mở khi dependency đạt |
| [!] P08-05 | Migration và English naming audit | ALN-11; P01-06; EXT-01..04; P07-04 | Models/fields/tables/columns/API/tests English; schema/dump/migration state nhất quán; legacy chỉ trong analysis/history/conversion | Fresh/upgrade DB, naming scan có review exceptions, dry-run/plan/SQL review | Không reset DB nhóm hoặc đổi tên cột FK ngoài schema; BLOCKED bởi ALN-11, P01-06, EXT-01, EXT-03, EXT-04, P07-04; mở khi dependency đạt |
| [!] P08-06 | Performance sanity | P08-01; P06-16 | Pagination bounded, query count hợp lý, không N+1 rõ ràng | Dataset demo lớn hơn một trang/query inspection | Không tối ưu quá mức, ghi số liệu; BLOCKED bởi P08-01, P06-16; mở khi dependency đạt |
| [!] P08-07 | Logging audit | P08-04; P05-07; P06-16 | Account/permission/reset/backup/restore/seed logs đủ, không secret | Capture success/failure logs | Restore log ngoài DB bị thay thế; BLOCKED bởi P08-04, P05-07, P06-16; mở khi dependency đạt |

## PHASE 9 — API Documentation

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P09-01 | Endpoint inventory | P08-01 | METHOD/URL/AUTH cho API thực tế, planned tách rõ | So sánh URLconf/views | Chọn docs path theo repo khi tạo; BLOCKED bởi P08-01; mở khi dependency đạt |
| [!] P09-02 | Payload/response docs | P09-01 | REQUEST/RESPONSE, field errors, filters/pagination rõ | Ví dụ theo contract tests | Không đưa password_hash vào response mẫu; BLOCKED bởi P09-01; mở khi dependency đạt |
| [!] P09-03 | Status/error matrix | P09-02 | ERRORS 400/401/403/404/405/409/500 theo thực tế | Error-case docs vs tests | Không giả định mọi endpoint cùng error set; BLOCKED bởi P09-02; mở khi dependency đạt |
| [!] P09-04 | Test accounts/demo access | P06-16; P09-01 | Demo roles/status/credentials được ghi đúng nơi, tách production | Đăng nhập từng fixture được phép | Không log mật khẩu vào evidence; BLOCKED bởi P06-16, P09-01; mở khi dependency đạt |
| [!] P09-05 | Usage examples/runbook | P09-02; P09-03; P09-04; P08-07 | EXAMPLE Windows, session/CSRF, backup/restore/SQL runbook | Chạy ví dụ trên demo/test | Ghi recovery và import workflows; BLOCKED bởi P09-02, P09-03, P09-04, P08-07; mở khi dependency đạt |

## PHASE 10 — Frontend/Admin UI (sau backend)

Gate: P08-01..07 và P09-01..05 liên quan hoàn tất. Dùng Django Templates + Bootstrap 5, không tự dựng SPA; backend vẫn là nơi quyết định quyền/validation.

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P10-01 | Account list/detail page | P09-05; P08-01..07 | Dùng API thật, pagination/empty state, không hash | ADMIN rendering + forbidden | Chưa có templates/static trong baseline; BLOCKED bởi P09-05, P08-01, P08-02, P08-03, P08-04, P08-05, P08-06, P08-07; mở khi dependency đạt |
| [!] P10-02 | Search/filter controls | P10-01 | q/role/status đồng bộ query/pagination | Kết hợp filters/no match/invalid query | Không search field legacy; BLOCKED bởi P10-01; mở khi dependency đạt |
| [!] P10-03 | Create/edit form | P10-01 | Frontend/backend validation, field errors, CSRF | Valid/duplicate/weak password/server error | Không thay API contract; BLOCKED bởi P10-01; mở khi dependency đạt |
| [!] P10-04 | Lock/unlock UI | P10-01; P10-10 | Hiện đúng status, confirm và refresh hợp lý | Success/403/409/session state | Guard luôn ở backend; BLOCKED bởi P10-01, P10-10; mở khi dependency đạt |
| [!] P10-05 | Reset password modal/form | P10-01; P10-10 | Theo flow duyệt, không hiện hash/log password | Weak/success/cancel/error | Không prefill password cũ; BLOCKED bởi P10-01, P10-10; mở khi dependency đạt |
| [!] P10-06 | Groups/permissions UI | P10-01; P03-07 | CRUD/assign/revoke đúng permission matrix | Missing rights/invalid assignment | Không thêm role DB qua form; BLOCKED bởi P10-01, P03-07; mở khi dependency đạt |
| [!] P10-07 | Backup UI | P10-01; P04-09 | Pending/success/error theo kết quả backend | Command failure/retry/success | Không báo success trước thời điểm thật; BLOCKED bởi P10-01, P04-09; mở khi dependency đạt |
| [!] P10-08 | Restore UI | P10-07; P05-07; P10-10 | Chọn file/ID hợp lệ, hiển thị target, confirm/cancel | Invalid file/cancel/403/failure | Demo trên DB disposable; BLOCKED bởi P10-07, P05-07, P10-10; mở khi dependency đạt |
| [!] P10-09 | Delete UI theo policy | P10-01; P02-09; P10-10 | Eligible/protected cases rõ, không xóa lịch sử ngầm | Confirm/cancel/conflict | Khác lock account; BLOCKED bởi P10-01, P02-09, P10-10; mở khi dependency đạt |
| [!] P10-10 | Confirmation dialogs | P10-01 | Target/action rõ, ngăn double submit, restore nêu DB/file | Confirm/cancel/repeated submit | UI không thay xác nhận/guard backend; BLOCKED bởi P10-01; mở khi dependency đạt |
| [!] P10-11 | Alerts | P10-03; P10-07 | Success/error/field message rõ, không stacktrace | Error mapping/readability | Tiếng Việt nhất quán; BLOCKED bởi P10-03, P10-07; mở khi dependency đạt |
| [!] P10-12 | Loading/error states và UI regression | P10-02..11 | Pending/empty/offline/server errors xử lý được | UI flows, basic responsive, CSRF | Lưu ảnh demo sau khi ổn định; BLOCKED bởi P10-02, P10-03, P10-04, P10-05, P10-06, P10-07, P10-08, P10-09, P10-10, P10-11; mở khi dependency đạt |

## PHASE 11 — Integration

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P11-01 | Customer integration | EXT-01; P02-13 | Account/profile/link/delete/status đúng policy | Account↔customer, customer DELETED | Không đồng nhất DELETED với LOCKED; BLOCKED bởi EXT-01, P02-13; mở khi dependency đạt |
| [!] P11-02 | Feedback handled_by | EXT-03; P11-01 | Handler trỏ accounts, history giữ sau lock/delete policy | Resolve feedback, locked/deleted actor policy | Phối hợp chủ feedback; BLOCKED bởi EXT-03, P11-01; mở khi dependency đạt |
| [!] P11-03 | Surveys created_by | EXT-04; P11-01 | Creator FK đúng, history và survey answers nhất quán | Creator lock/delete, survey flow | Phối hợp chủ surveys; BLOCKED bởi EXT-04, P11-01; mở khi dependency đạt |
| [!] P11-04 | Account status/login toàn hệ thống | P11-02; P11-03; P10-12 | Locked không login/thao tác protected ở mọi module | Session trước/sau lock/unlock/reset | Kiểm guard module đồng đội theo scope thống nhất; BLOCKED bởi P11-02, P11-03, P10-12; mở khi dependency đạt |
| [!] P11-05 | API/frontend contract integration | P11-04; P09-05 | UI gửi đúng payload/auth/CSRF, phản ánh errors | End-to-end ADMIN/CUSTOMER/LOCKED | Không sửa API tùy tiện để khớp UI; BLOCKED bởi P11-04, P09-05; mở khi dependency đạt |

## PHASE 12 — Full Regression

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P12-01 | All account flows | P11-05 | CRUD/search/filter/lock/unlock/reset không regression | Full account service/API/UI flows | Có delete protected cases; BLOCKED bởi P11-05; mở khi dependency đạt |
| [!] P12-02 | Auth regression | P12-01 | Login/logout/password/session/last_login đúng | Old/new passwords, expired/session after lock | Không lộ hash; BLOCKED bởi P12-01; mở khi dependency đạt |
| [!] P12-03 | Permission regression | P12-02 | Matrix role/group/permission pass | Anonymous/CUSTOMER/LOCKED/ADMIN/revoke | Direct API mọi method; BLOCKED bởi P12-02; mở khi dependency đạt |
| [!] P12-04 | Customers regression | P11-01; P12-03 | Customer module không bị phá bởi account changes | Chủ module suite + FK/status | Ghi phạm vi tests thực có; BLOCKED bởi P11-01, P12-03; mở khi dependency đạt |
| [!] P12-05 | Feedback regression | P11-02; P12-04 | Feedback/handler/history đúng | Feedback suite + account deletion integration | Không tự thay ownership module; BLOCKED bởi P11-02, P12-04; mở khi dependency đạt |
| [!] P12-06 | Surveys regression | P11-03; P12-04 | Creator/recipient/response/answer đúng | Survey suite + cross-FK invariants | Required/type/rating theo contract; BLOCKED bởi P11-03, P12-04; mở khi dependency đạt |
| [!] P12-07 | Backup regression | P04-09; P08-07 | Service/API/batch success/failure pass | Mock suite + demo dump | Windows paths; BLOCKED bởi P04-09, P08-07; mở khi dependency đạt |
| [!] P12-08 | Restore regression | P05-07; P12-07 | Guard/confirm/recovery/exitcode pass | Mock + disposable DB restore | Không restore production; BLOCKED bởi P05-07, P12-07; mở khi dependency đạt |
| [!] P12-09 | Seed regression | P06-16; P12-04..06 | Chạy lại/reset không mất dữ liệu ngoài demo | Two runs/reset guard/rollback | Count/FK validation; BLOCKED bởi P06-16, P12-04, P12-05, P12-06; mở khi dependency đạt |
| [!] P12-10 | SQL import/full suite | P07-04; P12-08; P12-09 | Dump mới nhất import được; full test suite pass | Empty DB import/smoke + manage.py test | Ghi revision, commands/results; BLOCKED bởi P07-04, P12-08, P12-09; mở khi dependency đạt |

## PHASE 13 — Demo Readiness

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P13-01 | Clean DB setup | P12-10 | DB demo riêng, charset/user/config đúng, không reset DB nhóm | Connection, target guard | Windows demo machine; BLOCKED bởi P12-10; mở khi dependency đạt |
| [!] P13-02 | Migrate | P13-01 | Migration plan được review/apply trên DB demo | showmigrations/check/schema | Ghi thời gian và revision; BLOCKED bởi P13-01; mở khi dependency đạt |
| [!] P13-03 | Seed | P13-02 | Đủ bộ demo, chạy lại an toàn | Count/login fixture smoke | Không password trong log; BLOCKED bởi P13-02; mở khi dependency đạt |
| [!] P13-04 | Login admin | P13-03 | Demo admin vào đúng trang/quyền | Login/logout | Có tài khoản CUSTOMER đối chứng; BLOCKED bởi P13-03; mở khi dependency đạt |
| [!] P13-05 | Account CRUD demo | P13-04 | List/detail/search/filter/create/edit/delete policy trình diễn được | Kịch bản success/validation/conflict | Không tạo dữ liệu ngẫu nhiên không kiểm soát; BLOCKED bởi P13-04; mở khi dependency đạt |
| [!] P13-06 | Lock/unlock/reset demo | P13-05 | Thấy rõ status/login/session/password behavior | Locked login fail, unlock pass, reset | Không khóa admin duy nhất; BLOCKED bởi P13-05; mở khi dependency đạt |
| [!] P13-07 | Permission demo | P13-06 | CUSTOMER bị từ chối API, group assign/revoke minh họa | Direct request + UI | Không chỉ ẩn button; BLOCKED bởi P13-06; mở khi dependency đạt |
| [!] P13-08 | Backup demo | P13-07 | File hợp lệ, thông báo/log đúng | API/batch success + failure demo an toàn | Không commit backup; BLOCKED bởi P13-07; mở khi dependency đạt |
| [!] P13-09 | Restore demo | P13-08 | Xác nhận target, restore DB demo được, app smoke pass | Guard/cancel/restore/smoke | Có recovery và DB riêng; BLOCKED bởi P13-08; mở khi dependency đạt |
| [!] P13-10 | SQL import demo | P13-09 | Import crm_db.sql vào DB rỗng khác, login được | Import counts/FK/API smoke | Không chạy migrate trùng schema mù quáng; BLOCKED bởi P13-09; mở khi dependency đạt |
| [!] P13-11 | Screenshots | P13-05..10 | Ảnh các flow/report không lộ credentials/PII thật | Review ảnh và tên file | Chụp khi UI hoàn thiện; BLOCKED bởi P13-05, P13-06, P13-07, P13-08, P13-09, P13-10; mở khi dependency đạt |
| [!] P13-12 | Documentation/report/demo script | P13-11; P09-05 | Hướng dẫn setup/API/DB/test/demo, sơ đồ và báo cáo khớp code | Người khác chạy lại theo tài liệu | Ghi limitations trung thực, không dùng tên bảng legacy; BLOCKED bởi P13-11, P09-05; mở khi dependency đạt |

## PHASE 14 — Finalization

| Status / ID | Task | Dependencies | Acceptance criteria | Test required | Notes |
| --- | --- | --- | --- | --- | --- |
| [!] P14-01 | Remove debug code | P13-12 | Không print secret/test bypass/dead debug trong sản phẩm | Diff review + relevant tests | Không xóa logging hữu ích; BLOCKED bởi P13-12; mở khi dependency đạt |
| [!] P14-02 | Verify .env not committed | P14-01 | .env/credential files không tracked; example an toàn | git ls-files/diff review | Nếu secret thật từng commit, báo xử lý/rotate, không âm thầm rewrite history; BLOCKED bởi P14-01; mở khi dependency đạt |
| [!] P14-03 | Verify backup files not committed | P14-02 | Backup/log tạm không tracked; chỉ demo SQL chủ đích | git check-ignore/ls-files | database/crm_db.sql là artifact demo; BLOCKED bởi P14-02; mở khi dependency đạt |
| [!] P14-04 | Verify test passwords demo-only | P14-03 | Không password production hard-code, fixtures/docs đúng phạm vi | Source/artifact review, demo login | Không in secret tìm thấy vào report; BLOCKED bởi P14-03; mở khi dependency đạt |
| [!] P14-05 | Final regression | P14-04; P12-10 | Tests/reimport/smoke pass ở revision cuối | Targeted sau cleanup + full regression phù hợp | Ghi evidence, không lặp vô ích khi không đổi gì; BLOCKED bởi P14-04, P12-10; mở khi dependency đạt |
| [!] P14-06 | Clean git status/handover | P14-05 | Changes được review/commit theo yêu cầu, không bỏ file người khác | git status/diff --check, docs/plan consistency | Không tự reset/clean để tạo trạng thái sạch; BLOCKED bởi P14-05; mở khi dependency đạt |
| [!] P14-07 | Tag/release nếu nhóm sử dụng | P14-06 | Version/report/artifacts trỏ đúng revision | Release checklist/manual smoke | Chỉ thực hiện khi nhóm yêu cầu; nếu không dùng ghi N/A kèm lý do; BLOCKED bởi P14-06; mở khi dependency đạt |

## Bug Log

Chỉ tạo entry thật khi có lỗi/evidence cụ thể; không coi mọi TODO là bug. Conflict C-07 hiện là phát hiện source, chưa có runtime reproduce. Dùng mẫu dưới đây, thay title/placeholders; không đánh DONE bug khi chưa xác minh fix.

```text
### BUG-001 — <title>

Status: [ ] TODO / [~] IN PROGRESS / [x] DONE / [!] BLOCKED
Severity: <critical/high/medium/low và tác động>
Detected: <YYYY-MM-DD, revision, môi trường>
Component: <app/API/service/DB/UI>

Reproduce:
1. <precondition, actor, DB demo/test>
2. <request/command/input đã sanitize>
3. <quan sát lỗi>

Expected:
<requirement/contract mong đợi>

Actual:
<error/response/traceback đã che secret>

Root cause:
<evidence file:line/function; tách giả thuyết chưa xác minh>

Fix:
<patch nhỏ, lý do, DB/API impact>

Files changed:
<paths>

Tests added/run:
<test cases, commands, kết quả thật hoặc blocker>

Regression result:
<scope, pass/fail/not run, evidence>

Notes:
<task/ADR liên quan, owner, follow-up, limitations>
```

## Technical Decision Log

Trạng thái ADR: ACCEPTED là đã có chỉ dẫn/quyết định; PROPOSED chưa được coi là yêu cầu chính thức. Sửa bằng entry bổ sung nếu cần đổi quyết định đã có, giữ lý do và ảnh hưởng.

### ADR-001 — Account schema / Legacy conflict

Status: ACCEPTED — theo yêu cầu chủ đồ án, 2026-09-28.

Decision: Use the official accounts schema defined in AGENTS.md. Toàn bộ 13 bảng trong đó là schema chính thức.

Reason: This is the schema agreed for current implementation.

Consequences: Legacy field names from old documents must not be introduced automatically. `tai_khoan`/`vai_tro` và role cũ là conflict cần migration có kiểm soát; ưu tiên schema không có nghĩa được phá dữ liệu ngay.

### ADR-002 — Django Auth mapping / Legacy Migration

Status: TARGET ACCEPTED theo ADR-008; migration strategy PROPOSED/BLOCKED cho đến ALN-02..04 có evidence và review.

Evidence — CURRENT STATE / LEGACY IMPLEMENTATION: settings dùng accounts.TaiKhoan; AbstractUser/0001_initial tạo schema khác chuẩn; chưa biết DB đã apply hay dữ liệu cần giữ. TARGET STATE: Account/accounts, official English fields, AUTH_USER_MODEL='accounts.Account' sau alignment.

Decision pending: Xác nhận DB nhóm đã migrate/có dữ liệu chưa; chọn safe migration strategy tới Account (model/table/columns/Auth), adapter English cho password/last_login/status, bảo toàn PK/hash/timestamps/profile/M2M/contenttypes. Map role legacy KHACH_HANG/QUAN_LY/NV_CSKH sang ADMIN/CUSTOMER hoặc Group/Permission phải được duyệt; không copy legacy enum vào Account.role, không tự nâng quyền.

Superseded proposal: Đề xuất trước đây giữ model label legacy làm target bị chủ đồ án bác bỏ trong correction. Không còn lựa chọn đó trong implementation plan; chỉ giữ legacy references cần thiết trong migration history/conversion.

Reason: Đổi AUTH_USER_MODEL hoặc thừa cột Auth ảnh hưởng migration graph/FK/contenttypes/session và schema chính thức.

Consequences: ALN-01..11 phải hoàn tất trước Account CRUD; cần migration mới/data migration được review, test fresh/upgrade và kế hoạch bảo toàn dữ liệu. Nếu replacement nguy hiểm, ghi BLOCKED, trình safe strategy, chờ approval trước destructive operations. Chưa cho phép xóa migration hoặc reset DB chung; tên target đã chốt không cần hỏi lại.

### ADR-003 — Ràng buộc schema và bảng kỹ thuật Django

Status: ACCEPTED cho bảng kỹ thuật Django và ADMIN-only gate (owner hardening, 2026-09-28); PROPOSED cho constraints và chiến lược quyền chi tiết.

Decision ACCEPTED: 13 bảng là business/domain schema. Django được phép có django_migrations, django_session, django_content_type, auth_permission, auth_group, M2M permission mappings và framework internals cần thiết. Không hỏi lại việc cho phép bảng kỹ thuật; không thêm BUSINESS/domain tables hoặc duplicate domain tables khi chưa có approval, không thêm cột ngoài schema accounts.

Decision pending: Chốt PK/auto increment, NULL/default/unique/index/FK/on_delete/cardinality, email identity/collation, enum/rating range chưa có trong spec với chủ module. Phạm vi dữ liệu dump kỹ thuật và implementation Groups/Permissions cần được thiết kế; đây không phải quyết định lại việc cho phép bảng kỹ thuật.

Policy bắt buộc: ACTIVE + ADMIN là cổng quản trị, CUSTOMER bị cấm dù có group. Đề xuất đánh giá Groups để gom quyền hành động. Cần quyết định ADMIN toàn quyền hay thêm permission chi tiết và cách xử lý superuser/admin site.

Reason: Model legacy có Groups/Permissions nhưng không có guard, còn schema chưa mô tả ràng buộc đầy đủ.

Consequences: Chưa chọn PermissionsMixin/AbstractBaseUser như giải pháp tự động; phải kiểm tra cột/bảng phát sinh, test permission matrix và xác định scope SQL export.

### ADR-004 — API convention backend-first

Status: PROPOSED cho contract; ACCEPTED cho việc chưa làm UI/không tự cài DRF.

Decision proposed: Django JSON views theo prefix /api/admin/, trailing slash, success/data và success/error envelope trong AGENTS.md; session + CSRF phù hợp định hướng Templates. Chốt HTTP status, page size, search/filter/order trước API đầu tiên.

Reason: requirements không có DRF; views và URLs hiện chưa có API nghiệp vụ để kế thừa. Django admin /admin/ hiện có không phải API quản trị đã hoàn thiện.

Consequences: Giữ nhẹ đồ án; URL/payload chỉ là candidate cho tới khi implement/review. Nếu nhóm có convention mới được duyệt, cập nhật tài liệu theo convention đó.

### ADR-005 — Delete, self-management và reset password

Status: ACCEPTED 2026-09-30 for P00-10 service policy; Account CRUD HTTP/UI contract remains a later task.

Decision: ACTIVE ADMIN is the Account management gate for list/detail/create/update/role/lock/unlock/reset/delete. Services enforce it for implemented mutations; future create/update and HTTP views must call the same guard. Self lock/delete are denied. At least one ACTIVE ADMIN is retained; role demotion, lock and delete serialize by locking all ACTIVE ADMIN rows in PK order and recheck actor membership. Hard delete is allowed only without customer, feedback handler, survey creator or Django admin log references; technical permission mappings may be removed with the Account. Reset uses an admin supplied new password at the service boundary, Django validators and `set_password()`, returns ID only; existing target sessions lose their password auth hash. No email or generated password workflow in this phase.

Reason: Official SQL has no Account soft-delete column. Live FK inspection on 2026-09-30 confirmed `customers.account_id` RESTRICT, `feedbacks.handled_by` SET NULL, `surveys.created_by` RESTRICT, `django_admin_log.user_id` NO ACTION, and technical M2M NO ACTION. Blocking feedback references preserves handler attribution despite SET NULL.

Consequences: No silent DELETE-to-lock conversion, business cascade, or password/hash response. P00-10 tests use disposable Django MySQL test DB; 21 Account tests pass (10 foundation plus 11 service tests). `check` passes with only existing staticfiles.W004; `makemigrations --check --dry-run` reports no changes. No live business rows were modified.

### ADR-006 — Backup/restore và log

Status: ACCEPTED cho mysqldump/mysql, Windows .bat, config không hard-code, ADMIN + xác nhận restore; PROPOSED cho chi tiết dưới đây.

Decision proposed: Service nhỏ trong apps.admin_portal, command chung cho wrapper/API; backup root database/backups đã ignore; logging ngoài DB, không thêm history table. Credentials qua option file giới hạn quyền/login-path; restore ưu tiên server backup ID tin cậy; DB test riêng, không cho dump trỏ DB thật bằng USE/CREATE DATABASE.

Reason: Chưa có service/history design; hạn chế command injection/path traversal, không giả định restore atomic.

Consequences: Chốt nguồn dump/upload, size/timeouts, pre-backup/recovery/maintenance; test mocks và integration disposable. Xác nhận file + DB đích cho mỗi restore thật.

### ADR-007 — Seed và SQL demo artifacts

Status: ACCEPTED cho seed_data, đủ 13 bảng, rerun an toàn và database/crm_db.sql import được; PROPOSED cho chi tiết implementation.

Decision proposed: Seed command trong apps.admin_portal, keys/demo fixtures ổn định, reset chỉ bộ demo với guard; SQL export từ DB demo sạch và được commit riêng với backup vận hành. Hash demo qua Django, không tài khoản/dữ liệu thật.

Reason: Toàn hệ thống cần demo tái lập, models các thành viên chưa có; xuất SQL trước schema ổn định sẽ sai contract.

Consequences: Chờ EXT-* và scope bảng kỹ thuật; ghi count/FK/smoke import/login/migration state, không đánh DONE khi chưa import kiểm chứng.

### ADR-008 — Mandatory English architecture and database name

Status: ACCEPTED cho English schema; phần tên database được quyết định mới 2026-09-29 thay thế.

Decision: All domain/database/backend/API/test identifiers use English based on the official schema. Required models: Account, Customer, Product, Category, Brand, CustomerPreference, Feedback, Survey, SurveyQuestion, SurveyOption, SurveyRecipient, SurveyResponse, SurveyAnswer. Tables/columns giữ đúng schema; Meta.db_table/db_column khai báo khi cần. Account.role chỉ ADMIN/CUSTOMER. Database `crm_db` theo quyết định chủ đồ án 2026-09-29, charset utf8mb4, collation utf8mb4_unicode_ci.

Reason: Current implementation/migration names are legacy evidence, not authority over the official English schema. Naming target là yêu cầu bắt buộc của chủ đồ án.

Consequences: Thay thế hoàn toàn source-of-truth order cũ và đề xuất giữ legacy model label trong ADR-002. New implementation không trộn English model với field Vietnamese; legacy names chỉ dùng để quote/detect/migrate/document code cũ. `accounts.Account` là auth target; cách chuyển phải giữ dữ liệu và chờ approval cho destructive steps. `database/crm_db.sql` là tên artifact hiện hành.

### ADR-009 — Official database name correction

Status: ACCEPTED — explicit project owner decision, 2026-09-29; supersedes only the earlier database-name choice, not the English business schema.

Decision: Official MySQL database is `crm_db`; `database/crm_db.sql` is the SQL artifact. Its existing `DROP DATABASE IF EXISTS crm_db` makes it unsafe to rerun against the initialized database. Use `crm_db` in config examples, scripts, backup/export naming, and future docs; historical evidence about a separate local `.db` file remains file evidence only. Owner reports MySQL Server and Workbench running and SQL initialization already executed; live schema/data/migration state still requires read-only verification.

### ADR-010 — SQL-owned Account foundation and removal of legacy auth

Status: ACCEPTED and IMPLEMENTED — explicit owner decision, 2026-09-29. Supersedes legacy conversion proposals in ADR-002 and the earlier migration-file preservation rule for the unapplied Account initial migration.

Decision: `Account` / `accounts` is the only supported Account implementation. Live `crm_db` had the exact SQL-owned `accounts` schema, zero rows in all 13 business tables, no legacy table, and no applied Django migrations before alignment. Replace the obsolete `accounts/0001_initial.py` with an Account state migration that validates an existing `accounts` table or creates the approved SQL table only in a fresh database. It creates Django technical group/permission M2M tables without adding Account business columns. No legacy compatibility, query, or data migration. Python `password`/`last_login` map via `db_column` to `password_hash`/`last_login_at`; ACTIVE ADMIN derives `is_staff`/`is_superuser`, LOCKED denies authentication, and Groups/Permissions remain available. Full backend API authorization remains Phase 3.

Consequence: The migration is deliberately non-atomic because MySQL cannot roll back DDL. The fresh disposable MySQL test path and existing live SQL table path both passed. No pre-migration backup was required by the rename/transform/remove rule because this alignment performed none of those actions and no business rows existed. Future migrations with data impact still need their own backup/recovery review.

## Verification Log

### V-001 — Source audit và kiểm tra môi trường, 2026-09-28

- Đã đọc cấu trúc tracked/hidden files, settings/URLs/entry points, toàn bộ models/views/tests/admin/app configs, accounts migration, requirements, .env.example, gitignore, README và Git history/status.
- `git status --short`: sạch trước tạo tài liệu; không thấy AGENTS.md/prompts.md/plans.md cũ trong repository hoặc AGENTS.md ở các thư mục cha đã kiểm tra.
- `python --version`: 3.12.7, resolve `E:\msys64\ucrt64\bin\python.exe`. `python -m pip show ...`: thiếu pip. `importlib.util.find_spec`: django/MySQLdb/dotenv đều không tìm thấy trong interpreter đó.
- `where.exe mysql`, `where.exe mysqldump`: không trên PATH. Chưa kiểm executable tại MYSQL_BIN hoặc MySQL server thực tế.
- Không cài dependency, không tạo .env, không chạy Django tests/check/migrate/seed/backup/restore/import. Chưa có runtime đủ và task hiện tại chỉ viết ba file.

### V-002 — Initial guidance files review (trước naming correction), 2026-09-28

- Deliverables: AGENTS.md chứa đủ schema 13 bảng/quy tắc; prompts.md chứa 30 templates; plans.md chứa 15 phases, task dependencies/acceptance/tests, conflicts, Bug Log và ADRs.
- Kiểm tra bằng script read-only: UTF-8/code fences/whitespace đạt; đủ 13 bảng và đúng thứ tự/tên field so với danh mục yêu cầu; đủ 30 prompts và 15 phases; 135 task có ID duy nhất, đủ 6 cột, các tham chiếu ID đầy đủ tồn tại; Bug Log đủ trường.
- `git status --short` chỉ có ba file mới được yêu cầu; `git diff --check` không báo lỗi trên tracked diff. File mới được kiểm tra riêng vì chưa stage; không commit/stage hoặc sửa feature code.
- Backend runtime tests: NOT RUN, lý do V-001; không liên quan đến việc xác nhận thay đổi tài liệu đã đủ phạm vi.

### V-003 — English naming correction review, 2026-09-28

- Đã đọc lại ba guidance files, legacy Account source/migration và auth/DB config; tách CURRENT STATE / LEGACY IMPLEMENTATION khỏi TARGET STATE. Không suy diễn các tên trong ban list thành code thực sự tồn tại.
- Document checks PASS: UTF-8/code fences/whitespace; đủ 13 model/table mappings; đủ Legacy Naming Ban; DB_NAME/DDL dùng crm_db; cả 30 prompt blocks chứa hai câu English naming bắt buộc; audit/FIX BUG có chỉ dẫn mới.
- Roadmap checks PASS: 15 phases, 146 tasks với 6 cột và ID duy nhất; 11 ALN tasks chưa đánh DONE; task references/ranges hợp lệ, dependency graph không có cycle; Account CRUD qua foundation có ALN-11 gate.
- So sánh SHA-256 các file ngoài .git trước/sau correction: chỉ AGENTS.md, prompts.md, plans.md thay đổi; không thêm/xóa file, không đổi badminton_crm_db.db, settings, .env.example, models hoặc migrations.
- Backend/migration tests NOT RUN: task chỉ sửa tài liệu; chưa kết nối/modify DB, chưa thực hiện alignment. V-001 ghi giới hạn runtime đã biết, không coi document checks là backend tests.

### V-004 — Final authentication/migration/database hardening, 2026-09-28

- Re-read ba tài liệu và source settings/auth model/migration/URLs/tests/dependencies; nhánh feature/admin-user-management. Chỉ sửa AGENTS.md, prompts.md, plans.md; không kết nối hoặc thay đổi DB, không triển khai backend.
- GATE-A..J đã ghi rõ: I DONE theo quyết định owner về bảng kỹ thuật, A–H/J BLOCKED do thiếu evidence/decision tương ứng. Task phụ thuộc được đánh BLOCKED theo graph; inventory/design độc lập vẫn được tiếp tục. ALN-12 yêu cầu backup verified trước migration rủi ro, không phụ thuộc service Phase 4.
- Document checks PASS: schema block chính thức giữ nguyên từng ký tự; đủ 13 bảng, 30 prompts, 15 phases; 157 task ID duy nhất, đủ 6 cột; references tồn tại và dependency graph không cycle. Code fences/whitespace/UTF-8 hợp lệ; legacy identifiers chỉ trong sections có nhãn Current State/Legacy/Migration/Conflict, không làm target recommendation.
- Scope check bằng SHA-256 trước/sau: chỉ ba file tài liệu thay đổi, không thêm/xóa file; badminton_crm_db.db, settings, .env.example, models và migrations giữ nguyên. Git diff --check không có lỗi; ba tài liệu vẫn untracked nên đã kiểm tra nội dung riêng, không chỉ dựa tracked diff.
- Backend/migration tests NOT RUN: task chỉ hardening tài liệu. Không có showmigrations/DB inspection/backup evidence mới; không đánh Account migration hoặc Phase 1 DONE.

### V-005 — Owner DB name correction and live runtime recheck, 2026-09-29

- Owner confirmed `crm_db` as official database and reported that MySQL/Workbench are running and the SQL initialization already executed. Current machine check independently found `MySQL80` Running, Workbench process running, and TCP 127.0.0.1:3306 open. This confirms server availability, **not** the schema or data in `crm_db`.
- Installed standard Windows CPython 3.12.10 x64; recreated only ignored `venv/` from its verified executable. The launcher still did not list it in this shell. Pinned `requirements.txt` installed completely with Windows wheels for mysqlclient 2.3.0 and Pillow 12.3.0; Django 5.2.17, `import MySQLdb`, `from PIL import Image`, and `pip check` passed. No dependency pins changed.
- `venv/Scripts/python manage.py check` passed with one existing `staticfiles.W004` warning because `static/` does not exist. No business source was changed to silence it.
- No `.env` or DB environment variables were available. MySQL root without password returned error 1045; `showmigrations accounts` and `migrate --plan` also returned 1045 for the OS-default user with no password. No applied migration state was obtained. A read-only inspection of Workbench connection metadata showed a local root connection but supplied no password; no credential was printed or copied. The MySQL login-path listing was empty.
- Repository already contained `database/crm_db.sql`; the old SQL filename was absent, so no rename was performed. The SQL file contains `DROP DATABASE IF EXISTS crm_db`, `CREATE DATABASE crm_db`, `USE crm_db`, all 13 `CREATE TABLE` statements, and an eight-column `accounts` definition with email UNIQUE and role/status CHECK clauses. This is **file evidence only**: `SHOW DATABASES`, `SHOW TABLES`, live `DESCRIBE accounts`, counts, and `django_migrations` remain unverified. The SQL file was not executed.
- Current classification under the four-state scheme: **STATE D — verification still impossible because valid local MySQL credentials are unavailable**. The prior stopped-service and missing-Python findings are historical and superseded. `crm_db` could be A, B, or C only after live read-only checks; no Account implementation or migration is authorized from this evidence.

### V-006 — Account Foundation implementation and live alignment, 2026-09-29

- Read-only `crm_db` inspection before changes: exactly 13 official business tables; all 13 counts were zero. `accounts` had eight official columns, primary/unique indexes and role/status CHECK constraints. No legacy table or `django_migrations`. `showmigrations accounts` showed old 0001 unapplied; `migrate --plan` would have created the obsolete model. FK references to `accounts` were found from customers.account_id, feedbacks.handled_by and surveys.created_by.
- Owner-authorized source changes: `apps/accounts/models.py` now defines Account only; manager/constants use English role/status names; Django framework `password`/`last_login` fields map to official SQL columns. `config/settings.py` selects `accounts.Account`. Active `apps/` and `config/` Python source contains no removed legacy model/table reference.
- Replaced the unapplied Account initial migration with state/database separation and a schema guard. Fresh test DB creates the exact official Account SQL table; an existing table is validated and kept. Technical M2M tables are created separately. First disposable test run exposed MySQL DDL-in-transaction error; setting migration `atomic=False` fixed the root cause. No business SQL initialization, DROP, fake migration, or legacy data conversion occurred.
- Targeted MySQL suite: `venv/Scripts/python.exe manage.py test apps.accounts --keepdb --noinput` passed 10/10 tests. Cases cover CUSTOMER/ADMIN creation, normalized/duplicate email, Django hashing/check_password, direct raw-password save rejection, invalid role/status, ACTIVE/LOCKED, locked login and existing session, last_login_at, permissions/group mapping, and exact physical columns. `manage.py check` and `makemigrations --check --dry-run` pass, with only the existing missing-static-directory warning.
- After review, `manage.py migrate --noinput` applied Django technical migrations and Account 0001 on live `crm_db`. Post-check: `accounts/0001_initial` marked applied; `migrate --plan` has no operations; official eight Account columns and zero account rows remain; `accounts_groups` and `accounts_user_permissions` exist; no legacy or `auth_user` table. No Account CRUD or UI was implemented.

## Historical previous next-task notes (superseded by V-006)

### Phase 1 Account Foundation attempt — 2026-09-29

**Status: [!] BLOCKED.** No Account/Auth model, setting, migration, or test was changed. This pass inspected only the relevant source and preserved all existing uncommitted files. The committed `apps/accounts/migrations/0001_initial.py` creates the legacy user model and table; `config/settings.py` still selects that model. The migration file exists in Git, but its applied state, the real database schema/data, and database ownership are unknown. This is a migration safety blocker for changing `AUTH_USER_MODEL` or replacing the model, independent of whether Customer/Product/Feedback/Survey exist.

Runtime evidence: no project `.env` or local venv was found. `python` resolves to MSYS2 Python 3.12.7 without Django; `py -0p` found no registered interpreter. `python manage.py showmigrations accounts` and `python manage.py migrate --plan` both stopped at `ModuleNotFoundError: No module named 'django'`. No database command, migration, test, or backup was run; no test result is claimed. The current untracked `badminton_crm_db.db` remains untouched and is not evidence of the MySQL state.

**GATE-C design proposal for review before implementation:** use `AbstractBaseUser` with only the official eight Account columns. Persist the Django encoded password in `password_hash` and last login in `last_login_at`; provide Django's `password` and `last_login` accessors as tested adapters so inherited `set_password()`, `check_password()`, session hash handling, and `update_last_login` use the official columns without extra columns. Verify Django model field inheritance and save/update behavior in a disposable runtime before accepting this mapping. Use email as `USERNAME_FIELD`, a custom manager, Django password hashers and validators, and one trim/case normalization policy enforced with a database unique constraint after existing emails are inventoried. `status=ACTIVE` supplies `is_active`; `status=LOCKED` must fail new login and protected requests from existing sessions through the selected auth backend. Do not treat this proposal as an approved data migration or claim it is already tested.

**GATE-G design proposal:** Django Groups and Permissions may use technical M2M tables. If `PermissionsMixin` is used, its default persisted `is_superuser` field must be replaced by an explicit non-column policy; `is_staff` can derive from active ADMIN. ADMIN authorization still needs the agreed role-and-permission policy before CRUD. `create_superuser`, admin site access, group/direct permissions, and CUSTOMER denial need tests. No ADMIN bypass or legacy flag mapping is approved here.

Next evidence needed for ALN-02/03/04 and P01-01..07: identify the correct Windows Python/venv and a separate MySQL dev/test database; inspect applied migrations, tables, row counts, actual FK/M2M relations and duplicate emails without printing secrets; confirm database ownership and data preservation scope. Then review a fresh-install and legacy-upgrade migration strategy, including role/profile disposition, password hashes, IDs, contenttypes, permissions, sessions and verified backup before any data-changing migration. Only after this evidence can a new Account migration and targeted MySQL tests be safely created. Future FK contracts remain `customers.account_id`, `feedbacks.handled_by`, and `surveys.created_by` pointing to `accounts.account_id`; teammates' models are outside this phase.

### P00-08 runtime and migration-state verification — 2026-09-29

Historical snapshot before V-005; its MSYS2, stopped-service, and earlier classification findings are superseded by the later Windows CPython and running-MySQL check.

**Classification: STATE C — CANNOT VERIFY.** A repository-local ignored `venv/` was created from MSYS2 Python 3.12.7 (`venv/bin`, not Windows `venv/Scripts`); pip 26.2.1 and the pinned Django 5.2.17, asgiref, python-dotenv, sqlparse, and tzdata were installed. The complete `requirements.txt` install failed: this interpreter used source builds for pinned `mysqlclient==2.3.0` and `pillow==12.3.0`; native build dependencies were unavailable (Pillow reports missing zlib). No package version was changed in requirements. `venv/bin/python -m django --version` returned 5.2.17. `manage.py check`, `showmigrations`, and `migrate --plan` were each attempted and stopped during setup with `ModuleNotFoundError: No module named 'MySQLdb'` / `ImproperlyConfigured: Error loading MySQLdb module`. They yielded no applied-migration evidence.

Source-only migration graph inspection used an in-process SQLite memory setting solely to load migration files; it did not open or modify any project database. It found only `accounts/0001_initial`, committed in `d8a2f2a`, depending on `auth/0012_alter_user_first_name_max_length`; Django admin `0001_initial` has a swappable user dependency resolving to `accounts/__first__` under the current `AUTH_USER_MODEL='accounts.TaiKhoan'`. This confirms graph membership, **not** applied state. Current legacy `AbstractUser` uses Django's encoded `password` field (VARCHAR(128)); any eventual conversion must copy valid encoded values to `accounts.password_hash` without rehashing or exposing them.

No local `.env` or DB_* / SECRET_KEY process variables exist. MySQL CLI 8.0.45 was found under `C:\Program Files\MySQL\MySQL Server 8.0\bin`, but Windows service `MySQL80` is stopped and TCP 127.0.0.1:3306 is closed. Consequently no `SHOW TABLES`, `DESCRIBE`, row counts, applied migrations, account hashes, actual FKs, ownership or shared/disposable status could be verified. **Tables found: unknown; account data: unknown.** Do not infer fresh/disposable from the stopped service or from the separate untracked `.db` file.

`.env.example` was aligned to `DB_NAME=crm_db`, the installed MySQL 8.0 CLI path, and a noncredential password placeholder. No real `.env`, database, model, migration, auth setting, AGENTS.md or prompts.md was changed. C-10 and the example credential issue in C-08 are resolved; C-05/06 and GATE-A/B remain blocked. P00-08 is partial, P00-09 remains blocked, and ALN-01 source inspection is done. No Account Foundation or CRUD task is done.

Migration strategy remains conditional on real evidence. If the selected DB is confirmed fresh, local, disposable and unapplied, review the shared-history impact before replacing the initial auth graph and testing a clean install on a separate MySQL test DB. If migration/data already exist, inventory IDs, valid password hashes, duplicate emails, legacy roles/profile fields, all business and technical FKs/M2M, sessions and content types; obtain owner decisions for role/profile/archive mapping; create and verify a backup on a disposable restore target before a staged, data-preserving migration rehearsal. Do not rename, drop, reset, fake migrations, or switch `AUTH_USER_MODEL` until that strategy is reviewed. The future Account target remains `accounts.Account` / `accounts` with exactly the official eight fields.

**Exact next task after V-005: finish P00-08 credential/test-DB setup, then execute P00-09 read-only.** The owner should place working MySQL credentials in ignored local `.env` with `DB_NAME=crm_db` and identify whether the live DB is shared or disposable, without sending the password in chat. Run `showmigrations`, `migrate --plan`, `SHOW DATABASES`, `SHOW TABLES`, `DESCRIBE accounts`, index/check inspection and safe counts. Compare all 13 live tables and `django_migrations` to the SQL file and Django source, then classify STATE A/B/C. Do not run SQL initialization, `migrate`, reset or Account implementation.

Account implementation **chưa thể bắt đầu an toàn**: GATE-A..H/J còn BLOCKED, ALN-12 chưa có backup evidence. Có thể tiếp tục inspection/design proposals; không chờ hỏi lại naming hoặc bảng kỹ thuật.

## Những quyết định cần xác nhận trước code ảnh hưởng lớn

Naming Account/accounts và database crm_db đã được chủ đồ án xác nhận, không hỏi lại việc giữ legacy naming làm target. Các quyết định còn mở:

1. Account DB/migration state đã xác minh và align theo V-006; không còn legacy data hoặc migration conversion decision.
2. Account email policy: trim và lowercase, unique ở DB và model; role/status theo SQL. NULL/FK/on_delete/cardinality và enum của các module khác vẫn do chủ module chốt. (ADR-003.)
3. ACTIVE ADMIN có framework superuser permission theo ADR-010. P00-10 đã chốt hard-delete, self/last ADMIN, reset service và Account action gate; HTTP request/response/CSRF contract thuộc Account CRUD backend tiếp theo. (GATE-H/J, ADR-005.)

API envelope/URL và vị trí service là đề xuất triển khai có thể review trong feature plan; không cần trì hoãn toàn bộ khảo sát chỉ vì các chi tiết này. Restore thực tế vẫn cần xác nhận đúng DB/file mỗi lần theo AGENTS.md.

PHASE — TEAM INTEGRATION

[ ] Integrate Account with Customer
[ ] Verify feedbacks.handled_by
[ ] Verify surveys.created_by
[ ] Reconcile shared settings.py
[ ] Reconcile AUTH_USER_MODEL
[ ] Reconcile URLs
[ ] Reconcile migrations
[ ] Run full-project migrations
[ ] Run regression tests after merge

## Exact next task — after Account CRUD Backend

**ACCOUNT ADMIN UI:** build the project Account management presentation on top of the tested `/admin-portal/accounts/` HTML backend, including consistent layout, confirmation for destructive actions, accessible messages and responsive styling. Do not bypass service rules. The `accounts:login` route referenced by `LOGIN_URL` remains unresolved; backend currently returns 403 for anonymous users and test clients authenticate directly. Do not invent a login route in this phase.

### P00-10 interrupted-run recovery — 2026-09-30

Before recovery, untracked `apps/accounts/errors.py`, `permissions.py`, `selectors.py`, and `services.py` already contained the initial guard, selectors, exceptions, and mutation functions; no P00-10 tests or plan update existed. Existing Account foundation changes and other owners' uncommitted files were preserved. Recovery corrected selector output naming, stale mutation results, ORM protection handling, actor revalidation after locks, and admin-log history protection; added focused service/FK tests and documented the contract. Test DB only: 21 Account tests pass. Read-only live FK inventory was performed; no live data change. `python manage.py check` succeeds with existing `staticfiles.W004`; `python manage.py makemigrations --check --dry-run` reports `No changes detected`. No business schema change or legacy technical identifier was introduced.

### ACCOUNT CRUD BACKEND evidence — 2026-09-30

Added `apps/accounts/forms.py`, `urls_admin.py`, HTML views in `views.py`, minimal `templates/accounts/admin/` pages, and `/admin-portal/` inclusion. Added `create_account` and `update_account_email` services; all role/status/reset/delete actions continue through P00-10 services. `AccountUpdateForm` edits email only, so role/status cannot bypass protected transitions. `list_account_page` selects only safe fields, orders by descending `account_id`, paginates 20 per page, and filters validated role/status. Named namespace is `accounts_admin`; mutations are POST-only with Django CSRF middleware and messages. Empty POST submissions are bound and validated. Anonymous, CUSTOMER, and LOCKED ADMIN access returns 403 because `accounts:login` has no route yet. All 35 Account tests pass on disposable Django MySQL test DB, including foundation, P00-10, and HTML view/CSRF/FK tests. `python manage.py check` succeeds with only existing `staticfiles.W004`; `python manage.py makemigrations --check --dry-run` reports `No changes detected`. No live business data, Account schema, or canonical SQL was changed. The earlier Phase 2 JSON API proposal is not implemented by this HTML backend task.
### Supplier and survey uniqueness extension — 2026-09-30

- CURRENT: canonical `database/crm_db.sql` had 13 business tables; catalog/customers/surveys Django apps were scaffolds; no supplier, recipient uniqueness or one-response constraint. TARGET: owner explicitly requests the fourteenth business table `suppliers`, required `products.supplier_id`, and named survey uniqueness constraints. This owner decision supersedes the earlier 13-table limit for this extension.
- FK contract: `products.supplier_id -> suppliers.supplier_id` is required, ON UPDATE CASCADE and ON DELETE RESTRICT; Django uses PROTECT. `survey_recipients` is unique by survey/customer; `survey_responses.recipient_id` is unique and exposed as OneToOne. Existing IDs and answers must be preserved.
- Read-only live inspection after MySQL became reachable: `products` has 0 rows; both duplicate GROUP BY queries returned 0 rows; supplier table does not exist; no catalog/customers/surveys migrations are applied. No `migrate` or SQL initialization was run on `crm_db`. Catalog migration raises with product IDs when future existing products need an explicit supplier assignment. Survey migration raises with duplicate recipient/response IDs before adding constraints. Resolve any future conflicts and verify a backup before a migration on populated/shared data.
- New migrations are SQL-owned alignment migrations: missing domain tables are created; existing SQL tables are retained. `manage.py check`, `makemigrations --check --dry-run`, template parse, and all 42 Django MySQL tests pass on a disposable test DB. `migrate --plan` lists only catalog/customers/surveys initial migrations. Live migration remains pending under the repository rule against running it automatically.
### INT identifier migration — owner decision 2026-09-30

- TARGET: all 14 business primary keys and their FKs are signed INT; models use AutoField, settings and app defaults use AutoField. Preserve suppliers and survey uniqueness. The earlier 13-table/BIGINT schema block is historical for ID types.
- LIVE READ-ONLY INVENTORY before change: `crm_db` has one Account row (ID 1), one Django session, 19 applied migrations, 24 auth permissions, six content types, and zero rows in the other 12 existing business tables. `suppliers` is absent. `accounts/0001_initial` is applied; catalog/customers/surveys initial migrations are unapplied. Actual BIGINT columns include all legacy domain IDs plus Account technical references (`accounts_groups`, `accounts_user_permissions`, `django_admin_log`), and technical `id` columns (`auth_group_permissions`, `django_migrations`). All 22 existing tables use InnoDB. No database reset is authorized.
- IMPLEMENTATION: keep applied Account 0001 as history; update only unapplied catalog/customers/surveys 0001 migrations to INT; add Account 0002 with range/column/FK preflight, preserve all discovered FK names and ON UPDATE/DELETE rules, convert signed columns, restore FKs and verify. MySQL DDL is nontransactional; a partial failure requires recovery from the verified backup. Fresh MySQL test DB: 44/44 tests pass; physical schema has zero BIGINT columns. `manage.py check`, `makemigrations --check --dry-run`, and `migrate --plan` pass.
- BACKUP: full structure/data dump from `crm_db`, 22 tables, created at 2026-09-30 14:53 UTC with `mysqldump --single-transaction`; file `database/backups/crm_db_20260930_145315_912ca611.sql`, size 32415 bytes, SHA-256 `d84cc45f254bc50753881955be1e970c871b5034f26da65ba8c8b6570e8b28bd`. File is ignored by Git. Restore verification on `crm_db_import_test` requires the exact file/target confirmation under Restore Rules; until verified, live migration is [!] BLOCKED. `crm_db` has not been migrated or seeded.
### Read-only reconciliation after Workbench INT conversion — 2026-09-30

- CURRENT LIVE `crm_db`: 14 business tables only; all 14 business PKs and 17 business FKs are signed `INT`, PKs remain `AUTO_INCREMENT`. `suppliers`, `products.supplier_id` with CASCADE/RESTRICT FK and index, and both named survey UNIQUE constraints are present. All 14 business tables have zero rows. There are no BIGINT columns in the live schema.
- MIGRATION STATE: `django_migrations` is absent, so `showmigrations` reports every Django migration unapplied. All technical tables are absent, including `accounts_groups`, `accounts_user_permissions`, `auth_group_permissions`, `django_admin_log`, `django_migrations`, `auth_group`, `auth_permission`, `django_content_type`, and `django_session`.
- TARGET/CONFLICT: `accounts/0002_int_identifiers.py` requires `accounts_groups.id/account_id`, `accounts_user_permissions.id/account_id`, `auth_group_permissions.id`, and `django_migrations.id`; all six columns are absent. `accounts/0001_initial.py` expects an existing BIGINT `accounts.account_id`, but the live column is INT. Business schema matches the final INT target, while the complete Django migration state/schema does not. **[!] BLOCKED:** do not run 0002, normal `migrate`, or `--fake` until a reviewed technical-table/history reconciliation path exists. Faking 0002 alone would leave its dependencies and technical tables unresolved.
- READ-ONLY CHECKS: `SHOW CREATE TABLE` for six requested tables, INFORMATION_SCHEMA columns/FKs/rules/constraints/indexes, exact business row counts and migration plan. `manage.py check` and `makemigrations --check --dry-run` pass. `manage.py test --keepdb --noinput` passes 44/44 on separate `test_crm_db` and preserves that test database. No DROP, restore, seed, ALTER, migrate, or fake ran on `crm_db` during this reconciliation.

### Rebuild from migrations rehearsal — owner decision 2026-09-30

- Owner abandoned live migration-state reconciliation and authorized a clean rebuild after final backup, rehearsal, restore verification, and Restore Rules confirmation. No `--fake` is permitted.
- Final pre-rebuild backup: `database/backups/crm_db_20260930_153739_2228dc57.sql`, 14 InnoDB business tables, 0 rows in each, SHA-256 `6a6e604487e571f18c705a9016d95e9c258befedb2d340f37cfc22339807d172`. Live `crm_db` remains unchanged as of this note.
- Initial rehearsal exposed missing `customer_preferences`, `feedbacks`, customer unique name, and survey indexes. Added the two model/migration definitions and aligned unapplied catalog/customer/survey migrations to canonical SQL. Final clean rehearsal on `crm_db_rebuild_test_v3`: 25 migrations applied without fake, 14 signed INT auto-increment PKs, 17 signed INT FKs, 9 technical tables, supplier FK CASCADE/RESTRICT, named survey UNIQUE keys and indexes. `check` and 44/44 tests pass; `seed_data` fills all 14 business tables and is repeatable.
- [!] BLOCKED pending explicit Restore Rules confirmation of exact backup file and disposable `crm_db_backup_verify` destination for backup restore proof. A separate exact-target confirmation is required immediately before destructive live `crm_db` replacement. Export/restore validation of the new SQL dump follows only after live rebuild succeeds.

### Final clean database build — owner authorization 2026-10-01

- Owner explicitly authorized deletion of the old project migrations, DROP/recreate of development `crm_db`, fresh migrations, seed, SQL overwrite, and disposable restore testing. The prior reconciliation/restore blocker is superseded; the previous 14-table, zero-row backup remains available at the recorded SHA-256.
- Removed the old project migration chain and retained each `migrations/__init__.py`. Generated fresh `accounts`, `catalog`, `customers`, `feedback`, and `surveys` `0001_initial.py` migrations with signed `INT` IDs from the start. `surveys/0002_schema_contract.py` applies MySQL-specific FK update/delete rules, index/check names, and original DATETIME/TEXT physical types after Django's deferred initial FKs exist. There is no BIGINT-to-INT migration and no fake migration.
- Clean rehearsal `crm_db_newchain_v3` passed all 24 migrations, schema audit, seed and 44 tests. Recreated development `crm_db` only after verifying the final backup hash and zero rows in all 14 old business tables. Live `crm_db` now has 14 business tables, nine technical tables, 14 signed INT auto-increment PKs, 17 signed INT FKs, canonical supplier and survey constraints, and all 24 migrations applied.
- `seed_data` populates all 14 business tables. Live `check` passed; 44/44 tests passed on a freshly recreated disposable `test_crm_db`. `database/crm_db.sql` is a full `mysqldump` including schema, technical tables, migration history and demo data; SHA-256 `118c3a75ec724ab696b812efb93b8e3c7a309c3ed4d1b023cbe1eb5dd89d8f98`, 40215 bytes. Imported without migrations into `crm_db_dump_verify`; physical schema, row counts, migration state, demo login and ORM reads all passed.

### Account JSON API and Swagger — 2026-10-01

- **RESTORE TEST: PASS** (owner confirmed). No backup/restore retest was run in this phase. **RESTORE REGRESSION: NOT TOUCHED**: `scripts/restore.bat`, `scripts/backup.bat`, and `database/crm_db.sql` were not edited. The canonical SQL SHA-256 remains `118c3a75ec724ab696b812efb93b8e3c7a309c3ed4d1b023cbe1eb5dd89d8f98`.
- Read-only live `crm_db` verification: `SHOW TABLES` returned 14 business and 9 Django technical tables, including `suppliers`; `DESCRIBE accounts` and `SHOW CREATE TABLE accounts` match the current canonical SQL; `SELECT COUNT(*) FROM accounts` returned 2. The Account columns are `account_id INT AUTO_INCREMENT PRIMARY KEY`, `email VARCHAR(255)`, `password_hash VARCHAR(255)`, `role VARCHAR(20)`, `status VARCHAR(20)`, `last_login_at DATETIME`, `created_at DATETIME`, and `updated_at DATETIME`. Live checks allow only ADMIN/CUSTOMER roles and ACTIVE/LOCKED statuses. Django `Account` uses `AutoField` and maps password/last_login to the canonical physical names; fresh `accounts/0001_initial.py` agrees. No INT/BIGINT mismatch or business migration was found.
- Django Ninja **1.7.1** was already installed in the active venv and already pinned exactly as `django-ninja==1.7.1` in `requirements.txt`; no dependency edit was needed. `config/api.py` exposes one `NinjaAPI` at `/api/`; `apps/accounts/api.py` registers the Account router. Swagger: `http://127.0.0.1:8000/api/docs`; OpenAPI: `http://127.0.0.1:8000/api/openapi.json`. Ninja is in `INSTALLED_APPS` so Swagger assets are served locally.
- Historical API routes at this phase: GET/POST `/api/accounts/`; GET/PATCH/DELETE `/api/accounts/{account_id}`; POST `/api/accounts/{account_id}/role`, `/lock`, `/unlock`, and `/reset-password`. The PATCH route was removed by the later immutable-email decision below. Session authentication uses Django's existing login cookie. Every handler uses the P00-10 `require_active_admin` guard; mutations call the existing Account services and reads call selectors. SessionAuth runs Ninja's CSRF check. Ninja's Swagger page sets the CSRF cookie and automatically sends `X-CSRFToken` on Try it out requests. No CSRF exemption was added.
- Historical input schemas at this phase included create (`email`, `role`, `status`, `password`, `password_confirm`), update (`email`), role (`role`), and reset (`new_password`, `new_password_confirm`). The update schema was removed by the later immutable-email decision below. Form/service validation enforces email format/normalization, role/status choices, duplicates, matching passwords, and Django password policy. AccountOutput contains only `account_id`, `email`, `role`, `status`, `last_login_at`, `created_at`, `updated_at`. List is ordered by descending Account ID, filtered by role/status, and paginated (default 20, maximum 100). Errors use JSON `detail`: 400 invalid input, 401 no session, 403 non-admin/locked, 404 missing Account, 409 business state conflicts. Validation errors omit submitted values and unknown field names to avoid credential leakage.
- Regression: 9 focused API test methods cover the requested authorization, CRUD, business rules, FK-safe delete, password reset, response secrecy, route schema, and CSRF cases. All **46 Account tests passed** on the separate existing disposable `test_crm_db` with `--keepdb --noinput`; `manage.py check` reports 0 issues; `makemigrations --check --dry-run` reports `No changes detected`. Live `crm_db` received only read-only queries.

#### Manual Swagger workflow

1. Activate `venv` and run `python manage.py runserver`.
2. Open `http://127.0.0.1:8000/api/docs`; use the API login sequence below. The existing `/admin/login/` remains available separately.
3. After login, execute GET `/api/auth/me`, then GET `/api/accounts/`.
4. Test mutations with Try it out. The Swagger script reads the current CSRF cookie before every request, including after Django rotates it during login. Do not paste session cookies or passwords into an Authorization field.
5. Example create CUSTOMER: `{"email":"customer01@test.local","role":"CUSTOMER","status":"ACTIVE","password":"Customer@123456","password_confirm":"Customer@123456"}`. Example create second ADMIN: `{"email":"admin02@test.local","role":"ADMIN","status":"ACTIVE","password":"Admin02@123456","password_confirm":"Admin02@123456"}`.
6. Role: `{"role":"admin"}`. Reset password: `{"new_password":"NewPassword@123456","new_password_confirm":"NewPassword@123456"}`. Invalid create test: `{"email":"invalid-email","role":"INVALID","status":"INVALID","password":"123","password_confirm":"456"}`. Email PATCH was removed by the later immutable-email decision below.

**Exact next task: ACCOUNT ADMIN UI.** Build the presentation on top of the tested Account backend without changing the Account API or bypassing services.

### Swagger session login follow-up — 2026-10-01

- Root cause of reported 401: the previous Swagger/curl request supplied `X-CSRFToken` but did not establish a valid Django `sessionid` cookie. CSRF proves request origin, not user identity. Existing `NinjaAPI(auth=SessionAuth())` reads `request.user` from Django's SessionMiddleware and AuthenticationMiddleware; the Account router uses the same user in `require_active_admin`. The default `ModelBackend` uses `Account.email` as USERNAME_FIELD and rejects LOCKED accounts through `is_active`. No evidence of a router/backend mismatch was found. Host-only cookies can also disappear when switching between `localhost` and `127.0.0.1`; use one hostname consistently.
- Added `apps/accounts/api_auth.py` under the existing Ninja API: public GET `/api/auth/csrf` issues a Django CSRF token/cookie; public POST `/api/auth/login` validates CSRF, normalizes email, calls Django `authenticate(request, email=..., password=...)` and `login()`, then returns safe Account fields. GET `/api/auth/me` and POST `/api/auth/logout` require Ninja SessionAuth; logout uses Django `logout()` and remains CSRF protected. Login accepts ACTIVE ADMIN or CUSTOMER; Account management still requires ACTIVE ADMIN via the existing permission guard. Bad credentials and LOCKED accounts receive the same 401 response.
- The local Swagger template and `static/accounts/swagger-session-init.js` read the latest CSRF cookie for every request. Django rotates that cookie at login, so a single open Swagger page can continue through mutations and logout. No CSRF exemption, JWT, API key, auth schema column, or alternate user model was introduced. Login JSON never contains a session ID, password or hash; the browser receives Django's normal session cookie.
- Six focused auth API tests cover ADMIN/CUSTOMER login, invalid/unknown/LOCKED login, session creation, `/me`, logout, CSRF, safe output, Account permission integration, and OpenAPI routes. The test client verifies a single cookie session across login → `/me` → Account list → logout; a real browser walkthrough with a local development password remains a manual owner check. Full Account regression: **52/52 tests passed** on separate disposable `test_crm_db` with `--keepdb --noinput`, including Account foundation, P00-10, CRUD, existing API and new auth API tests. `manage.py check` reports 0 issues; `makemigrations --check --dry-run` reports `No changes detected`. No business migration or live database change was made.

#### Exact Swagger authentication workflow

1. Activate `venv`, run `python manage.py runserver`, and open `http://127.0.0.1:8000/api/docs`.
2. Execute GET `/api/auth/csrf` to establish/refresh the CSRF cookie.
3. Execute POST `/api/auth/login` with `{"email":"admin@test.local","password":"<local development password>"}` using an existing ACTIVE ADMIN Account. Use the actual local credentials; do not store them in source.
4. Execute GET `/api/auth/me`: expect `authenticated=true`, `role=ADMIN`, `status=ACTIVE`.
5. Execute GET `/api/accounts/`: expect HTTP 200. Then test Account POST/DELETE and dedicated role, lock/unlock, and reset actions as needed. Account PATCH is unavailable.
6. Execute POST `/api/auth/logout`, then GET `/api/auth/me` and GET `/api/accounts/`: both should return 401.
7. Keep `127.0.0.1` for docs, auth, admin and admin-portal paths. Do not mix it with `localhost` in one session.

For curl diagnostics, `X-CSRFToken` alone does not authenticate. Use curl's `-c <cookie-jar>` when fetching `/api/auth/csrf` and logging in, then `-b <cookie-jar>` for login, `/api/auth/me`, and Account requests; send the CSRF token in `X-CSRFToken` for POST/DELETE Account actions. Refresh the token after login because Django rotates it. Keep the cookie jar and development password out of logs, source control, and shared examples.

### Account input normalization and immutable email — owner decision 2026-10-01

- **Current contract:** Account email is supplied on create only and is immutable immediately afterward. The former Account PATCH endpoint, `AccountUpdateInput`, HTML edit route/form/link, and `update_account_email` service were removed. Model `save()` rejects changed email; Account queryset `update()` and `bulk_update()` reject email writes. No replacement login identifier or generic update was added.
- Shared helpers in `apps/accounts/constants.py` normalize Account role/status input using `strip().upper()` and then validate against ADMIN/CUSTOMER and ACTIVE/LOCKED. Account forms use a shared canonical choice field; direct services, manager/model entry points, and list selector also normalize/validate. Invalid values still fail. SQL CHECK constraints and stored canonical uppercase values are unchanged. Role change, lock/unlock and administrator password reset stay on dedicated actions with their existing service protections.
- Current Swagger Account operations: GET/POST `/api/accounts/`; GET/DELETE `/api/accounts/{account_id}`; POST `/api/accounts/{account_id}/role`, `/lock`, `/unlock`, `/reset-password`. **No Account PATCH** appears in OpenAPI. Example create: `{"email":"customer01@test.local","role":"customer","status":"active","password":"Customer@123456","password_confirm":"Customer@123456"}`. Role action accepts `{"role":"admin"}`, `{"role":"Admin"}`, or `{"role":"ADMIN"}` and stores ADMIN. Role/status list filters accept mixed case; invalid filters return 400.
- Account regression: **57/57 tests passed** on existing disposable `test_crm_db` (`--keepdb --noinput`), covering foundation, P00-10, HTML, API, session auth, normalization, email immutability, password reset and protected actions. `python manage.py check`: 0 issues. `python manage.py makemigrations --check --dry-run`: `No changes detected`. `database/crm_db.sql` was not edited; SHA-256 remains `118c3a75ec724ab696b812efb93b8e3c7a309c3ed4d1b023cbe1eb5dd89d8f98`. No live database mutation was made.
- The older P02-07 generic update task and earlier Account email-edit examples above are superseded by this decision. **Exact next task remains ACCOUNT ADMIN UI** with read-only email display and dedicated Account actions.

### Admin Portal UI and custom login — 2026-10-01

- Added standalone `/login/`, POST `/logout/`, and a root redirect. Login uses `authenticate(request, email=..., password=...)`, Django `login()`, the current Account model, and an ACTIVE ADMIN check. Invalid credentials, CUSTOMER, and LOCKED ADMIN receive one safe error. Anonymous Admin Portal HTML requests redirect to `/login/?next=...`; safe local `next` destinations are limited to `/admin-portal/`. CUSTOMER requests remain 403; a locked session is treated as unauthenticated. `/admin/` and `/admin/login/` remain intact. Logout is POST-only with Django CSRF and invalidates the session.
- Reusable `templates/admin_portal/base.html` shell has a left sidebar, compact header, signed-in email and text Logout action. Bootstrap 5.3.3 CSS/JS comes from a CDN; `static/css/admin_portal.css` and small vanilla `static/js/admin_portal.js` handle portal styling, modal targets and reopening after form errors. Desktop sidebar is visible; mobile uses a text Menu button and Bootstrap offcanvas. A small text-based `static/favicon.svg` is included. No icon library, icon-only action, emoji, SPA or build pipeline was added.
- Sidebar uses real links for Accounts, Products, Suppliers and Database Tools. Customers, Feedback and Surveys appear as disabled text because no management landing routes/backends exist. There is no standalone Authorization navigation item or `/admin-portal/authorization/` route; supported role changes remain in Account Management. The shared shell also wraps the existing catalog list/form templates; catalog business logic was not changed. Future modules can extend the base and enable their links when routes are ready.
- `/admin-portal/accounts/` is now the primary one-page workflow: filters and pagination use the existing selector; the table displays safe email, role, status, last-login and creation data. Create, Change Role and Reset Password use Bootstrap modals; Lock/Unlock/Delete use a confirmation modal with Account context. HTML forms POST with CSRF to existing services. Server validation reopens Create/Reset modals with field errors. Actions return to the list with Django messages. There is no generic Edit or Change Email control. The read-only Account detail route remains available for compatibility.
- Database Tools status: a protected `/admin-portal/database/` page shows the repeatable `seed_data` command as a development-only, confirmed POST action. Backup/restore service modules and `scripts/backup.bat`/`restore.bat` are empty in this checkout; no callable Admin Portal backend exists, so there are no fake Backup or Restore buttons. The SQL export script overwrites canonical `database/crm_db.sql`; no downloadable UI export was exposed during this UI phase. The owner-confirmed RESTORE TEST: PASS was not repeated. `database/crm_db.sql` and restore scripts were not modified.
- Tests: added 8 Admin Portal UI tests for login, root/next routing, session logout, CSRF, access control, sidebar, one-page Account controls, safe content, and Database Tools confirmation; updated Account HTML expectations for anonymous redirects. Existing Account/API/catalog/survey coverage remained green. Full `python manage.py test --keepdb --noinput`: **72/72 passed** on the separate test database. `python manage.py check`: 0 issues. `python manage.py makemigrations --check --dry-run`: `No changes detected`. API routes `/api/docs`, `/api/auth/*`, and `/api/accounts/*` were not redesigned.
- Remaining team integration: implement reviewed callable Backup/Restore services and safe downloadable SQL export before enabling those UI actions; implement CRM module landing pages before enabling their disabled sidebar items. Group/Permission management remains separate backend work if requested later; it does not have a sidebar destination in this phase. A real browser walkthrough at desktop/mobile sizes with local ACTIVE ADMIN credentials remains to be performed by the owner.

### Account Management email search — 2026-10-01

- Added server-side `q` search on Account email through `list_account_page` using trimmed, case-insensitive ORM matching. Search combines with validated role/status filters and retains stable Account ordering. Empty `q` leaves the list unfiltered.
- The Account page now places a text search control beside role/status filters, retains the validated `q`, role and status values in pagination links, and offers a Clear link. A valid search with zero matches shows `No accounts found.` while Create Account remains available.
- Added focused HTML tests for exact/partial/case-insensitive search, whitespace and no-result behavior, combined role/status filters, and pagination query preservation. Full `python manage.py test --keepdb --noinput`: **75/75 passed**. `python manage.py check`: 0 issues. `python manage.py makemigrations --check --dry-run`: `No changes detected`. No API or database schema change.

### Products and Suppliers SQL field UI alignment — 2026-10-02

- Compared `database/crm_db.sql` with current `Supplier` and `Product` models and forms. All nine Supplier and ten Product SQL columns are represented by existing model fields; both forms already include exactly the editable business fields and omit generated IDs/timestamps. Product category, brand and supplier use required ForeignKeys and readable select options. No model field/schema mismatch or migration is needed.
- Supplier list now displays ID, code, name, address, phone, email, status, creation and update times, and actions; NULL contact/address values show an em dash. Supplier search (`q`) across code/name/email/phone, status filtering, combination and pagination query preservation remain in place.
- Product list now displays ID, name, readable Category/Brand/Supplier names, complete wrapping description, locale-formatted price, status, creation and update times, and actions. Existing `select_related("category", "brand", "supplier")` avoids related-object N+1 queries; Product search and Supplier filter remain unchanged.
- Both tables retain the Bootstrap responsive scroll wrapper and text Edit/Delete buttons with `d-flex gap-2 flex-wrap`. Focused Catalog and Admin Portal regression tests cover list columns, nullable display, form coverage, filter behavior and actions: `python manage.py test apps.catalog apps.admin_portal --keepdb --noinput` passed **21/21**. `python manage.py check`: 0 issues. `python manage.py makemigrations --check --dry-run`: `No changes detected`. Browser visual inspection at desktop/mobile sizes remains pending.

### TV1 auth, customer self-service and shop — 2026-10-08

- [x] Surveyed AGENTS.md, repository SKILL.md, plans.md, README, runtime, settings,
  auth backend, permission decorators, API, routes, models/migrations, layouts,
  tests and seed conventions. Working tree was clean; HEAD and freshly fetched
  origin/develop both `ee13e427854faaa2ccb3086f90c43f6f84bf2b97`. Created
  `feature/tv1-auth-customer` in the existing clean worktree. No merge/cherry-pick,
  commit, push, PR or GitHub mutation.
- [x] Common login/register/logout routes, safe permission-aware `next`, default
  role/group destinations, public shop home and protected CRM home. Kept named
  admin login/logout and all admin templates/services/API intact. LOGIN_URL now
  names customer_auth:login; admin guard still explicitly reverses admin login.
  LOCKED cannot use protected pages with old sessions; locked login message
  requires a verified password.
- [x] Registration normalizes via AccountManager, validates/hashes via Django,
  always creates CUSTOMER/ACTIVE and Customer ACTIVE atomically. Duplicate email
  and unique-constraint races map to email errors; unrelated DB failures are not
  swallowed. No caller-supplied security fields are writable.
- [x] Own-profile service/formset for existing Customer/CustomerPreference fields;
  fresh ACTIVE actor/profile lookup, Account row locks and preference ownership
  checks on every submitted ID. Email/role/status/groups/permissions untouched.
  Phone/date/length validation; future birth dates rejected. Profile and preference
  writes roll back together on error. No change to customer-management logic.
- [x] Current-password change with Django validators and session hash update;
  token reset through Django views/forms/token generator, 1-hour timeout,
  single-use behavior, stale-session invalidation and status/token recheck under
  row lock at write. Reset does not log in or unlock. AccountPasswordResetForm
  filters status=ACTIVE because is_active is a property, not a physical column.
  Reset-request response is identical for missing/locked email. Console mail in
  DEBUG and SMTP env settings; credentials/password/hash are not logged.
- [x] Shop read selectors on current Product ACTIVE status; name/category/brand/
  Decimal price filters, stable product_id order, 12 products per page and query
  preservation. Invalid filters return field errors/400; missing or INACTIVE
  detail is 404. Local Bootstrap 5.3.3 CSS with MIT license, local SVG placeholder
  and responsive CSS; no new frontend framework or model fields.
- [x] README run/demo/email/test instructions; docs/15_week_plan.md proposal with
  blank group/student identifiers; docs/chapter4.md reflecting actual TV1 scope;
  docs/tv1_handoff.md URL/permission/model/menu contracts for TV3/TV4/TV5.

**Schema and cross-module contract.** No model/migration/SQL changes. Reused
Customer.account OneToOne and CustomerPreference.customer FK; no FK/on_delete
change. TV1 adds self-service files/views under customers and read-only shop
queries against catalog. TV3 admin UI and TV2/TV4/TV5 business code not edited;
only pre-existing tests expecting root 404 and old default LOGIN_URL were updated
for the newly authorized routes. API and separate admin-auth regressions passed.
Gender, playing_level and preferences are currently free-text schema fields with
no approved enum. TV1 keeps this contract, documents CATEGORY/name seed convention
and does not introduce a new fixed taxonomy. Formset permits add/edit/delete of
owned preferences and caps one submitted formset at 50 rows (100 parsed forms).

**Verification Log — current run.** Python 3.12.10, Django 5.2.17,
mysqlclient 2.3.0, MySQL 8.4.11. Global Python has all pinned requirements needed;
the existing external venv lacks Ninja and was not modified. Local ignored .env
was used without printing credentials.

- `python manage.py check`: 0 issues.
- `python manage.py makemigrations --check --dry-run`: No changes detected.
- `python manage.py test apps.customers.test_self_services --settings=config.test_settings --keepdb --noinput`:
  **7/7 passed**, backend/service before UI.
- Initial focused HTTP/shop/profile run: 29/30 passed; expiry test mixed UTC with
  Django's local naive token clock. Fixed the test clock, without changing expiry
  policy. It passes in the full run below.
- `python manage.py test --settings=config.test_settings --keepdb --noinput`:
  **144/144 passed in 186.899 seconds** on separate MySQL test_crm_db, including
  existing Account API/auth/admin/catalog/survey tests and 30 new TV1 cases.
  Existing migrations applied normally on DB test; no SQLite, fake or disabled
  migrations. The seed command's output in full regression comes from existing
  tests on test_crm_db, not a live seed action.
- Browser verified common login, registration form, products and product detail,
  logged-in profile, CRM group landing and POST logout on a temporary server
  pointed only to test_crm_db. Desktop and 390px product/CRM layout checked;
  DOM confirmed no horizontal overflow. Local CSS/placeholder requests succeeded.
  Browser preview fixtures were removed, server stopped, temporary ignored preview
  settings removed and browser closed. CRM screenshot saved outside the repo.
- Final source check and migration dry-run again succeeded; git diff --check has
  no whitespace errors. No real SMTP delivery test.

**Runtime findings / remaining dependencies.**

- [!] BLOCKED — live demo on this machine's crm_db: read-only table inventory
  found only technical tables and legacy tai_khoan/tai_khoan_groups/
  tai_khoan_user_permissions, with no current accounts/catalog/customers tables.
  showmigrations marks accounts initial and framework migrations applied, but
  current catalog/customers/feedback/surveys initials not applied; migrate --plan
  lists them. This conflicts with historical database-build notes. Do not blindly
  migrate/reset/restore; owner/TV3 needs a separate backup-and-reviewed-alignment
  task. TV1 did not add legacy compatibility code or mutate live crm_db.
- Initial proposed test_crm_tv1_auth_customer was denied with MySQL 1044. Read-only
  grant inspection showed crm_user has ALL only on test_crm_db; changed dedicated
  test settings to that already-authorized test database. No grants changed.
- [ ] TV4 customer/feedback/report landing and backend permissions to enable CRM
  menu; feedback submit route absent on develop, so product action remains Sắp có.
- [ ] TV5 personal survey list and CRM survey landing before enabling shared menu.
  Existing recipient-specific survey routes are preserved; no invented list,
  guessed recipient link or replacement survey implementation.
- [ ] SMTP provider/configuration and actual mail-delivery verification.
- [ ] Names/MSSVs, dates, actual individual contributions and report screenshots
  to be filled/approved by the team; 15-week plan is a proposal.

### TV1 pre-publication review and isolated demo request — 2026-10-08

- Owner explicitly authorized commit, push of feature/tv1-auth-customer and a PR
  into develop, without merging it or integrating TV2/TV4/TV5 branches.
- Reviewed all 49 changed/new TV1 files: auth/forms/services/routes, profile
  ownership/transactions, shop selectors, templates/static/CSS, tests and docs.
  Vendored Bootstrap retained its upstream CSS and MIT license. No material TV1
  code defect found; no model/migration/SQL/API/admin UI changes introduced.
  The admin test change only replaces root 404 with the new shop homepage 200.
- Pre-stage audit passed: actual SECRET_KEY/DB_PASSWORD/EMAIL_HOST_PASSWORD values
  from local .env do not appear in candidate files; no private-key/GitHub-token
  patterns, unexpected scope files or trailing whitespace. .env and
  config/local_settings.py are ignored and not tracked. Local review scripts,
  manifests and prior screenshots are outside the repo; no backups/private data
  are included in the commit. Stage uses an explicit reviewed-file manifest.
- Fresh verification: `python manage.py check` reports 0 issues;
  `python manage.py makemigrations --check --dry-run` reports No changes detected;
  `python manage.py test --settings=config.test_settings --keepdb --noinput`
  passed **144/144 in 175.004 seconds** on MySQL test_crm_db. This database is only
  used for automated tests in this follow-up, not for new demo setup.
- [x] RESOLVED (see verification below) — initial CREATE of **crm_tv1_demo**
  returned MySQL 1044; grants initially covered only crm_db and test_crm_db.
  Asked the owner for demo-only privileges or local admin configuration. No
  fallback to a legacy/test DB for demo and no existing DB dropped/reset.
  Migrations and HTTP/browser checks were pending at this initial review stage.
- Machine-local `config/local_settings.py` prepared: deep-copies DB config and
  overrides NAME=crm_tv1_demo, localhost hosts and console email. It is ignored,
  contains no hard-coded credential and does not change group .env/default DB.
  README/handoff/Chapter 4 document exact setup/run commands, the initial blocker,
  URLs and the distinction from automated regression evidence.
- GitHub authentication/repository push permission verified; fetch shows develop
  still ee13e42, push dry-run for this feature branch succeeded. Publish as a draft
  while the separate demo validation is blocked; no merge/auto-merge is requested.
- TV4/TV5 post-merge steps documented in docs/tv1_handoff.md: preserve WIP, update
  develop with --ff-only, integrate origin/develop into their own feature branches,
  review shared-route/layout conflicts and run full regression before enabling menus.

### TV1 isolated demo verification and publication — 2026-10-08

- [x] RESOLVED — owner granted crm_user privileges on crm_tv1_demo and created
  that database. Inspection found it empty before any application operation.
  Reviewed migrate --plan, Account SQL and the existing MySQL schema-contract
  operation; applied all current migrations only to this fresh demo database.
  showmigrations marks all applied and check reports 0 issues. No existing
  database was dropped/reset; live crm_db still has its legacy table inventory.
- Demo: MySQL 8.4.11, utf8mb4/utf8mb4_unicode_ci, 23 physical tables including
  14 business tables. Local settings remains ignored; group .env/default settings
  retain their original configuration. No model/migration/SQL change was needed.
- Created only synthetic demo fixtures on crm_tv1_demo: 5 Accounts (ADMIN,
  CRM_MANAGER, CUSTOMER_SERVICE and customers), 2 Customer profiles, 1 category,
  1 brand, 1 supplier, 14 ACTIVE products and 1 INACTIVE product. Did not run the
  seed_data management command or import shared/private data. Fixtures retained.
- HTTP server at http://127.0.0.1:8000 using config.local_settings. **42 smoke
  checks passed**: registration/duplicate/privilege whitelist, customer/CRM/admin
  login and last_login/safe next, CSRF, profile/preference ownership and immutable
  account fields, password change session behavior, reset console link/token
  single-use/session invalidation, LOCKED login/session, catalog filters/pages/404,
  admin account list/detail/catalog and Django built-in admin.
- Windows console email initially raised UnicodeEncodeError when redirected
  to a local log. Restarted the demo process with PYTHONIOENCODING=utf-8 and
  reran the reset and remaining checks successfully. README and handoff document
  this runtime setting. No application source fix was necessary; SMTP unverified.
- Browser verified shop, customer login/profile, CRM_MANAGER login/landing,
  dedicated admin login/account list and admin catalog. Screenshots, smoke scripts,
  results and randomly generated demo credentials are local outside the repository.
  Never put passwords/reset tokens in source, PR description or report screenshots.
- Implementation commit cd9503273be84019d390e3bb72b766f457711296 was pushed.
  PR https://github.com/KhimTran/crm_project/pull/3 targets develop from
  feature/tv1-auth-customer; draft initially, ready for review after demo resolution.
  No PR merge, auto-merge or TV2/TV4/TV5 branch integration performed.

### TV1 customer profile usability and cross-branch contract — 2026-10-08

- Owner authorized direct implementation, commit/push and PR #3 update; no merge.
  Working tree initially clean on feature/tv1-auth-customer. Read AGENTS, current
  forms/models/services/tests, fetched refs and inspected TV4 constants/forms/
  services/tests at 2f0b82e and TV5 audience filters/forms/seed/tests at ef45cb9.
  No branch merge/cherry-pick or schema/model/migration/SQL change performed.
- Existing compatible convention: CATEGORY stores the category_name string;
  TV4 BRAND/PLAY_STYLE store display strings and TV5 filters raw preference values.
  TV4 gender MALE/FEMALE/OTHER; level BEGINNER/RECREATIONAL/COMPETITIVE.
  TV5 seed level INTERMEDIATE/ADVANCED differs; used the owner's requested TV4
  choices for new input and preserved legacy values without inventing a mapping.
  Future TV5 seed alignment and a single shared choices import are documented
  integration work, not implicitly approved data conversion.
- Replaced technical preference formset with dynamic ACTIVE Category checkboxes.
  Backend validates IDs, stores names, syncs only own CATEGORY rows atomically
  under row locks, removes deselected current names and prevents duplicates.
  Unmatched/inactive old category values are preserved unless explicitly selected
  for deletion by their owner. Other preference types are displayed read-only.
  Empty active-category state retains data. Revalidation handles a category being
  disabled after view form validation, returning an error without partial save.
- TV4-aligned dropdowns also apply to registration via the shared profile form.
  Existing unknown gender/level is an owner-specific choice; missing fields keep
  saved values, explicit blank clears to NULL, unknown new values are rejected.
- Fixed CTA text using only .customer-layout .shop-hero selectors; no admin style
  changes. Browser measured rgb(255,255,255) for normal, actual mouse hover and
  keyboard focus-visible. Profile saved through browser; checked default desktop
  and 390px with no horizontal overflow, two/one-column checkbox layout. Temporary
  viewport reset; screenshots outside repo.
- Verification: check 0 issues; makemigrations --check --dry-run No changes detected.
  `python manage.py test apps.customers apps.accounts.tests.test_customer_auth
  apps.shop apps.admin_portal --settings=config.test_settings --keepdb --noinput`
  passed **47/47 in 50.937 seconds** on MySQL test_crm_db. Includes multiple/uncheck/
  repeat/legacy/other-type/fake and inactive ID/ownership/rollback/dropdown cases.
- Demo: **26 checks passed** on crm_tv1_demo, including HTTP writes, profile data
  preservation and admin login/accounts/catalog. Ran only the read TV5 filter
  function definitions against the new demo values: exact preference and level
  filtering finds the customer, preference choices still contain category names.
  Local script's first preselection assertion incorrectly assumed an option index;
  corrected it to match by Category ID and reran successfully; no source defect.
  Added only synthetic profile fixture/category rows; no legacy/shared DB or bulk
  data conversion. Credentials, scripts/results/logs/images remain outside repo.

# Prompt library — CRM cầu lông

Copy một block, thay placeholders và bổ sung task ID từ `plans.md`. Các đường dẫn có chữ “dự kiến” chưa phải code tồn tại. Mọi prompt dùng schema trong `AGENTS.md`; đọc lại hiện trạng trước khi làm. Khi task bị chặn, ghi dependency/evidence và tiếp tục phần độc lập; không tự đổi schema để vượt blocker.

## Current Account foundation — owner decision 2026-09-29

CURRENT STATE: Django 5.2.17, MySQL `crm_db`, `accounts.Account` / `accounts`, `AUTH_USER_MODEL='accounts.Account'`. `TaiKhoan` / `tai_khoan` = **REMOVED LEGACY IMPLEMENTATION**, chỉ được nhắc trong historical notes, không có compatibility hoặc data migration. Initial Account migration đã apply với SQL-owned table, targeted foundation tests pass. Prompt 16 là mẫu chính cho mọi bug; 17–21 và 29 dùng để bổ sung hướng điều tra, không thay thế quy trình root cause.

## 01 — Khảo sát repository trước khi code

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Khảo sát repository CRM cầu lông, KHÔNG sửa file hoặc DB, không cài dependencies.
Đọc AGENTS.md và plans.md; kiểm tra git status, cấu trúc project, requirements.txt,
.env.example (không in secret), config/settings.py, config/urls.py và toàn bộ apps liên quan.
Xác định framework/version, apps, models, migration graph, URL structure, auth model/backend,
permission, test runner/tests, DB config, API convention và service layer nếu có.
Đọc kỹ apps/accounts/models.py và migrations/0001_initial.py; đối chiếu từng bảng/cột
với 13 bảng nghiệp vụ chính thức. Không coi bảng/field/role legacy là chuẩn mới.
Phân biệt migration tồn tại trong Git và migration đã apply trên DB; chỉ kiểm tra DB
nếu môi trường được chỉ định và truy cập read-only phù hợp, không chạy migrate.
Báo tách rõ hai phần: Current implementation (LEGACY IMPLEMENTATION có evidence file/function)
vs Target architecture (Account/accounts, đủ 13 model English trong AGENTS.md, DB crm_db).
Liệt kê conflicts, phần chưa xác minh, runtime/tool thiếu, migration đã apply hay chưa,
DB fresh/shared và dữ liệu cần giữ, ảnh hưởng Account/Customer/Feedback/Survey và bước tiếp.
Không coi model label legacy là target; đề xuất alignment trước Account CRUD.
Không giả định DRF, FBV/CBV hoặc một API đã tồn tại.
```

## 02 — Lập kế hoạch feature

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Lập kế hoạch cho [FEATURE], task [TASK_ID], requirements [REQUIREMENTS]. Chưa implement.
Đọc AGENTS.md, plans.md và code/tests/URLs/migrations liên quan trước khi đề xuất.
Trả kết quả đúng các mục:
- Mục tiêu và phạm vi ngoài task.
- File sẽ ảnh hưởng: tồn tại hay dự kiến mới, lý do cần sửa.
- DB impact: schema/data/FK/migration, có conflict với schema chính thức không.
- API impact: method/URL/request/response/status và compatibility.
- Security impact: auth/permission/CSRF/password/file/subprocess nếu liên quan.
- Test cases: success, validation, failure, anonymous, CUSTOMER, LOCKED, regression.
- Implementation order và dependencies theo task ID.
- Risks, quyết định cần chốt, cách rollback nếu thay dữ liệu.
Target auth là accounts.Account; không đổi AUTH_USER_MODEL trước migration analysis hoặc
lập kế hoạch rewrite cả repo. Naming đã chốt, chỉ strategy/preservation cần quyết định.
```

## 03 — Implement chức năng

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

FEATURE: [FEATURE]
REQUIREMENTS: [REQUIREMENTS]
EXPECTED_API: [EXPECTED_API]
RELATED_TABLES: [RELATED_TABLES]
TASK_ID: [TASK_ID]

Đọc AGENTS.md, plans.md; inspect code, migrations và tests hiện có trước khi code.
Đối chiếu requirement/schema, nêu ngắn gọn file ảnh hưởng và test plan rồi implement
phần tối thiểu cần thiết. Dùng convention hiện có; không tự thêm DRF/dependency.
Nếu có xung đột auth/schema chưa được chốt, ghi blocker thay vì thay model tùy tiện.
Backend kiểm tra quyền, validate input, xử lý lỗi đúng contract; không lộ password_hash.
Chạy targeted tests rồi regression cần thiết; xem git diff, cập nhật plans.md.
Báo file sửa, behavior, commands/kết quả thật, limitations. Không làm UI trong task backend.
```

## 04 — CRUD Accounts

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Triển khai task [TASK_IDS] CRUD Accounts sau khi GATE-A..J và foundation/alignment đã đạt.
Normal deactivation dùng status=LOCKED; không coi lock là DELETE hoặc tự hard-delete.
Đọc AGENTS.md, plans.md, accounts model/manager, URL/auth/permission/test hiện có.
Làm list có pagination/sort ổn định, search email, filter role/status, detail, create,
dedicated role/lock/unlock/reset actions và DELETE theo policy đã duyệt. Email bất biến
sau create; không tạo Account PATCH hoặc HTML edit email. Role/status input chấp nhận
khác hoa/thường và lưu giá trị uppercase chuẩn. URL hiện tại /api/accounts/;
điều chỉnh theo convention thực tế. Không expose hash/field auth nội bộ.
Normalize email, duplicate validation + ràng buộc đã chốt, validate lengths/enums,
password qua Django hashing/validators, whitelist fields. ADMIN guard mọi action.
Trước DELETE inspect customers.account_id, feedbacks.handled_by, surveys.created_by
và FK kỹ thuật. Nếu policy chưa rõ, báo blocker riêng cho DELETE và làm phần độc lập.
Test success, invalid/duplicate, pagination/filter, 401/403/404/409, CUSTOMER/LOCKED,
hash không lộ, FK/history được giữ và rollback liên quan. Không cascade tùy tiện.
Cập nhật task/evidence và API usage; không tạo giao diện.
```

## 05 — Lock/unlock account

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Implement lock/unlock cho [TASK_IDS], đọc AGENTS.md và auth flow hiện tại.
Contract dự kiến POST accounts/{account_id}/lock/ và /unlock/; trạng thái chuẩn
lần lượt LOCKED và ACTIVE, không thêm field ngoài schema chuẩn.
Chốt idempotency, tự khóa và ADMIN cuối cùng theo decision đã ghi; không tự chọn policy.
Kiểm tra ADMIN, target tồn tại, log actor/target/action không log credentials.
Tích hợp trạng thái vào login và request của session đã có; unlock cho login lại.
Test lock/unlock lặp, not found, non-admin, login bị khóa, session trước khi khóa,
unlock và regression create/update. Cập nhật plans.md, giải thích mapping is_active nếu dùng.
```

## 06 — Reset password

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Implement reset password [TASK_ID] theo flow đã chốt [ADMIN_SUPPLIED_TEMP_PASSWORD_OR_SYSTEM_GENERATED_TEMP_PASSWORD_OR_RESET_LINK_TOKEN].
Đọc AGENTS.md, password mapping/manager/backend/session hiện tại; không đổi AUTH_USER_MODEL.
Nếu GATE-J chưa chốt một trong ba flow trên, ghi [!] BLOCKED; không tự chọn reset UX.
API/service phải có auth + ADMIN/permission thích hợp, validate password bằng cơ chế
Django và hash qua set_password/API tương đương. Không gán plaintext vào password_hash.
TUYỆT ĐỐI không trả password_hash, password mới hoặc token bí mật trong log/URL;
response chỉ xác nhận kết quả phù hợp flow. Không dùng mật khẩu cố định cho tài khoản thật.
Chốt ảnh hưởng session cũ, account LOCKED và cách bàn giao mật khẩu/token theo flow.
Test unauthorized/forbidden/not found/weak password; nếu flow cho phép, old password
thất bại, new password thành công, session invalidation và trạng thái khóa không bị bỏ qua.
Cập nhật plans.md, API contract và log action với actor/target (không password).
```

## 07 — Role / permission / group

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Thực hiện [TASK_IDS] phân quyền với requirements [PERMISSION_MATRIX].
Đọc auth model/migration và ADR trong AGENTS.md/plans.md. Repo có AbstractUser legacy
và Groups/Permissions kế thừa nhưng chưa có guard nghiệp vụ; không coi chúng đã hoàn chỉnh.
Giữ role DB ADMIN/CUSTOMER. Không thêm giá trị role legacy để biểu diễn nhóm quyền.
Nêu nguồn quyết định quyền: status/role gate, group, direct permission, superuser policy.
Bảng kỹ thuật Django/M2M đã được phép bên cạnh 13 bảng nghiệp vụ; không hỏi lại.
Chốt Groups/Permissions strategy tại GATE-G, không tạo thêm bảng domain. Implement checks backend
tập trung, group CRUD, permission assignment và account membership theo contract đã chốt.
Test từng method/action: anonymous, CUSTOMER kể cả có group quyền, LOCKED, ADMIN có/thiếu
permission, revoke và chống tự nâng quyền. Log permission changes; cập nhật plan/contract.
```

## 08 — Backup service

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.

Viết backup service [TASK_ID], chưa làm UI. Đọc settings/.env.example/AGENTS.md/plans.md.
Đề xuất module nhỏ trong apps.admin_portal nếu repo chưa có convention service.
Dùng mysqldump, DB config từ settings, executable từ MYSQL_BIN/PATH đã validate;
ưu tiên --single-transaction --no-tablespaces --default-character-set=utf8mb4.
Output database/backups/ với timestamp + chống trùng; publish file chỉ khi thành công.
Subprocess argv, shell=False, timeout, binary output, kiểm tra returncode; xử lý config
thiếu, executable thiếu, permission/disk/output lỗi. Credentials qua cơ chế an toàn,
không password trong source/command log. Log kết quả đã sanitize, không tự thêm bảng audit.
Nếu expose API/command, route qua cùng service; API chỉ ADMIN theo policy đã duyệt.
Test mock success/failure/missing tool/config/timeout và cleanup file lỗi/credentials.
Cập nhật plans.md và cách chạy; không dump dữ liệu thật trong test.
```

## 09 — Restore service

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.

Viết restore service [TASK_ID], không tự chạy restore thật trên DB chung/production.
Đọc AGENTS.md, plans.md, backup service và cấu hình hiện có. ADMIN guard + xác nhận
rõ backup ID/file và DB đích. Chốt nguồn dump tin cậy; extension .sql không đủ đảm bảo an toàn.
Validate regular file/size/format, canonical path nằm trong backup root, chặn traversal,
absolute path ngoài root và symlink/junction escape. Không lấy command/DB host tùy ý từ input.
Dùng mysql argv shell=False, stdin file, timeout/exitcode; log start/end/error không secret.
Nêu recovery khi import áp dụng dở; bảo vệ ghi đồng thời và chuẩn bị pre-restore backup.
Test unauthorized/forbidden/no confirmation/invalid file/traversal/subprocess failure
và success bằng mock. Integration dùng DB disposable, kiểm tra dump không USE/CREATE
DATABASE trỏ DB thật; không tự xác nhận restore hộ người dùng. Cập nhật plan và runbook.
```

## 10 — Tạo backup.bat

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.

Tạo scripts/backup.bat cho Windows, task [TASK_ID], sau khi backup service/command có sẵn.
Đọc AGENTS.md và interface command hiện có; wrapper phải gọi cùng logic đã test.
Resolve root từ %~dp0; setlocal, quote biến/path, hỗ trợ cwd khác và path có khoảng trắng.
Chọn Python/venv rõ; lấy .env qua Python/settings, không thực thi .env như batch,
không chứa/echo DB password. Kiểm tra ERRORLEVEL ngay sau command, truyền exit code thật,
thông báo success/failure rõ, không pause làm automation treo.
Verify Windows: success, missing config/tool, command failure, path có khoảng trắng.
Không tạo backup DB thật để kiểm tra wrapper nếu chưa có môi trường demo phù hợp.
Cập nhật plans.md và usage.
```

## 11 — Tạo restore.bat

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.

Tạo scripts/restore.bat cho Windows, task [TASK_ID], dùng restore service/command hiện có.
Đọc AGENTS.md; resolve root theo %~dp0, quote mọi path/biến, xử lý file có khoảng trắng.
Hiển thị file và DB đích, yêu cầu xác nhận đúng thao tác; không bỏ qua validation/guard
của service. Không nhúng password, không parse .env bằng call, không nhận shell tùy ý.
Kiểm tra ERRORLEVEL, giữ nonzero exit khi lỗi, báo hủy/thành công/thất bại chính xác.
Test hủy, file thiếu/traversal, command fail và success qua test command/DB disposable.
Không restore DB chung/production khi verification. Cập nhật plan và usage.
```

## 12 — seed_data management command

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Triển khai python manage.py seed_data, task [TASK_IDS]. Đọc AGENTS.md và toàn bộ models/FK
hiện có. Nếu models của thành viên khác chưa sẵn sàng, ghi dependency, không tự thay schema.
Bao phủ accounts, customers, categories, brands, products, customer_preferences, feedbacks,
surveys, survey_questions, survey_options, survey_recipients, survey_responses, survey_answers.
Tạo theo FK; fixture demo deterministic, natural keys ổn định, không trùng vô hạn khi chạy lại.
ADMIN/CUSTOMER/LOCKED dùng set_password hoặc API tương đương; không gán password_hash trực tiếp.
Seed đủ tình huống demo được duyệt, option/question/response đúng survey, rating/enum hợp lệ.
Nếu thêm --reset, cảnh báo + xác nhận, chỉ xóa bộ demo, guard môi trường, rollback khi lỗi;
không flush DB nhóm hoặc ghi đè account thật trùng key. Log summary, không log password.
Test lần 1/lần 2, duplicate collision, reset/cancel, FK và lỗi giữa chừng. Cập nhật plans.md.
```

## 13 — Xuất crm_db.sql

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.

Thực hiện SQL export [TASK_IDS] thành database/crm_db.sql từ DB DEMO sạch [DEMO_DB].
Tên DB chính thức là crm_db; setup guide dùng DB_NAME=crm_db và DDL
CREATE DATABASE crm_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE crm_db; Đây là ví dụ setup, không tự chạy trên DB shared.
Tên database và tên file SQL đều dùng crm_db; không chạy lại file khởi tạo đã chứa DROP DATABASE trên DB hiện có.
Đọc AGENTS.md, migrations/seed và phạm vi dữ liệu bảng kỹ thuật trong SQL export.
Bảng kỹ thuật Django đã được phép; chỉ scope dump cần chốt, không hỏi lại allowance.
Dump structure + demo data, utf8mb4; không credentials thật, tokens/sessions thật,
CREATE USER/GRANT/definer phụ thuộc máy. Không lấy dữ liệu từ DB production/cá nhân.
Giữ script import được vào DB rỗng khác tên; không nhúng USE/CREATE DATABASE về DB nguồn.
Tạo command/script tái lập theo convention repo. Import kiểm chứng trên [DISPOSABLE_DB]
với guard đích, rồi kiểm tra 13 bảng nghiệp vụ + bảng kỹ thuật trong scope dump, FK/count/tiếng Việt,
đăng nhập admin demo, API đại diện và migration state. Không báo DONE nếu chưa import test.
Ghi revision/commands/result trong plans.md; phân biệt luồng migrate+seed và import dump.
```

## 14 — Tests cho một feature

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Viết tests có giá trị cho [FEATURE], task [TASK_ID], contract [CONTRACT].
Đọc AGENTS.md, code và tests hiện có; mặc định Django test runner nếu repo chưa đổi.
Lập matrix success/failure/validation/401/403/404/409/CUSTOMER/LOCKED/CSRF nếu liên quan.
Kiểm tra hash không lộ, FK/rollback/invariants, boundary input và regression bug đã biết.
Dùng test DB riêng; mock external subprocess cho unit tests, tách integration MySQL/restore.
Không gọi backup/restore vào DB dev chung, không thêm pytest/DRF chỉ để viết test.
Chạy targeted tests rồi regression phù hợp, ghi command và số test/kết quả thật.
Nếu runtime thiếu, ghi BLOCKED và cách unblock, không coi zero tests là pass feature.
```

## 15 — Code review trước khi sửa

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Đóng vai reviewer cho [DIFF_OR_BRANCH_OR_FILES]. Chỉ review, KHÔNG rewrite/sửa file.
Đọc AGENTS.md, plans.md, requirements và code quanh diff cùng tests/migrations liên quan.
Kiểm tra correctness, security, DB consistency với schema chính thức, auth/permissions,
validation/error contract, test coverage, regression và maintainability.
Chú ý alignment từ LEGACY IMPLEMENTATION sang Account/accounts, role cũ cần chuyển có
kiểm soát, FK/history, password_hash, CSRF, path/subprocess nếu liên quan. Kiểm tra model,
field, API/test identifiers English; legacy names chỉ được tham chiếu để audit/migrate.
Trả findings theo mức nghiêm trọng: file:line, evidence, tình huống tái hiện, tác động,
patch gợi ý nhỏ nhất và test cần có. Phân biệt bug chắc chắn, nghi vấn và quyết định nghiệp vụ.
Nếu không có finding, nói rõ phạm vi đã review và phần chưa verify; không bịa lỗi.
```

## 16 — FIX BUG (prompt chính)

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Do not delete migrations or reset the database just to make the error disappear.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

BUG:
[PASTE ERROR]

HOW TO REPRODUCE:
[STEPS, ENVIRONMENT, REVISION, USER ROLE]

EXPECTED:
[EXPECTED BEHAVIOR]

ACTUAL:
[ACTUAL BEHAVIOR, SANITIZED REQUEST/RESPONSE]

TASK/BUG ID: [ID]

Đọc AGENTS.md (Debugging Protocol, Error Investigation Checklist) và plans.md.
Không sửa ngay. Đọc lỗi nguyên văn, reproduce, đối chiếu expected/actual, kiểm tra
request/response/log/traceback đã che secret. Trace từ symptom qua URL, view, auth,
permission, validation, service, ORM/migration hoặc subprocess tới root cause.
Chỉ ra root cause bằng evidence trong code (file/function/line) và lỗi/test liên quan;
không trình bày giả thuyết chưa chứng minh như kết luận. Nếu thiếu thông tin, nêu rõ
phần thiếu và tiếp tục điều tra độc lập; không đoán rồi sửa hàng loạt.
Liệt kê file cần sửa và plan patch nhỏ. Implement khi root cause đủ rõ trong scope đã giao;
không cần dừng xin duyệt patch thường, nhưng tuân thủ guard khi đổi DB/nghiệp vụ lớn.
Thêm test tái hiện lỗi khi có giá trị, chạy targeted tests rồi regression theo dependencies.
Do not fix a bug by reintroducing legacy Vietnamese schema names.
Do not fix a bug by bypassing authentication, permissions,
validation, foreign keys, or the official English schema.
Không nuốt exception, bỏ validation, xóa test fail, hard-code demo hoặc tùy tiện đổi schema.
Cập nhật Bug Log trong plans.md: reproduce, root cause, fix, files, tests, regression, notes.
Báo nguyên nhân, patch, bằng chứng xác minh và limitations; không claim pass nếu chưa chạy.
```

## 17 — Fix API 500

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Do not delete migrations or reset the database just to make the error disappear.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Áp dụng prompt FIX BUG cho API [METHOD URL], lỗi [TRACEBACK], payload [SANITIZED_PAYLOAD].
Đọc AGENTS.md; tái hiện cùng role/session và config tương ứng; trace project frame trong
traceback qua view/validation/service/ORM/subprocess. Kiểm tra exception gốc và DB state.
Phân biệt input lỗi cần 400/409 với lỗi server 500; không bọc toàn view bằng except Exception
để trả success/200. Không expose traceback/SQL/secret ra JSON, không chữa bằng DEBUG=True.
Nêu evidence root cause, patch nhỏ, test request lỗi + success + permission/regression.
Cập nhật Bug Log và response contract nếu chỉ rõ đó là bug contract hiện có.
```

## 18 — Fix Migration

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Do not delete migrations or reset the database just to make the error disappear.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Áp dụng FIX BUG cho [MIGRATION_ERROR], app [APP], DB môi trường [TARGET_ENV].
Đọc AGENTS.md, model, migration graph, Git history và trạng thái migrations thật qua
showmigrations/migrate --plan khi có quyền truy cập. Đối chiếu DB thật với migration state.
CURRENT STATE: accounts/0001_initial.py mô tả Account/accounts và đã apply trên `crm_db`.
HISTORICAL ONLY: model/table legacy đã bị loại bỏ theo quyết định owner; không làm compatibility hoặc data migration từ chúng.
Xác minh migrations đã apply, DB fresh/shared và dữ liệu cần giữ trước thay đổi tiếp theo.
Không xóa migration, dùng --fake, DROP hoặc reset DB theo suy đoán.
Nêu root cause, dữ liệu/FK bị ảnh hưởng, đề xuất migration mới và recovery khi cần.
Nếu migration state chưa rõ, STOP destructive migration; ghi [!] BLOCKED task và dependencies.
Nếu đổi auth/model/table về sau có thể phá dữ liệu, đánh BLOCKED task alignment, đề xuất staged
strategy và chờ approval trước destructive operations; không khôi phục legacy implementation.
Review migration/SQL và inventory mọi FK: source, target, nullable/required, expected ON DELETE,
hậu quả nghiệp vụ; không giả định CASCADE. Trước rename/transform/remove dữ liệu, tạo và xác minh
backup theo AGENTS.md; backup lỗi/chưa xác minh thì STOP. Không destructive steps khi chưa approval.
Test trên DB disposable cả fresh install và upgrade từ trạng thái lỗi tương ứng.
Cập nhật Bug Log/ADR, ghi rõ điều đã chạy và điều chưa chạy.
```

## 19 — Fix permission 401/403

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Do not delete migrations or reset the database just to make the error disappear.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Áp dụng FIX BUG cho [METHOD URL], actor [ROLE_STATUS_GROUPS], response [ERROR].
Đọc AGENTS.md và auth/permission/CSRF thực tế; phân biệt chưa login, thiếu quyền, LOCKED
và CSRF fail. Kiểm tra cookie/session/header, backend, role gate, group/permission,
superuser bypass và LOGIN_URL/namespace nếu có redirect.
Chứng minh expected access theo matrix đã duyệt, patch đúng nguyên nhân; không dùng
csrf_exempt, bỏ guard hoặc nâng role để làm request pass. Không chỉ sửa nút UI.
Test anonymous/CUSTOMER/LOCKED/ADMIN, CSRF có/thiếu và quyền bị revoke trên từng action.
Cập nhật Bug Log và regression result.
```

## 20 — Fix MySQL/FK

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Do not delete migrations or reset the database just to make the error disappear.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Áp dụng FIX BUG cho [MYSQL_ERROR], thao tác [OPERATION], môi trường [ENV].
Đọc AGENTS.md; kiểm tra connection config đã che secret, server/port/driver/quyền DB
nếu connection fail. Nếu FK fail, truy parent/child, ID/type, NULL/on_delete, migration
state và thứ tự insert/delete/seed/import; kiểm tra quan hệ survey chéo.
Không tắt foreign_key_checks hoặc cascade xóa dữ liệu để che bug. Không in DB_PASSWORD.
Nêu evidence root cause và patch nhỏ; transaction.atomic cho nhiều bước phù hợp.
Test MySQL riêng: valid relation, invalid relation, delete protected và rollback; regression
accounts/customers/feedback/surveys theo tác động. Cập nhật Bug Log.
```

## 21 — Fix backup/restore

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Do not delete migrations or reset the database just to make the error disappear.

Áp dụng FIX BUG cho [BACKUP_OR_RESTORE_ERROR], command/exitcode đã sanitize [EVIDENCE].
Đọc AGENTS.md và service/batch hiện có. Kiểm tra MYSQL_BIN/PATH/executable, quoting path,
config, credentials mechanism, argv/options, stdin/stdout binary, timeout/returncode,
quyền file, backup root và DB đích. Không echo password/raw command chứa secret.
Reproduce bằng mock/test command trước; restore thật chỉ DB disposable và xác nhận đúng đích.
Không tự restore lại production để xem lỗi. Kiểm tra dump USE/CREATE DATABASE, partial restore
và recovery nếu lỗi giữa chừng. Patch nhỏ, không success khi subprocess fail.
Test success/failure/missing executable/config/invalid file/traversal, Windows path khoảng trắng.
Cập nhật Bug Log, targeted/regression evidence và runbook.
```

## 22 — Refactor không đổi behavior

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Refactor [FILES_OR_COMPONENT] vì [REASON], task [TASK_ID]. Đọc AGENTS.md/plans.md và tests.
Xác định behavior/contract hiện tại cần giữ, chạy baseline tests nếu môi trường sẵn sàng.
Đề xuất patch nhỏ, chỉ refactor phạm vi được giao; không đổi schema, AUTH_USER_MODEL,
API payload/status, permissions hoặc dependencies. Nếu phát hiện bug, ghi riêng trước khi sửa.
Ưu tiên tên rõ, function nhỏ, tách business logic cần thiết; không tạo abstraction quá mức.
Chạy targeted/regression tests, so sánh behavior trước/sau, kiểm tra diff; cập nhật plans.md.
```

## 23 — Tạo API documentation

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.

Tạo/cập nhật tài liệu API [SCOPE] tại [DOC_PATH], task [TASK_ID].
Đọc AGENTS.md, URLs/views/service/tests thực tế; không biến candidate APIs thành API đã có.
Với mỗi endpoint, dùng format:
METHOD:
URL:
AUTH:
REQUEST:
RESPONSE:
ERRORS:
EXAMPLE:
Nêu session/CSRF, role/status/permission, params/search/filter/pagination, field read-only,
success/error envelope/status, duplicate/delete policy và password reset nếu liên quan.
Ví dụ chạy được trên Windows bằng curl.exe/PowerShell theo auth thực tế; không chứa secret thật.
Phân biệt implemented/planned; kiểm chứng ví dụ với test/demo environment, cập nhật plans.md.
```

## 24 — Frontend integration (sau backend)

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.

Tích hợp UI [SCREEN] với API [IMPLEMENTED_ENDPOINTS], task [TASK_ID].
Chỉ bắt đầu khi backend contract/tests và Phase 8/9 liên quan đạt gate trong plans.md.
Đọc AGENTS.md, API docs và backend code hiện tại; dùng Django Templates + Bootstrap 5
theo hướng đồ án, không tự cài SPA framework. Không đổi backend contract tùy tiện.
Xử lý loading/error/success, empty state, field errors, pagination và session/CSRF.
Validate form cả frontend lẫn backend; quyền thực tế luôn ở backend. Không expose hash.
Test UI/API contract với ADMIN/CUSTOMER/LOCKED và failure responses; cập nhật plans.md.
```

## 25 — Trang Admin Accounts (sau backend)

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.

Tạo trang Admin Accounts [TASK_IDS] sau khi backend accounts/auth/permissions ổn định.
Đọc AGENTS.md/plans.md và APIs đã implement. Dùng Django Templates + Bootstrap 5.
Làm list/pagination/search/filter role/status, detail, form create/edit, lock/unlock,
reset password form/modal; delete và confirmation đúng policy backend đã chốt.
Field errors, loading/empty/error/success rõ; không hiện password_hash hoặc tự suy diễn
field hồ sơ customers thành accounts. Gửi CSRF, tránh double submit; không đổi API vì UI.
Kiểm tra responsive cơ bản và các flow thành công/thất bại/forbidden; cập nhật plan.
```

## 26 — UI Backup/Restore (sau backend)

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.

Tạo UI Backup/Restore [TASK_IDS] trên Django Templates + Bootstrap 5 sau service/API tests.
Đọc AGENTS.md, actual contract và plans.md; chỉ ADMIN theo backend policy.
Backup hiển thị pending/success/failure đúng kết quả thật; không báo thành công trước exitcode.
Restore chọn backup hợp lệ, hiển thị file + DB đích và cảnh báo/xác nhận rõ thao tác mất dữ liệu;
disable submit lặp, xử lý cancel/error/success. Không gửi arbitrary path/shell từ UI.
Không để frontend là nơi duy nhất validate permission/file/confirmation.
Test UI với mocked failure và DB demo/test được xác nhận; không restore DB chung tùy tiện.
Cập nhật plans.md và ảnh demo khi phù hợp.
```

## 27 — Kiểm tra trước demo

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.

Kiểm tra demo readiness [TASK_IDS] theo AGENTS.md/plans.md; môi trường [DEMO_ENV].
Xác minh Windows runtime/deps/MySQL/mysql/mysqldump, .env local dùng DB_NAME=crm_db
ở môi trường demo chính thức, charset utf8mb4/collation utf8mb4_unicode_ci. DB test/restore
phải tách biệt, ví dụ crm_db_import_test; không sửa file DB ngoài phạm vi.
Thực hiện clean DB setup đã được phép → review/apply migrations → seed → admin login →
CRUD/search/filter → lock/unlock/reset → CUSTOMER bị cấm quản trị → group permissions →
backup → restore có xác nhận trên DB demo disposable → SQL import vào DB rỗng khác.
Đối chiếu customers/feedback/surveys, ghi commands/results và lỗi vào Bug Log.
Kiểm tra screenshots, API docs, runbook, demo credentials chỉ là dữ liệu mẫu; không quay/chụp secret.
Không xóa/reset DB nhóm để chuẩn bị demo. Báo pass/fail/blocker, không che bước chưa chạy.
```

## 28 — Regression trước merge

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Kiểm tra regression trước merge [BRANCH_OR_DIFF], không tự merge/push.
Đọc AGENTS.md, plans.md, diff và dependencies; chọn tests theo tác động và full suite phù hợp.
Accounts/auth/permissions phải kiểm tra ADMIN/CUSTOMER/LOCKED, CRUD/reset/hash exposure;
cross-module kiểm tra customers, feedback handled_by, surveys created_by nếu bị ảnh hưởng.
Backup/restore mock tests; seed idempotency, MySQL constraints và SQL import integration
chỉ dùng DB test/disposable. Review migration plan, API compatibility, secrets và git diff --check.
Báo commands/results, regression scope chưa chạy và blockers; cập nhật plans.md.
Không chạy restore production hoặc sửa test fail để che regression.
```

## 29 — Phân tích traceback

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.
Do not delete migrations or reset the database just to make the error disappear.
Before modifying Account/Auth models, inspect migration history,
AUTH_USER_MODEL, database state, and data preservation requirements.

Phân tích traceback dưới đây, CHƯA sửa code:
[PASTE TRACEBACK WITH SECRETS REMOVED]
Context: [REQUEST_OR_COMMAND, ENV, EXPECTED, ACTUAL]

Đọc AGENTS.md và code file/function được nhắc; trace call chain từ entry point đến
exception gốc, phân biệt exception wrapper và root cause. Nêu file:line/evidence,
giả thuyết theo độ chắc chắn, cách reproduce tối thiểu và dữ liệu/log còn thiếu.
Không yêu cầu gửi password/.env thật, không tự thêm try/except hoặc đổi schema.
Đề xuất file cần patch và targeted/regression tests. Nếu được giao implement ở turn sau,
tiếp tục prompt FIX BUG từ evidence này, không điều tra lại vô ích.
```

## 30 — Chuẩn bị commit

```text
Use the official English schema and naming rules in AGENTS.md.
Do not copy legacy Vietnamese model/table/field names into new code.

Chuẩn bị commit cho [TASK_IDS], KHÔNG tự commit/push khi chưa được yêu cầu.
Đọc AGENTS.md/plans.md; xem git status, diff kể cả untracked files và git diff --check.
Kiểm tra scope, migrations đã merge không bị sửa tùy tiện, .env/backup/credentials không
bị stage, database/crm_db.sql chỉ chứa demo đã kiểm chứng nếu thuộc task.
Đảm bảo plan/API docs/Bug Log cập nhật đúng kết quả, không đánh DONE khi test còn blocked.
Trả kết quả:
- Files changed: path và mục đích.
- Tests run: command, kết quả và phần chưa chạy.
- Known limitations: blockers/risks còn thực tế.
- Suggested commit message: ngắn, mô tả thay đổi chính.
Không stage file người khác, không dọn working tree bằng reset/clean.
```

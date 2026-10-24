# Review và hoàn thiện PR #4 — 2026-10-10

PR: https://github.com/KhimTran/crm_project/pull/4

## Revision và bảo toàn checkout

- TV2 đã fetch: `origin/feature/tv2-catalog` tại **`2cc11b1ff0afeaad2ae00fe0bb1bd0cac0d1a167`**.
- Develop đã fetch: **`89a884b005961234b010ab7bdeb5414fc26adc99`**, đã gồm PR TV1 và TV4.
- GitHub xác nhận PR open, non-draft, mergeable tại đầu phiên. Pha review ban đầu không commit/push. Owner sau đó cho phép commit/push bản sửa và cập nhật mô tả PR #4; không approve hoặc merge PR.
- Checkout ban đầu `73f6/crm_project` sạch, detached tại `ee13e427854faaa2ccb3086f90c43f6f84bf2b97`; giữ nguyên checkout này.
- Worktree sửa TV2: `C:\Users\Khiem\.codex\worktrees\pr4-tv2-fix\crm_project`, bắt đầu tại đúng TV2 SHA trên. Bản sửa được đưa vào nhánh `feature/tv2-catalog` theo yêu cầu tiếp theo của owner.
- Worktree ghép thử: `C:\Users\Khiem\.codex\worktrees\pr4-tv2-integration\crm_project`, HEAD đúng develop SHA trên. Ghép TV2 tạm bằng `git merge --no-commit --no-ff <TV2 SHA>`, không conflict, không tạo commit và không cập nhật branch ref; áp dụng cùng form fix và tests mới.
- Code tree bản ghép được kiểm thử: **`2dc261d8c1a8f1ff2864758cb58ca60f1e7a4996`**, từ `git write-tree` sau khi stage bản ghép + hai file sửa, trước tài liệu. Đây là Git tree, không phải commit.
- Thay đổi của review PR #2 (`plans.md` và báo cáo mới ở worktree `pr2-tv4-review`) được giữ nguyên. Không đổi nhánh hoặc ghi đè checkout develop/TV1 của người dùng.

## Bản sửa

`apps/catalog/forms.py::SupplierForm.clean_phone` trước đó chỉ kiểm tra 8–20 ký tự thuộc một character class, nên nhận cả `........`, chuỗi ít/nhiều chữ số và nhiều dấu `+` hoặc `+` giữa/cuối chuỗi.

Bản sửa:

- Giá trị thiếu, rỗng hoặc chỉ whitespace được trả về `None`, giữ phone optional/NULL.
- Đếm **9–15 chữ số ASCII**, cùng phạm vi phone của hồ sơ TV1; không đếm dấu phân cách như chữ số.
- Tối đa một dấu `+`, chỉ ở đầu sau trim.
- Giữ khoảng trắng, dấu gạch, dấu chấm và ngoặc; giữ định dạng hợp lệ sau trim, không tự đổi số điện thoại lưu trữ.
- Giữ giới hạn field/model 20 ký tự, không đổi model, schema, SQL, migration hay FK.
- Lỗi trả về field `phone` với thông báo rõ; không thay auth hoặc permission.

## Tests mới

Thêm `apps/catalog/test_pr4_catalog.py`, **28 test methods** với nhiều subtests:

| Nhóm | Methods | Phạm vi |
| --- | --- | --- |
| SupplierPhoneTests | 4 | Thiếu/rỗng/whitespace → NULL; định dạng nội địa/quốc tế; biên 9/15 digits; dấu phân cách; punctuation-only, 8/16 digits, ký tự sai, dấu + sai |
| CatalogManagementTests | 6 | CRUD Category/Brand; trùng tên trên create/edit, case/trim; giữ tên hiện tại; xóa khi đang có Product giữ cả parent/product; duplicate Supplier code và giữ code của chính nó; phone invalid qua HTTP create/edit không ghi dữ liệu |
| ProductValidationTests | 6 | Giá 0/âm bị từ chối trên create/edit, 0.01 hợp lệ; create không hiển thị/chấp nhận Category/Brand/Supplier INACTIVE; edit giữ current INACTIVE nhưng không chọn INACTIVE khác; relation bị tắt giữa GET và POST phải revalidate |
| CatalogQueryTests | 7 | Kết hợp q/status/category/brand/supplier, mỗi decoy sai đúng một filter; price asc/desc và tie ổn định; sort tên quan hệ; supplier/category/brand filter+sort; theo link phân trang giữ đầy đủ filter/sort, không mất/trùng record; sort/filter/page sai không phá list |
| CatalogAuthorizationTests | 5 | Anonymous và CUSTOMER kể cả hai nhóm CRM không quản lý catalog qua GET/POST; khóa/hạ role ADMIN với session cũ; ACTIVE ADMIN mở mọi list/create/edit; delete chỉ POST, CSRF bắt buộc, request bị từ chối không đổi dữ liệu |

Các test cũ giữ nguyên. Không mock DB hoặc dùng SQLite để thay MySQL.

## Runtime, database và lệnh

- Python 3.12.10, Django 5.2.17, mysqlclient 2.3.0, django-ninja 1.7.1, MySQL 8.4.11.
- Tạo venv riêng ở worktree fix với `--system-site-packages`, dùng các dependency đã cài trên máy. Không sửa shared venv hoặc requirements.
- `.env` hiện có được copy vào hai worktree, không in credential. Machine-local `config.local_settings` chỉ định demo `crm_tv1_demo` cho check và migration dry-run.
- Automated tests dùng **`config.test_settings` với TEST.NAME=`test_crm_db`**, riêng với demo/legacy. Trên TV2 cũ chưa có module này, copy cấu hình test hiện có từ TV1 để chạy targeted tests; bản ghép dùng file đã track trong develop, giữ nguyên nội dung.
- Đặt `DB_NAME=crm_tv1_demo` qua môi trường cho kết nối trước runner; xác minh `SELECT DATABASE()` và source `BASE_DIR` trước khi chạy. Chỉ một runner hoạt động mỗi lần, targeted TV2 xong rồi mới chạy full bản ghép.
- Không chạy migration, reset, drop, restore hay flush `crm_db` legacy; không ghi dữ liệu demo. Test fixtures chỉ nằm trên `test_crm_db`. Dòng seed output đến từ test seed trên DB test.

Targeted trên TV2:

```powershell
$env:DB_NAME = 'crm_tv1_demo'
.\venv\Scripts\python.exe manage.py test apps.catalog.test_pr4_catalog.SupplierPhoneTests --settings=config.test_settings --keepdb --noinput
.\venv\Scripts\python.exe manage.py test apps.catalog --settings=config.test_settings --keepdb --noinput
```

Trong worktree ghép thử, dùng interpreter venv của worktree fix; `manage.py`, settings và app imports đều lấy từ worktree integration đã xác minh qua `BASE_DIR`:

```powershell
$env:DB_NAME = 'crm_tv1_demo'
$env:DJANGO_SETTINGS_MODULE = 'config.local_settings'
$pythonPath = 'C:\Users\Khiem\.codex\worktrees\pr4-tv2-fix\crm_project\venv\Scripts\python.exe'
& $pythonPath manage.py check
& $pythonPath manage.py makemigrations --check --dry-run
& $pythonPath manage.py test --settings=config.test_settings --keepdb --noinput
```

| Lần chạy | Kết quả thật |
| --- | --- |
| Regression phone trước sửa | RED — 4 methods, 12 failures trong subtests, exit 1; tái hiện lỗi source |
| Toàn bộ catalog sau sửa, TV2 riêng | PASS — 41/41, 0 failures/errors, 8.656 giây |
| `check`, bản ghép | PASS — 0 issues |
| `makemigrations --check --dry-run`, bản ghép | PASS — No changes detected |
| Full suite bản ghép | PASS — 204/204, 0 failures/errors, 227.264 giây, exit 0 |
| Whitespace/source integrity | PASS — staged/unstaged diff và các file mới không có lỗi whitespace; form/tests ở hai worktree giống nhau |

Full suite gồm các regression hiện có cho admin login/UI/accounts/API, cửa hàng home/products/detail/filter/pagination, TV1 auth/profile/preferences và TV4 customer management. Các source module này được đối chiếu với develop và không bị thay đổi bởi bản ghép catalog.

## File thay đổi và trạng thái bàn giao

- Source patch để áp dụng lên TV2: `apps/catalog/forms.py` và file mới `apps/catalog/test_pr4_catalog.py`.
- Tài liệu review: báo cáo này và entry mới trong `plans.md`, trong hai worktree riêng. Không sửa tests cũ trong quá trình review; các khác biệt có sẵn ở `apps/catalog/tests.py` trong bản ghép thuộc PR TV2.
- Cấu hình local/venv chỉ phục vụ chạy kiểm thử; không đưa `.env` hay credentials vào patch. Log full suite lưu ngoài repo: `C:\Users\Khiem\.codex\tmp\pr4-tv2-review\integration_tests.log`.
- Patch gồm đúng hai file source/tests: `C:\Users\Khiem\.codex\tmp\pr4-tv2-review\pr4-catalog-fix.patch`, SHA-256 `330da7f1122a4367b13317a25a56a6e0f2454f650ec1d7a7d059c83612286296`. Hai file trong fix worktree và integration worktree đã đối chiếu giống nhau.
- Sau kiểm thử đã dùng `git merge --quit` để bỏ metadata của lần ghép thử, giữ source/index đã kiểm thử; HEAD và branch refs không đổi. Không có merge commit hoặc pending merge.
- **Bản sửa đạt điều kiện kiểm thử để bàn giao trên PR #4.** Không còn blocker kỹ thuật/môi trường trong phạm vi yêu cầu: catalog 41/41 và toàn bộ bản ghép 204/204 pass, migration dry-run không đổi schema. Head tiền sửa `2cc11b1…` có lỗi phone đã tái hiện; các kết quả pass áp dụng cho source đã sửa.

## Cập nhật PR theo yêu cầu tiếp theo của owner

- Fetch origin và xác minh lại remote TV2 vẫn là `2cc11b1ff0afeaad2ae00fe0bb1bd0cac0d1a167`, develop vẫn là `89a884b005961234b010ab7bdeb5414fc26adc99`.
- Đối chiếu form/tests với worktree integration đã chạy 204 tests và log kết quả: source không đổi sau kiểm thử; chỉ cập nhật tài liệu để bàn giao.
- Commit giới hạn đúng bốn file: `apps/catalog/forms.py`, `apps/catalog/test_pr4_catalog.py`, `docs/pr4_tv2_review.md`, `plans.md`. Đặt entry PR #4 trước phần lịch sử chung cuối file plans để không tranh vị trí append với ghi chú TV1 trên develop.
- Cấu hình machine-local `config/test_settings.py`, `.env`, `local_settings`, `venv`, patch/log và file tạm không thuộc commit.
- Bàn giao bằng push bình thường lên `feature/tv2-catalog` và cập nhật mô tả PR hiện có với 41 catalog tests, 204 full tests trên bản ghép develop `89a884b…`. Không force-push, không push develop, không approve hoặc merge.

# Bàn giao TV1 cho TV3 / TV4 / TV5

Nền develop `ee13e42`, nhánh `feature/tv1-auth-customer`; không merge nhánh thành viên.
TV1 không đổi models, migrations, SQL, backup/restore, API hay giao diện admin.

## URL và quyền

Auth mới có namespace `customer_auth`: login/register/logout, password_change,
password_reset/done/confirm/complete, crm_home. `LOGIN_URL` dùng customer_auth:login.
Tên `login`/`logout` không namespace vẫn trỏ đến admin login/logout cũ.
Shop có namespace `shop`: home (`/`), products, product_detail.
Customer namespace `customers` hiện chỉ có profile (`/account/profile/`). TV4
có thể bổ sung URL CRM riêng khi đã thống nhất contract; tránh trùng namespace.
Không nối generic profile bằng customer_id từ URL hoặc form.

ADMIN mặc định vào `/admin-portal/`; nhóm CRM_MANAGER/CUSTOMER_SERVICE vào
`/crm/`; CUSTOMER vào `/`. role_required kiểm tra Account/Groups hiện tại ở DB.
CRM home cho ACTIVE ADMIN hoặc hai nhóm CRM; không trao quyền admin account
cho CUSTOMER chỉ vì được gán nhóm. Các trang quản trị vẫn cần guard riêng.

## Model và service dùng chung

- Account/AccountManager chuẩn hóa email; password/last_login map cột SQL hiện có.
- Customer.account OneToOne, status ACTIVE/DELETED; profile chỉ dùng ACTIVE và
  deleted_at NULL. Account LOCKED khác Customer DELETED.
- CustomerPreference.customer là FK; service `update_own_profile` kiểm tra tất
  cả preference_id dưới transaction/row lock và chỉ ghi profile của actor.
- `register_customer` không nhận role/status/groups/permission; profile whitelist
  full_name/phone/date_of_birth/gender/address/playing_level.
- Không đổi FK/on_delete. Regression bao gồm rollback registration/profile và
  không làm thay đổi Customer/Preference của người khác.
- Product read-only cho TV1: ACTIVE; Category/Brand/Supplier giữ model TV2 hiện có.
  Không thêm field ảnh, giá trị tồn kho hoặc trạng thái bán khác.

Gender/playing_level/preference hiện là văn bản với max_length; chưa có enum
được chốt. TV1 không tạo bộ giá trị mới. Seed dùng CATEGORY / Badminton rackets;
TV4 cần thống nhất convention và kế hoạch dữ liệu trước khi chuyển sang choices.
Formset hiện cho cập nhật/thêm/xóa sở thích; giới hạn gửi tối đa 50 dòng, 100 form
parse; nếu báo cáo cần taxonomy cố định thì phải bàn giao quyết định riêng.

## Vị trí nối menu

`templates/layouts/base_customer.html`: products/profile/auth đã dùng reverse.
Khảo sát cá nhân đang là span “Sắp có”. TV5 chỉ thay bằng link khi có landing
thật và kiểm tra ownership/status. Không đoán recipient ID trong template.

`templates/layouts/base_crm.html`: Tổng quan dùng customer_auth:crm_home;
khách hàng/phản hồi/khảo sát là span “Sắp có”. TV4/TV5 bổ sung link route thật sau
khi backend/test quyền hoàn tất. Nội dung trang tổng quan tại
`templates/accounts/customer/crm_home.html` phải được cập nhật cùng việc nối menu.

`templates/shop/product_detail.html`: chưa có feedback submit URL trên develop,
nên feedback hiển thị “Sắp có”. TV4 nối nút theo route thật, kiểm tra Product và
Customer ở backend. Survey không có route shop theo product, không suy diễn mapping.

TV3 giữ `templates/admin_portal/*`, Account API/services hiện có. Chỉ test root
404 trước đây đổi sang 200 vì TV1 thêm homepage. Admin login guard dùng `reverse('login')`,
không phụ thuộc LOGIN_URL chung. Việc gán nhóm vẫn do quy trình quản trị có sẵn,
TV1 không cấp quyền qua register/profile.

## Kiểm thử chéo và phần chờ

TV5 kiểm thử TV1: đăng ký/login/profile/password/reset/CSRF/shop theo Chương 4.
Trước ghép nhánh, chạy toàn bộ tests trên MySQL DB riêng với config.test_settings.
Không chạy đồng thời nhiều test runner trên cùng test_crm_db.

Chờ: TV4 landing/quyền customer management/feedback/report; TV5 danh sách survey
cá nhân và CRM survey landing; TV3 hoặc chủ DB căn chỉnh live crm_db bằng quy trình
được duyệt. SMTP thật và thông tin nhóm/báo cáo phải bổ sung bằng bằng chứng.

## Demo DB và trạng thái review trước PR

Demo riêng: `crm_tv1_demo`, settings máy `config/local_settings.py` (ignored),
không dùng `crm_db` legacy và không dùng `test_crm_db` cho demo mới.
Lệnh chạy sau khi quản trị MySQL cấp quyền/tạo DB và migrations đã được áp dụng:
`python manage.py runserver 127.0.0.1:8000 --settings=config.local_settings`.
Các URLs TV1/admin giữ nguyên như bảng README. Console email chỉ dành cho local.

Lần review này MySQL CREATE DATABASE trả 1044; chưa có quyền tạo DB demo,
nên migrate và smoke test HTTP/browser trên DB demo mới vẫn BLOCKED. Source check,
migration dry-run và regression dùng DB test được ghi riêng ở plans.md; chúng không
thay bằng chứng demo. Không thay quyền DB, không reset/drop DB hiện có.
Regression trước PR: **144/144 passed trong 175.004 giây** trên MySQL 8.4.11,
check 0 lỗi và No changes detected. Draft PR giữ bước demo DB còn chờ xác minh.

## TV4 / TV5 cập nhật sau khi PR TV1 được merge

Các lệnh dưới đây là hướng dẫn cho từng thành viên **sau khi** PR đã merge;
TV1 chưa merge PR và chưa gộp nhánh thành viên trong task này.

1. Kiểm tra `git status --short`; bảo toàn WIP bằng commit trên nhánh riêng hoặc
   worktree khác. Không reset/stash/ghi đè thay đổi của người khác.
2. Cập nhật develop bằng fast-forward:

   ```powershell
   git fetch origin
   git switch develop
   git pull --ff-only origin develop
   ```

3. Chuyển về nhánh tính năng thực tế của mình, rồi merge `origin/develop` vào nhánh
   đó. Không copy/cherry-pick riêng TV1 một cách mù quáng; không push thẳng develop.
4. Review conflict ở config/urls.py, customers/views.py và hai shared layouts;
   giữ các namespace/route auth/profile hiện có. TV4 thêm management views riêng,
   không thay thế own-profile service. TV5 giữ kiểm tra recipient ownership.
5. Chạy `check`, `makemigrations --check --dry-run` và toàn bộ tests trên DB test
   riêng. TV1 không tạo migration mới; không migrate live legacy để chữa conflict.
6. Chỉ mở menu “Sắp có” sau khi route, service và guard backend đã kiểm thử. Cập
   nhật docs/tv1_handoff.md khi chốt contract mới; tạo PR của mình vào develop.

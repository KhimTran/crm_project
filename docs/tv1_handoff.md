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
- CustomerPreference.customer là FK; service `update_own_profile` chỉ ghi profile
  của actor dưới transaction/row lock, kiểm tra Category ID ACTIVE và ID dòng cũ
  được yêu cầu xóa. Không nhận customer_id để chọn hồ sơ.
- `register_customer` không nhận role/status/groups/permission; profile whitelist
  full_name/phone/date_of_birth/gender/address/playing_level.
- Không đổi FK/on_delete. Regression bao gồm rollback registration/profile và
  không làm thay đổi Customer/Preference của người khác.
- Product read-only cho TV1: ACTIVE; Category/Brand/Supplier giữ model TV2 hiện có.
  Không thêm field ảnh, giá trị tồn kho hoặc trạng thái bán khác.

### Contract form hồ sơ sau đối chiếu TV4 / TV5

Đọc bằng git show/grep, không merge/cherry-pick:
TV4 feature/tv4-models `2f0b82e2a2f974e53454f5d27ae1046e26aa11ad`
(constants/forms/services/tests); TV5 feature/tv5-surveys
`ef45cb90e5090af59c188b5ade7c5b5371f89980` (audience filter/forms/seed/tests).

| Field | Giá trị lưu / nhãn TV4 |
| --- | --- |
| gender | MALE / Nam; FEMALE / Nữ; OTHER / Khác |
| playing_level | BEGINNER / Mới chơi; RECREATIONAL / Phong trào; COMPETITIVE / Thi đấu |
| preference_type | CATEGORY, BRAND, PLAY_STYLE |
| CATEGORY preference_value | category_name, ví dụ Badminton rackets; không lưu category_id |
| BRAND preference_value | Yonex, Victor, Li-Ning, Mizuno, Kumpoo, Apacs, VNB (TV4 choices) |
| PLAY_STYLE preference_value | Tấn công, Phòng thủ, Toàn diện, Đánh đơn, Đánh đôi (TV4 choices) |

TV4 tạo BRAND/PLAY_STYLE từ chuỗi hiển thị. CATEGORY hiện được seed foundation/TV5
lưu bằng tên. TV5 lấy distinct preference_value và playing_level từ DB rồi lọc
trực tiếp theo giá trị; hiện bộ lọc sở thích không phân biệt preference_type.
TV1 giữ nguyên cách lưu này, không tự sửa logic TV5.

**Khác biệt thật:** TV5 seed dùng BEGINNER/INTERMEDIATE/ADVANCED; TV4 form dùng
BEGINNER/RECREATIONAL/COMPETITIVE. Theo yêu cầu chủ task, TV1 áp dụng dropdown TV4,
giữ INTERMEDIATE/ADVANCED hoặc giá trị cũ khác chỉ cho đúng hồ sơ đang lưu giá trị
đó (option “Đã lưu: …”). Không ánh xạ hai bộ giá trị hoặc đổi dữ liệu hàng loạt.
Trường bị bỏ khỏi payload được giữ; chọn trống rõ ràng lưu NULL. Đăng ký mới chỉ
nhận các choices TV4 hoặc trống. Models vẫn là CharField, không thêm SQL enum/CHECK.
TV5 cần cân chỉnh seed trong task riêng khi nhóm chốt tích hợp; đây là việc chờ,
không phải một mapping đã được duyệt. Phone policy TV1 vẫn giữ nguyên phạm vi cũ.

**POST hồ sơ mới:** categories là danh sách Category ID ACTIVE; remove_preferences
là danh sách preference_id của riêng CATEGORY cũ không khớp tên ACTIVE thuộc actor.
Không còn formset hay input preference_type/preference_value. Backend tự đặt CATEGORY.
`update_own_profile(actor, profile_data=..., category_ids=...,
remove_preference_ids=...)` thay signature TV1 formset cũ; không thay TV4 services.
Chỉ đồng bộ tên danh mục ACTIVE: thêm lựa chọn mới, bỏ lựa chọn đã bỏ chọn, gộp
dòng trùng cho cùng tên. Hai Category trùng tên vẫn chỉ lưu một preference_value.
Việc đổi tên/tắt danh mục làm tên cũ thành dữ liệu giữ lại, không tự đổi sang tên mới.
Không có Category ACTIVE thì hiển thị trạng thái trống và giữ dữ liệu cũ.
BRAND/PLAY_STYLE/loại khác hiển thị chỉ đọc và không bị sửa/xóa bởi flow này.
Mọi validation và sync/profile save chạy atomic, khóa actor/profile/preferences
và Category ACTIVE; service revalidate khi danh mục bị tắt sau khi form đã được kiểm tra.

TV1 dùng adapter self_service_choices.py theo đúng giá trị TV4 để tránh ghi đè
constants.py thuộc TV4. Khi tích hợp, đề xuất thống nhất import từ một nguồn choices
cùng nhóm; không tự merge/cherry-pick nhánh hoặc thay đổi contract trong task này.

Xác minh revision cải thiện: check 0 lỗi, No changes detected;
47/47 tests liên quan pass trong 50.937 giây trên MySQL test_crm_db.
26 kiểm tra HTTP/demo pass trên crm_tv1_demo, gồm gọi các hàm lọc audience TV5
đọc từ đúng ref trên dữ liệu TV1 mới (không chạy/merge toàn bộ module TV5).
Browser lưu hồ sơ thành công, desktop/390px không tràn ngang, checkbox chuyển từ
hai cột sang một cột. CTA shop có computed color trắng ở normal/hover/focus-visible.
Admin login/accounts/catalog vẫn hoạt động; không đổi template/CSS/logic admin TV3.

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
đặt `$env:PYTHONIOENCODING='utf-8'` trên Windows trước lệnh
`python manage.py runserver 127.0.0.1:8000 --settings=config.local_settings`.
Các URLs TV1/admin giữ nguyên như bảng README. Console email chỉ dành cho local.

MySQL CREATE DATABASE ban đầu trả 1044. Chủ máy sau đó cấp quyền và tạo database
rỗng; đã review plan, apply migrations và check thành công trên `crm_tv1_demo`.
MySQL 8.4.11, utf8mb4/utf8mb4_unicode_ci; 23 bảng gồm 14 bảng nghiệp vụ.
Fixtures giả lập được giữ lại: 5 Account, 2 Customer, 14 sản phẩm ACTIVE, 1 INACTIVE.
Không sao chép dữ liệu từ DB chung và không reset/drop database hiện có.
Regression trước PR: **144/144 passed trong 175.004 giây** trên MySQL 8.4.11,
check 0 lỗi và No changes detected. Demo riêng: **42 kiểm tra HTTP pass** cho
auth, CSRF/quyền/LOCKED/session, profile/preferences/ownership, đổi/reset mật khẩu,
shop/lọc/phân trang/404 và admin account/catalog/Django admin.
Browser đã xác minh shop/profile/CRM và đăng nhập/admin account list/catalog.
Console reset tiếng Việt cần UTF-8 trên Windows; đã sửa cấu hình tiến trình và
chạy lại reset thành công. SMTP thật chưa kiểm chứng. Credentials/script/log/ảnh
demo nằm ngoài repo; không chia sẻ password hoặc reset token trong báo cáo.
PR [#3](https://github.com/KhimTran/crm_project/pull/3) vào develop; chưa merge.

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

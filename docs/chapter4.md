# Chương 4 — Triển khai, kiểm thử và hướng dẫn sử dụng

Người biên soạn: [Họ tên — MSSV]. Lớp: [Lớp]. Giảng viên: [Họ tên].
Revision nền: develop `ee13e42`; nhánh triển khai: `feature/tv1-auth-customer`.
Nội dung này phản ánh code TV1; không xác nhận tên/MSSV, đóng góp cá nhân của
thành viên khác, kết quả khảo sát thực tế hoặc chức năng chưa tích hợp.

## 4.1. Môi trường triển khai

Backend Django 5.2.17, Python 3.12, MySQL 8.x với mysqlclient 2.3.0.
Giao diện Django Templates; Bootstrap 5.3.3 CSS lưu cục bộ và CSS hai layout.
Không thêm frontend framework, DRF hoặc schema mới cho UI.
MySQL thực tế của lần kiểm thử: 8.4.11, trên database riêng test_crm_db.

Database nghiệp vụ `crm_db`, charset utf8mb4; Account dùng email làm định danh,
password và last_login của Django map vào password_hash và last_login_at.
Customer dùng account OneToOne; CustomerPreference tham chiếu Customer;
Product tham chiếu Category/Brand/Supplier. PK/FK/migrations giữ nguyên.
Email Account bất biến; role ADMIN/CUSTOMER; trạng thái ACTIVE/LOCKED.
CRM_MANAGER/CUSTOMER_SERVICE là Groups, không phải role mới.

## 4.2. Cài đặt

1. Lấy revision đã review, tạo virtualenv và cài `requirements.txt`.
2. Sao chép `.env.example` thành `.env`, điền SECRET_KEY, ALLOWED_HOSTS và MySQL.
3. Kiểm tra `check`, `showmigrations`, `migrate --plan` trước khi khởi tạo dữ liệu.
4. Chỉ chạy migrate trên DB mới/rỗng được giao cho phát triển theo người phụ trách.
   Với DB đã có dữ liệu hoặc schema legacy, cần kế hoạch căn chỉnh và backup riêng.
5. Cấu hình console email cho demo hoặc SMTP thật cho triển khai.
6. Chạy `python manage.py runserver`, dùng cùng hostname cho toàn bộ phiên.

Lần thực hiện TV1 không migrate/seed/flush/restore live DB. Live crm_db tại máy
khảo sát còn schema legacy; không thể dùng kết quả source check thay bằng chứng
demo trên live. Test runner áp dụng migrations thật lên test_crm_db riêng.

## 4.3. Các luồng TV1 đã triển khai

**Đăng nhập/đăng xuất.** Form `/login/` chuẩn hóa email bằng AccountManager,
xác thực qua Django backend và tạo session. Với tài khoản bị khóa, thông báo khóa
chỉ xuất hiện sau kiểm tra mật khẩu đúng; sai mật khẩu dùng thông báo chung.
Đích mặc định ADMIN là Admin Portal, người thuộc nhóm CRM là `/crm/`, khách hàng
là `/`. `next` bị giới hạn bởi host, route có thật, quyền và allowlist GET.
Đăng xuất dùng POST có CSRF. Admin login riêng vẫn giữ nguyên.

**Đăng ký.** Form `/register/` nhận email, mật khẩu/nhập lại và hồ sơ.
Password validators và manager thực hiện hashing; service tạo Account CUSTOMER
ACTIVE và Customer ACTIVE trong transaction. Duplicate/race email được trả vào
lỗi email; lỗi tạo hồ sơ rollback tài khoản. Role/status/groups không nhận từ form.

**Hồ sơ và sở thích.** `/account/profile/` chỉ nhận Customer ACTIVE gắn với
Account CUSTOMER đang hoạt động. ID không quyết định chủ thể sửa; account/email/
role/status/quyền không writable. Checkbox lấy Category ACTIVE, gửi ID để backend
xác minh và lưu CATEGORY/tên danh mục. Lưu atomic riêng sở thích danh mục, không
tạo trùng; dữ liệu cũ không khớp chỉ xóa khi khách chọn rõ ràng. BRAND/PLAY_STYLE
giữ nguyên. Giới tính/trình độ dùng dropdown nhãn tiếng Việt theo TV4; dữ liệu cũ
ngoài choices được giữ trong option riêng, không chuyển đổi hàng loạt.

**Mật khẩu.** Đổi mật khẩu yêu cầu mật khẩu cũ; giữ phiên đang thao tác bằng
update_session_auth_hash và vô hiệu phiên khác. Reset dùng PasswordResetView,
PasswordResetTokenGenerator và PasswordResetConfirmView của Django, thời hạn
1 giờ, không tự đăng nhập và không gửi mật khẩu thô. Lọc Account ACTIVE thay cho
is_active ORM vì đó là property. Reset kiểm tra lại token/status dưới row lock
trước khi ghi. Phản hồi yêu cầu giống nhau cho email không tồn tại/bị khóa.

**Cửa hàng.** `/` giới thiệu sản phẩm đang bán; `/products/` hỗ trợ tên, danh mục,
thương hiệu và khoảng giá Decimal, 12 dòng/trang, giữ tham số. Product ACTIVE
được hiển thị; chi tiết INACTIVE/không có trả 404. Không thêm ảnh/tồn kho/thông số
vào DB; dùng placeholder SVG cục bộ. Lỗi bộ lọc trả 400 và chỉ rõ trường lỗi.

**CRM.** `/crm/` dùng layout CRM, bảo vệ bằng role_required; ADMIN hoặc hai nhóm
CRM được vào. Các module khách hàng/phản hồi/khảo sát chưa có landing chung phù
hợp vẫn hiển thị “Sắp có”, không có link giả.

## 4.4. Kiểm thử

Kiểm thử Django TestCase trên MySQL test_crm_db tách khỏi live. Email dùng locmem;
SMTP thật chưa kiểm chứng. Lệnh tái hiện:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.customers.test_self_services --settings=config.test_settings --keepdb --noinput
python manage.py test --settings=config.test_settings --keepdb --noinput
```

| Nhóm | Nội dung xác minh |
| --- | --- |
| Registration | Normalize/hash, duplicate, mật khẩu yếu, rollback, không nâng quyền |
| Authorization | Role/group routing, CRM guard, revoke group, khóa session cũ, admin regression |
| Profile | Ownership, ID giả/INACTIVE, whitelist, checkbox, bảo toàn dữ liệu cũ và rollback |
| Password | Mật khẩu cũ/mới, xác nhận, giữ/vô hiệu session, reset token hết hạn/đã dùng/bị khóa |
| CSRF | Login/register/logout/profile/change/reset và reset confirm |
| Shop | ACTIVE, lọc kết hợp, giá sai, phân trang giữ query, 404, static cục bộ |
| Regression | Accounts API/session, admin, catalog, surveys hiện có |

Kết quả 2026-10-08: check 0 lỗi, không có migration mới; 7/7 test service và
144/144 test toàn repo thành công trên MySQL 8.4.11. Đã xem login/register,
shop/detail, hồ sơ và CRM bằng browser trên server tạm dùng DB test; layout
product/CRM được kiểm tra ở chiều rộng 390px. Verification Log TV1 ở plans.md
ghi lệnh, lỗi test ban đầu đã sửa và giới hạn live DB/SMTP.
Ảnh minh họa: [Chèn ảnh chụp revision đã bàn giao].

## 4.5. Kịch bản demo

1. Kiểm tra DB đã khớp models; khởi động server và mở cửa hàng.
2. Lọc sản phẩm theo category/brand/price, chuyển trang và mở chi tiết.
3. Đăng ký email mới, thử email trùng và mật khẩu sai chính sách.
4. Đăng nhập, sửa hồ sơ, chọn/bỏ chọn nhiều danh mục, kiểm tra dữ liệu cũ được giữ
   và chỉ xóa khi đánh dấu; email chỉ đọc, giới tính/trình độ có dropdown.
5. Đổi mật khẩu; dùng phiên thứ hai xác minh bị yêu cầu đăng nhập lại.
6. Đăng xuất; yêu cầu reset, lấy console link, đặt mật khẩu mới và thử lại token cũ.
7. Đăng nhập Account có nhóm CRM được cấp sẵn; quan sát menu “Sắp có”.
8. Đăng nhập ADMIN; kiểm tra Admin Portal và API hiện có.

Không cần chạy seed hay sửa quyền qua UI TV1. Không ghi mật khẩu/console token
vào ảnh báo cáo. Danh sách account demo: [Email — quyền, không ghi password].

## 4.6. Giới hạn và hướng tích hợp

Chưa triển khai feedback/survey/report thay TV4/TV5. Route làm khảo sát theo
recipient đã tồn tại trong develop nhưng chưa có danh sách khảo sát cá nhân để
nối menu chung; không đoán recipient ID hay thêm logic gửi khảo sát.
SMTP, enum profile/preference và live database alignment cần người phụ trách
xác minh/chốt riêng. Kế hoạch 15 tuần là đề xuất, không khẳng định đã hoàn thành.
Contract bàn giao URL/layout/model/quyền chi tiết nằm trong tv1_handoff.md.

## 4.7. Review và chuẩn bị PR

Đã review toàn bộ source diff, tests, templates, static/vendor và tài liệu của
TV1. Không đổi model/migration/SQL/API hay UI quản trị. Secret thực tế từ .env,
private-key/token patterns và đường dẫn máy được kiểm tra trước stage; chỉ source,
tests và tài liệu hợp lệ được đưa vào commit. .env/config/local_settings.py,
backup, ảnh/log/script review cục bộ nằm ngoài commit.

Database demo được chỉ định là `crm_tv1_demo`; cấu hình local_settings không commit.
Lỗi quyền 1044 ban đầu được giải quyết sau khi chủ máy cấp quyền và tạo DB rỗng.
Đã review plan, apply migrations hiện có và check 0 lỗi trên DB riêng này:
MySQL 8.4.11, utf8mb4/utf8mb4_unicode_ci, 23 bảng vật lý (14 bảng nghiệp vụ).
Fixtures giả lập: 5 Account, 2 Customer, 14 sản phẩm ACTIVE và 1 INACTIVE.
Server demo dùng `http://127.0.0.1:8000`; các URLs theo bảng README.

**42 kiểm tra HTTP đã pass**: đăng ký/trùng email/login khách hàng/CRM/admin,
CSRF/whitelist/ownership/LOCKED/session, cập nhật hồ sơ/sở thích, đổi/reset mật khẩu
và token, shop/lọc/phân trang/404, account list/detail/catalog và Django admin.
Browser đã xác minh giao diện shop, profile, CRM, login/admin accounts và catalog.
Console email ban đầu lỗi mã hóa tiếng Việt khi ghi log Windows; thiết lập
PYTHONIOENCODING=utf-8 cho tiến trình demo và chạy lại reset thành công.
README/handoff đã ghi bước này. SMTP thật chưa kiểm chứng; credentials/log/token/
ảnh/script cục bộ nằm ngoài commit. Không thay đổi crm_db legacy.

PR vào develop được người dùng cho phép; không merge PR, không gộp nhánh TV2/TV4/TV5.
Thông tin commit/PR và kết quả test cuối cùng ghi trong Verification Log/PR.
Lần regression trước PR: 144/144 tests passed trong 175.004 giây trên MySQL 8.4.11;
source check 0 lỗi, migration dry-run No changes detected.
PR [#3](https://github.com/KhimTran/crm_project/pull/3) được tạo draft khi thiếu quyền;
sau khi hoàn tất demo, chuyển sang sẵn sàng review. Chưa merge PR.

## 4.8. Cải thiện giao diện hồ sơ và contract TV4/TV5

Đối chiếu TV4 2f0b82e và TV5 ef45cb9 bằng git show/grep. TV4 gender:
MALE/FEMALE/OTHER; playing_level: BEGINNER/RECREATIONAL/COMPETITIVE. TV5 seed còn
INTERMEDIATE/ADVANCED; không coi chúng tương đương bộ TV4. Form mới dùng TV4 theo
yêu cầu, giữ giá trị cũ và chỉ đổi khi khách chọn lại. CATEGORY lưu category_name,
không đổi sang ID; TV5 vẫn lọc được bằng preference_value và playing_level.
Chi tiết giá trị và signature service trong docs/tv1_handoff.md.

47/47 tests liên quan pass trong 50.937 giây trên test_crm_db. Check 0 lỗi,
không có migration mới. 26 kiểm tra HTTP/demo mới pass trên crm_tv1_demo:
nhiều danh mục/bỏ chọn/lưu lặp, dữ liệu cũ/BRAND/PLAY_STYLE được giữ, xóa chủ động,
category_id giả/INACTIVE/ownership bị từ chối, enum/dropdown cũ và admin regression.
Đã chạy các hàm lọc TV5 trên dữ liệu demo vừa lưu; đây là kiểm chứng contract có
phạm vi, không phải test toàn bộ nhánh TV5. Browser xác minh desktop/390px,
không tràn ngang, CTA chữ trắng ở normal/hover/focus. Ảnh và credentials chỉ lưu
cục bộ ngoài repo; không đổi schema, crm_db legacy hoặc UI quản trị TV3.

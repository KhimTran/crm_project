# Roadmap TV4 – CRM: khách hàng, phản hồi, báo cáo KH

Nguồn: `01_Phan_cong_cong_viec_EN_DB.docx`, `02_Huong_dan_do_an_EN_DB.docx`, đối chiếu `AGENTS.md` và code hiện có.

## 1. Phạm vi TV4

| Mã | Chức năng | Điểm gắn với |
|---|---|---|
| 4.1.1 | Thêm khách hàng (tạo hồ sơ + tài khoản, mật khẩu tạm) | III.4.1 |
| 4.1.2 | Xóa khách hàng (xác nhận, cảnh báo dữ liệu liên quan) | III.4.1 |
| 4.1.3 | Khóa / mở khóa tài khoản khách hàng | III.4.1 |
| 4.1.4 | Tiếp nhận phản hồi (xem, lọc, xử lý, trả lời) | III.4.1 |
| 4.2.4 | Khách gửi phản hồi về sản phẩm, xem lại câu trả lời | III.4.2 |
| 4.1.5 | Báo cáo KH: nhóm tuổi, sở thích, trình độ, giới tính, KH mới theo tháng (Chart.js, in) | III.4.1 |

- **Bảng CSDL:** `customers`, `customer_preferences`, `feedbacks`.
- **Báo cáo:** Chương 2 – mô tả bài toán, BFD, sơ đồ ngữ cảnh (draw.io → PNG). Ngoài ra: ảnh chụp + mô tả giao diện (Ch.3b) và hướng dẫn sử dụng (Ch.4) cho chức năng của mình.
- **Điểm:** I.2 (6đ), 4.1 (≈11đ), 4.2 (≈2đ).
- **Phối hợp:** TV1 kiểm thử chéo phần TV4; TV4 kiểm thử chéo phần TV3; TV5 dùng lại bộ lọc KH để gửi khảo sát; chốt tên BFD ↔ DFD ↔ ERD cùng TV3, TV5.

## 2. Hiện trạng repo

- Đã có: model `Customer`, `CustomerPreference`, `Feedback` + migration 0001; `role_required` (`CRM_MANAGER`, `CUSTOMER_SERVICE`, `CUSTOMER`); layout `base_crm.html`, `base_customer.html`.
- Chưa có: `urls.py`, `forms.py`, `services.py`, `selectors.py`, view, template, test, seed cho `customers` / `feedback`. Menu CRM đang `href="#"`.

## 3. Khác biệt giữa file Word và schema thật (làm theo schema)

| File Word | Làm theo schema |
|---|---|
| `is_active`, `lock_reason`, `locked_at` | Khóa = `accounts.status='LOCKED'`. Không có cột lý do/ngày khóa, không tự thêm cột; ngày khóa lấy `updated_at`. Cần cột thì hỏi TV3. |
| Xóa cứng KH | Xóa mềm: `customers.status='DELETED'` + `deleted_at`, đồng thời khóa account (FK `feedbacks.customer_id` là RESTRICT). |
| `interests`, `customer_interests` | `customer_preferences(preference_type, preference_value)`; type: `PLAY_STYLE`, `BRAND`, `CATEGORY`. |
| `feedbacks.type/reply/handled_at/submitted_at` | Không có `type`; trả lời ở `manager_note`; `handled_by`, `resolved_at`, `created_at`. Status `NEW/IN_PROGRESS/RESOLVED`. |
| `birth_date`, `skill_level`, `customer_code` | `date_of_birth`, `playing_level` (`BEGINNER/RECREATIONAL/COMPETITIVE`); mã KH hiển thị `KH{customer_id:04d}`. |
| URL tiếng Việt | URL/identifier tiếng Anh: `/crm/customers/`, `/crm/feedbacks/`, `/crm/reports/customers/`, `/feedbacks/`. |

## 4. Lộ trình theo tuần

Hôm nay 05/10/2026 = tuần 5. Code freeze cuối tuần 8 (01/11); chấm tuần 10–11.

| Tuần | Ngày | Việc code | Việc báo cáo |
|---|---|---|---|
| T5 | 05/10–11/10 | Bước 0 + Bước 1: thêm / xóa / khóa KH, danh sách, chi tiết | Hoàn thiện Ch.2 bản nháp (bài toán, BFD, ngữ cảnh) |
| T6 | 12/10–18/10 | Bước 2: KH gửi phản hồi; quản lý tiếp nhận, trả lời; badge menu | – |
| T7 | 19/10–25/10 | Bước 3 + 4: báo cáo KH, seed 40 KH / 30 phản hồi | – |
| T8 | 26/10–01/11 | Bước 5: test, PR, kiểm thử chéo (TV1 test phần mình, mình test TV3); **CODE FREEZE** | – |
| T9 | 02/11–08/11 | Chỉ sửa lỗi | Hoàn thiện Ch.2; chụp màn hình, mô tả giao diện, HDSD; kịch bản demo |
| T10–11 | 09/11–22/11 | Demo: KH, phản hồi, báo cáo | – |
| T12–14 | 23/11–13/12 | Sửa theo góp ý, kiểm thử hồi quy | Rà soát Ch.2 |
| T15 | 14/12–20/12 | – | Tự đánh giá, chốt % đóng góp |

## 5. Các bước code

### Bước 0 – Chuẩn bị (T5)
1. `git checkout develop && git pull`; tách nhánh nhỏ: `feature/tv4-customer-management`, `feature/tv4-feedback`, `feature/tv4-customer-report`. Xóa nhánh gõ nhầm `feature/tb4-models`.
2. 🟡 Thêm `TextChoices` (`apps/customers/constants.py`, `apps/feedback/constants.py`) cho `Customer.status`, `playing_level`, `gender`, `Feedback.status` – chỉ thêm `choices`, không đổi cột. Chạy `makemigrations --check --dry-run`. *(Xong phần customers: `CustomerStatus`, `Gender`, `PlayingLevel`, `PreferenceType` + danh sách lối chơi/thương hiệu; còn `Feedback.status`.)*
3. Họp TV3, TV5 chốt tên chức năng / kho dữ liệu / bảng.

### Bước 1 – Quản lý khách hàng (T5)
Tạo `forms.py`, `services.py`, `selectors.py`, `urls.py`, `templates/customers/…`; thêm `path("crm/customers/", include("apps.customers.urls"))` vào `config/urls.py`.
- 🟡 **Danh sách** `/crm/customers/`: tìm theo tên / SĐT / email; lọc theo nhóm tuổi, giới tính, trình độ, sở thích, trạng thái account; phân trang 10. Viết `filter_customers(qs, params)` trong `selectors.py` để **TV5 dùng lại**. *(Xong: tìm kiếm, phân trang, ẩn KH đã xóa, link menu. Còn: bộ lọc + `selectors.py`.)*
- ✅ **4.1.1 Thêm** `/crm/customers/new/`: `create_customer()` trong `transaction.atomic()` – kiểm tra trùng email / SĐT → tạo Account role `CUSTOMER` (mật khẩu tạm `secrets.token_urlsafe`, hiện 1 lần) → tạo Customer + CustomerPreference.
- ✅ **4.1.2 Xóa** `/crm/customers/<id>/delete/`: GET = trang xác nhận kèm số phản hồi / khảo sát liên quan; POST = xóa mềm + khóa account. Nút xóa ẩn bằng `perms.customers.delete_customer`; view kiểm tra `has_perm` (CSKH không được xóa). *(Chặn CSKH bằng `@role_required("CRM_MANAGER")` vì TV3 chưa gán permission cho Group; khi có thể thêm `has_perm`.)*
- ✅ **4.1.3 Khóa / mở** `/crm/customers/<id>/lock/`, `/unlock/` (POST): đổi `account.status`, không khóa KH đã xóa. KH bị khóa đăng nhập phải thấy "Tài khoản đã bị khóa" (phối hợp TV1). *(Xong phía TV4: khóa chặn đăng nhập + cắt phiên đang mở. Còn chờ TV1: câu báo "Tài khoản đã bị khóa" ở trang đăng nhập.)*
- **Chi tiết** `/crm/customers/<id>/`: thông tin, sở thích, lịch sử phản hồi.

### Bước 2 – Phản hồi (T6)
- **4.2.4 Phía KH** (`@role_required("CUSTOMER")`): `/feedbacks/new/?product=<id>` (sản phẩm, 1–5 sao, nội dung → `NEW`); `/feedbacks/mine/` (lịch sử + `manager_note` + trạng thái). TV1 đặt nút "Gửi phản hồi" ở trang chi tiết sản phẩm trỏ tới URL này.
- **4.1.4 Phía quản lý** `/crm/feedbacks/` (`CRM_MANAGER`, `CUSTOMER_SERVICE`): lọc theo trạng thái, sản phẩm, số sao, khoảng ngày; xem chi tiết; cập nhật trạng thái + trả lời → `handled_by=request.user`, `resolved_at` khi `RESOLVED`.
- **Badge** phản hồi `NEW` trên menu: `apps/feedback/context_processors.py` (đăng ký trong settings – báo TV1) và gắn URL thật vào `base_crm.html`.

### Bước 3 – Báo cáo KH (T7)
- `apps/customers/reports.py`: nhóm tuổi (`<18, 18–24, 25–34, 35–44, 45–54, ≥55`, dùng `date_of_birth`), sở thích (group theo type/value), trình độ, giới tính, KH mới theo tháng (`TruncMonth(created_at)`), điểm hài lòng TB theo sản phẩm (`Avg("rating")`).
- Template `/crm/reports/customers/`: mỗi chỉ tiêu 1 biểu đồ Chart.js + bảng số liệu, dữ liệu truyền bằng `json_script`; nút In (`window.print()` + `@media print`).
- Chart.js **bản offline** tại `static/js/chart.umd.min.js`.

### Bước 4 – Dữ liệu demo (T7)
`seed_customers()` / `seed_feedbacks()` cho TV3 gọi trong `seed_data`: ≥ 40 KH (`kh01…kh40`, `Khach@123`, kh40 bị khóa), tên Việt, đủ nhóm tuổi / trình độ / sở thích, `created_at` rải 6–12 tháng; ≥ 30 phản hồi về vợt / giày / cầu ở cả 3 trạng thái, một số đã có `manager_note`. Idempotent.

### Bước 5 – Test & PR (T8)
- Test trong `apps/customers/tests/`, `apps/feedback/tests/` (theo kiểu `apps/accounts/tests/`): trùng email / SĐT; xóa mềm + cảnh báo; khóa → login bị chặn, mở lại được; CSKH không xóa được KH; KH chỉ thấy phản hồi của mình; `status` / `handled_by` / `resolved_at` đúng; số liệu nhóm tuổi.
- Commit nhỏ: `feat(tv4): add customer lock and unlock` → PR vào `develop` → TV1 test chéo. Không đẩy thẳng `main`.

## 6. Phần báo cáo

1. **Ch.2 – Mô tả bài toán:** quy trình tiếp nhận KH (tự đăng ký / quản lý thêm), khóa – xóa, xử lý phản hồi (NEW → IN_PROGRESS → RESOLVED), khảo sát, báo cáo; vai trò Admin / Quản lý CRM / CSKH / KH.
2. **BFD:** 6 nhánh – Quản trị hệ thống, Quản lý danh mục, Quản lý KH, Quản lý phản hồi, Quản lý khảo sát, Báo cáo thống kê.
3. **Sơ đồ ngữ cảnh:** 1 tiến trình "Hệ thống CRM Shop cầu lông X", 4 tác nhân (Khách hàng, Quản lý CRM, Admin, Ban giám đốc); gửi TV5 để DFD khớp luồng vào/ra.
4. **Ch.3b + Ch.4:** chụp màn hình từng chức năng 4.1.1–4.1.5, 4.2.4; mô tả giao diện; HDSD từng bước → gửi TV1 tổng hợp.
5. Mỗi mục ghi "Người thực hiện: TV4".

## 7. Kiểm tra hoàn thành

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py test apps.customers apps.feedback`
- Demo theo kịch bản: KH vào chi tiết vợt → gửi phản hồi → quản lý trả lời → KH thấy câu trả lời; quản lý thêm KH, khóa KH → KH đăng nhập bị chặn; xem báo cáo tuổi / sở thích và in; đăng nhập `cskh01` thấy nút Xóa KH bị ẩn.

## 8. Checklist bàn giao

- [x] 4.1.1 Thêm KH – 11 test `apps.customers` pass, toàn bộ 125 test dự án pass, smoke test trên server thật (`crm_dev`) ổn (05/10/2026)
- [x] 4.1.2 Xóa KH – xóa mềm + khóa account, trang xác nhận có cảnh báo số phản hồi/khảo sát; test pass, smoke test `crm_dev` ổn (05/10/2026)
- [x] 4.1.3 Khóa / mở KH – có lý do trong thông báo, khóa chặn đăng nhập và cắt phiên; 23 test `apps.customers` + 137 test toàn dự án pass (05/10/2026)
- [ ] 4.1.4 Tiếp nhận phản hồi
- [ ] 4.2.4 KH gửi phản hồi
- [ ] 4.1.5 Báo cáo KH (Chart.js offline, nút in)
- [ ] Seed ≥ 40 KH, ≥ 30 phản hồi đủ 3 trạng thái
- [ ] Test pass, PR được TV1 kiểm thử chéo
- [ ] Đã kiểm thử chéo phần TV3
- [ ] Bộ lọc KH đã bàn giao cho TV5
- [ ] Ch.2: mô tả bài toán, BFD, sơ đồ ngữ cảnh
- [ ] Ảnh chụp, mô tả giao diện, HDSD các chức năng TV4
- [ ] Bảng tự đánh giá của TV4

## 9. Rủi ro / việc cần hỏi

- Muốn lưu lý do và ngày khóa tài khoản → cần TV3 / chủ đồ án duyệt thêm cột (hiện schema không có).
- Chính sách xóa KH (xóa mềm) cần thống nhất với TV3 và ghi vào báo cáo.
- Thêm context processor vào `settings.py`, gắn URL vào `config/urls.py` và `base_crm.html` là file chung → báo TV1 trước.
- Trễ hạn quá 3 ngày phải báo nhóm; không âm thầm làm hộ nhau.

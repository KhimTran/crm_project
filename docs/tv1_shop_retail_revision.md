# TV1 — bản cửa hàng gọn, 2026-10-12

## Trạng thái bàn giao

- Nhánh: `feature/tv1-shop-redesign`, worktree
  `C:/Users/Khiem/.codex/worktrees/44c0/crm_project`.
- Trước sửa: tree sạch, HEAD `d22c43f`. Đã tạo annotated tag cục bộ
  `checkpoint/tv1-shop-before-retail-20261012` tại HEAD để đối chiếu/quay lại.
- Bản sửa lần này để ở working tree, chưa commit thêm, push, PR hoặc merge.
- Hai ảnh người dùng nhắc tới không xuất hiện trong tin nhắn công cụ nhận được;
  triển khai theo mô tả chi tiết và các website tham khảo.

## Hướng bố cục và phạm vi

Tham khảo trực tiếp [VNB](https://shopvnb.com/),
[danh sách vợt VNB](https://shopvnb.com/vot-cau-long.html),
[FBShop](https://fbshop.vn/) và
[danh sách vợt FBShop](https://fbshop.vn/vot-cau-long/).
Ưu tiên tìm kiếm, danh mục, bộ lọc riêng và tên/giá sát nhau; chỉ học cách tổ chức
thông tin. Không sao chép logo, nội dung, ảnh, mã nguồn hoặc các chức năng thương
mại của họ. Không tuyên bố đo chính xác pixel của website tham khảo.

- Header còn hàng tên/tìm kiếm/tài khoản và một hàng điều hướng kèm menu danh mục.
  Category ACTIVE luôn lấy từ DB; toàn bộ tên dài vẫn hiện trong menu và trang chủ.
- Banner chữ đơn giản cao 140px ở desktop; không dùng khẩu hiệu cỡ lớn, hình vợt,
  vòng tròn hoặc khối trang trí cuối trang. Mobile banner xếp dọc theo nội dung.
- Heading trực tiếp; card bỏ dòng danh mục lặp lại, mũi tên, đường kẻ nội bộ và bóng
  đổ. Desktop 1366/1440 có 4 cột; mobile 390 có 2 cột. Tên 16px desktop/15px mobile,
  hãng và liên kết 14px, giá 18px/17px; font Arial/Segoe UI hệ thống hỗ trợ tiếng Việt.
- Listing giữ sidebar, mobile filter đóng mặc định và tự mở khi có lỗi.
  Giữ nguyên q/category/brand/min_price/max_price, thứ tự, 12 sản phẩm/trang,
  query pagination và validation. Trang chủ vẫn lấy 8 sản phẩm theo selector cũ.
- Detail có breadcrumb, khu vực ảnh, tên/giá, hãng/danh mục, mô tả và link thật.
  Product ACTIVE thuộc Category INACTIVE vẫn giữ hành vi hiển thị cũ và tránh link
  vào bộ lọc danh mục không hợp lệ.
- Login/register/password-change dùng form gọn; profile/reset nhận cùng CSS
  khách hàng. Giữ form names, action, CSRF, next, errors và phân quyền.
- CSS chỉ dưới `.customer-layout`; không đổi Admin/CRM, backend nghiệp vụ,
  model/migration/SQL/URL/config/seed hoặc dependencies.

## Ảnh và dữ liệu

Product hiện không có cơ chế ảnh (không ImageField, FileField, URL ảnh); không có
thư mục media chứa ảnh. Bản trước chỉ có SVG minh họa tự tạo. Lần này xóa helper
đoán ảnh theo tên danh mục và dùng `product-image-unavailable.svg`, biểu tượng
ảnh trung tính tự tạo, với nhãn “Chưa có ảnh”. Không ánh xạ theo ID/tên hãng/model.
SVG cũ được giữ như asset lịch sử nhưng không còn được customer templates gọi.

Không cập nhật/seed/reset/migrate `crm_tv1_demo`; không đổi tên, ẩn bằng CSS hoặc
lọc theo tiền tố Demo/PR2. Không thêm ảnh giả model, giỏ hàng, thanh toán, khuyến
mãi, đánh giá, tồn kho, hotline, địa chỉ hoặc chính sách.

TV1/TV2 cần chuẩn bị riêng:

1. Tên danh mục chính thức và quyết định với các danh mục kiểm thử.
2. Tên thương hiệu chính thức, quan hệ thương hiệu với từng sản phẩm.
3. Tên sản phẩm/model, mô tả và giá thực tế; quyết định dữ liệu demo nào giữ lại.
4. Ảnh đúng từng model/biến thể, có quyền sử dụng và nguồn rõ ràng. Cơ chế lưu/upload
   ảnh cần được duyệt ở task riêng; không thêm cột hoặc migration trong bản giao diện.

## Kiểm chứng đã chạy ở lần sửa này

```powershell
D:/Python312/python.exe manage.py check --settings=config.local_settings
D:/Python312/python.exe manage.py makemigrations --check --dry-run --settings=config.local_settings
D:/Python312/python.exe manage.py test apps.shop apps.accounts.tests.test_layouts apps.accounts.tests.test_customer_auth apps.customers.test_profile_views apps.customers.test_self_services apps.admin_portal --settings=config.test_settings --keepdb --noinput
git diff --check
```

- Check: 0 issues; migration dry-run: No changes detected.
- **62/62 tests pass**, 51.576s, MySQL **test_crm_db**, không dùng crm_tv1_demo.
  Bao gồm regression giữ nguyên/tìm được tên Demo/PR2. Không chạy lại full suite
  ở lượt sửa này; số full suite trong tài liệu bản trước thuộc lần trước.
- Browser ở zoom 100% (Ctrl+0, visualViewport.scale=1), viewport 1440×900,
  1366×900, 390×844. Home/list không tràn ngang; 4/2 cột đúng như trên.
- GET header search “Demo Racket 13” trả 1 sản phẩm; tìm từ không tồn tại hiển thị
  trạng thái rỗng. Lọc Demo Rackets + Demo Brand + 100000–1500000 trả 14 sản phẩm;
  trang 2 giữ các tham số và trả Demo Racket 13/14. Detail giữ giá 1.300.000 ₫.
- Menu danh mục đầy đủ tên DB, không tràn ở 390px; Escape đóng và trả focus về
  summary, có outline. Tài khoản đóng/mở và các link hoạt động.
- Lỗi min_price > max_price có thông báo và filter tự mở trên mobile.
- Login sai/đúng, profile field error/save/category checkbox/success message/logout
  kiểm tra bằng tài khoản tổng hợp trên server tạm 8002, DB test_crm_db, cookie
  session/CSRF riêng. Login/register/profile desktop/mobile không tràn ngang.
  Không đăng ký tài khoản mới bằng browser; backend registration được suite kiểm tra.
- Admin login và account list kiểm tra trên DB test; không tải customer.css/tv1.css,
  body không có customer-layout. Không đổi source Admin/CRM.
- Đã dọn đúng 2 Account, 1 Customer, 2 Category tạo cho browser QA (cùng preferences
  và authenticated sessions liên quan), không dọn dữ liệu khác. Server QA đã dừng.
- Tính tương phản các cặp chữ chính: ink/white 14.84:1; muted/light-gray ≥5.18:1;
  orange/white 5.29:1; error/white 7.82:1. Đây là kiểm tra palette và focus thủ công,
  không phải chứng nhận audit toàn bộ WCAG.
- Chỉ kiểm tra browser trên máy tính với viewport giả lập, chưa kiểm tra điện
  thoại vật lý/toàn bộ browser. Kết nối browser bị ngắt ở cuối QA; ảnh đã lưu và
  server 8001 được khởi động lại.

Ảnh nằm ngoài repo tại:
`C:/Users/Khiem/.codex/visualizations/2026/10/12/01a12edc-2bc2-7f41-a8b9-76e8c69b572a`.

Các cặp so sánh cùng viewport/zoom:
- `retail-before-home-1440.jpg` / `retail-after-home-1440.jpg`
- `retail-before-products-1440.jpg` / `retail-after-products-1440.jpg`
- `retail-before-home-390.jpg` / `retail-after-home-390.jpg`
- `retail-before-products-390.jpg` / `retail-after-products-390.jpg`

Công cụ IAB xuất vùng nội dung JPEG; kích thước file có thể nhỏ hơn viewport do
thanh cuộn/scale capture. Các cặp trên có kích thước ảnh khớp nhau. 1366px là lượt
kiểm tra bổ sung; không dùng ảnh trước 1366 làm cặp so sánh vì capture lúc đổi
viewport có chiều cao không khớp.

## Chạy và so sánh

Preview: http://127.0.0.1:8001/ (hoặc /products/).
Nếu tab cũ hiển thị lỗi sau phiên kết nối bị ngắt, tải lại trang.
Preview hiện chạy PID 232428 với --noreload. Dừng tiến trình này trước khi tự
chạy lại trên cùng cổng; PID có thể thay đổi sau khi khởi động lại.

```powershell
Set-Location C:/Users/Khiem/.codex/worktrees/44c0/crm_project
$env:PYTHONIOENCODING = 'utf-8'
D:/Python312/python.exe manage.py runserver 127.0.0.1:8001 --settings=config.local_settings
```

Không cần migrate hoặc seed. So sánh với mốc trước:

```powershell
git diff checkpoint/tv1-shop-before-retail-20261012
git show checkpoint/tv1-shop-before-retail-20261012
```

Để mở code cũ mà vẫn giữ bản sửa chưa commit, có thể tạo checkout riêng từ tag
bằng `git worktree add --detach ../crm-shop-before-retail checkpoint/tv1-shop-before-retail-20261012`;
không reset worktree đang sửa. Các ignored local settings/.env cần được cấu hình
riêng trước khi chạy checkout đó.

Quay lại develop: dừng preview và chuyển về checkout chính, nơi develop đã được
checkout; không switch develop trong worktree này.

```powershell
Set-Location D:/Desktop/crm_project
git branch --show-current
```

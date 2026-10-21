# Hướng dẫn chạy đồ án CRM Shop cầu lông X

Công nghệ: Django 5.2 + MySQL 8.4 + Python 3.12. Chạy bằng **PowerShell** trên Windows.

## A. Cài đặt lần đầu (chỉ làm một lần)

### 1. Chuẩn bị
- MySQL Server đang chạy (`services.msc` → tìm `MySQL80`/`MySQL84` → Start).
- Trong `crm_project\.env` có đủ các dòng sau (điền mật khẩu thật của bạn):
  ```
  DB_NAME=crm_db
  DB_USER=crm_user
  DB_PASSWORD=<mật khẩu crm_user>
  DB_HOST=127.0.0.1
  DB_PORT=3306
  MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.4\bin
  ```

### 2. Bật môi trường ảo
```powershell
cd D:\DoAn_HTTTDN\crm_project
.\venv\Scripts\Activate.ps1
```
Đầu dòng lệnh hiện `(venv)` là thành công.
- Lỗi "running scripts is disabled": chạy `Set-ExecutionPolicy -Scope Process Bypass` rồi bật lại.
- Nếu `venv` hỏng: `python -m venv venv`, bật lại, rồi `pip install -r requirements.txt`.

### 3. Tạo database trống (nếu chưa có `crm_db`)
```powershell
& "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p
```
Trong dấu nhắc `mysql>`:
```sql
CREATE DATABASE IF NOT EXISTS crm_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'crm_user'@'localhost' IDENTIFIED BY '<mật khẩu>';
GRANT ALL PRIVILEGES ON crm_db.* TO 'crm_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Tạo bảng và nạp dữ liệu mẫu
```powershell
python manage.py migrate
python manage.py seed_catalog
python manage.py seed_data
python manage.py seed_surveys
```
**Phải chạy đúng thứ tự trên** (mỗi lệnh chạy lại được, không tạo trùng):

| Lệnh | Tạo ra |
|---|---|
| `seed_catalog` | 40 sản phẩm thật (4 danh mục, 5 thương hiệu). Ảnh là link imgur, máy demo cần có mạng. |
| `seed_data` | 2 tài khoản demo, 8 sản phẩm "Demo racket", 40 khách hàng `kh01…kh40` và 36 phản hồi gắn với sản phẩm thật. |
| `seed_surveys` | 3 khảo sát (nháp / đang chạy 8 trên 20 trả lời / đã đóng 24 trên 24), 24 khách "Khách hàng mẫu", và tài khoản `demo-manager@example.test`. |

Lưu ý:
- Chạy `seed_data` **trước** `seed_catalog` thì phản hồi sẽ gắn với "Demo racket". Muốn sửa thì phải tạo lại DB rồi chạy lại các lệnh.
- `seed_surveys` phải chạy sau `seed_data` (cần tài khoản `demo-admin`).
- Chạy lại `seed_catalog` sẽ **ghi đè** giá, mô tả, trạng thái và ảnh của 40 sản phẩm thật về giá trị mặc định.
- Nếu `DEBUG=False` trong `.env`, cần đặt trước `$env:CRM_DEMO_PASSWORD = "DemoPass!2026"` thì `seed_data` và `seed_surveys` mới chạy.
- Sau khi seed đủ, danh sách khách hàng có từ 65 người trở lên (40 + 24 + các tài khoản demo).

### 5. Đăng nhập thử
Không cần cấp quyền thêm. Tài khoản `demo-admin@example.test` đã vào được các trang CRM. Xem mục C.

## B. Chạy hằng ngày
```powershell
cd D:\DoAn_HTTTDN\crm_project
.\venv\Scripts\Activate.ps1
python manage.py runserver
```
Dừng server: `Ctrl+C`.

Web **không có trang chủ ở `/`** (báo 404 là bình thường). Hãy vào thẳng đường dẫn bên dưới.

## C. Tài khoản và đường dẫn

| Vai trò | Tài khoản | Mật khẩu |
|---|---|---|
| Admin | `demo-admin@example.test` | `DemoPass!2026` |
| Quản lý (nhóm CRM_MANAGER) | `demo-manager@example.test` (tạo bởi `seed_surveys`) | `DemoPass!2026` |
| Khách hàng demo | `demo-customer@example.test` | `DemoPass!2026` |
| 40 khách hàng mẫu | `kh01@example.test` … `kh40@example.test` (kh40 bị khóa) | `Khach@123` |

Nhân viên đăng nhập ở `/manager/login/`, khách hàng đăng nhập ở `/login/`.
`demo-manager` có thể bị chặn ở trang nhân viên ("Access Denied: Staff only") vì vai trò của tài khoản này là khách hàng. Khi đó hãy dùng `demo-admin`.

| Chức năng | Địa chỉ |
|---|---|
| Đăng nhập nhân viên | http://127.0.0.1:8000/manager/login/ |
| Đăng nhập khách hàng | http://127.0.0.1:8000/login/ |
| Danh sách sản phẩm (cửa hàng) | http://127.0.0.1:8000/products/ |
| Danh sách khách hàng | http://127.0.0.1:8000/crm/customers/ |
| Thêm khách hàng | http://127.0.0.1:8000/crm/customers/new/ |
| Quản lý phản hồi | http://127.0.0.1:8000/crm/feedbacks/ |
| Báo cáo khách hàng | http://127.0.0.1:8000/crm/reports/customers/ |
| Khách gửi phản hồi | http://127.0.0.1:8000/feedbacks/new/?product=<id> |
| Phản hồi của tôi (khách) | http://127.0.0.1:8000/feedbacks/mine/ |

Các trang `/crm/...` dành cho Admin, Quản lý (`MANAGER`) hoặc nhóm `CRM_MANAGER` / `CUSTOMER_SERVICE`.

### Dữ liệu có sau khi seed đủ 4 lệnh
- **Khách hàng:** khoảng 65–70 (kh01…kh40, 24 khách mẫu và các tài khoản demo).
- **Phản hồi:** 38, đủ 3 trạng thái (mới, đang xử lý, đã xử lý), phần lớn gắn với sản phẩm thật.
- **Khảo sát:** 7 khảo sát, trong đó "Hài lòng dịch vụ căng cước" có 24 trên 24 người trả lời.
- **Báo cáo khách hàng:** đủ biểu đồ tuổi, giới tính, trình độ, sở thích, khách mới theo tháng, điểm hài lòng theo sản phẩm.

## D. Lỗi thường gặp

| Thông báo | Cách xử lý |
|---|---|
| `Can't connect to MySQL server` | MySQL chưa chạy → Start dịch vụ trong `services.msc`. |
| `Access denied for user` | Sai `DB_USER`/`DB_PASSWORD` trong `.env`. |
| `Unknown database 'crm_db'` | Chưa tạo database → làm mục A.3. |
| `Table 'crm_db.accounts' doesn't exist` | Chưa chạy `python manage.py migrate`. |
| `Table '...' already exists` khi migrate | DB đang dở dang → xóa và tạo lại `crm_db` (mất dữ liệu trong DB), rồi chạy lại `migrate` và 3 lệnh seed ở mục A.4. |
| `No module named ...` | Chưa bật `venv` hoặc chưa `pip install -r requirements.txt`. |
| `Page not found` ở `/` | Bình thường, vào đường dẫn ở mục C. |
| Vào `/crm/...` bị đẩy đi hoặc "không có quyền" | Đang đăng nhập bằng tài khoản khách hàng. Đăng xuất, rồi đăng nhập `demo-admin` ở `/manager/login/`. |
| `CommandError: Set CRM_DEMO_PASSWORD...` | `DEBUG=False` → đặt `$env:CRM_DEMO_PASSWORD = "DemoPass!2026"` rồi chạy lại. |
| `CommandError: Run seed_data first` | Chạy `seed_data` trước `seed_surveys`. |
| `backup.bat` báo "not a valid application" trong PowerShell | Thử chạy bằng `cmd /c scripts\backup.bat`, hoặc dùng chức năng sao lưu trong trang Admin. |
| `IndentationError: unexpected indent` trong shell | Dòng lệnh bị thụt đầu dòng → gõ lại sát mép trái. |

# SKILL.md — HTTT CRM Shop Cầu Lông

## 1. Mục tiêu của skill

Skill này hướng dẫn AI/agent tham gia phát triển project:

**Website bán đồ thể thao cầu lông tích hợp hệ thống quản lý quan hệ khách hàng (CRM)**

Mục tiêu là giúp agent:
- hiểu đúng phạm vi đồ án;
- làm đúng kiến trúc Django + MySQL của nhóm;
- giữ code giữa các thành viên nhất quán;
- không tự ý thay đổi mô hình dữ liệu, phân quyền hoặc cấu trúc project;
- hỗ trợ code, sửa lỗi, kiểm thử, viết tài liệu và chuẩn bị demo theo yêu cầu đồ án.

Skill này được dùng cho các yêu cầu liên quan đến:
- Django backend;
- MySQL;
- CRUD;
- đăng nhập, phân quyền;
- quản lý khách hàng;
- phản hồi sản phẩm;
- khảo sát khách hàng;
- báo cáo/thống kê;
- sao lưu/phục hồi;
- Git/GitHub;
- tài liệu đồ án;
- dữ liệu demo;
- kiểm thử và chuẩn bị demo.

---

## 2. Phạm vi project

Project là hệ thống CRM cho shop bán đồ thể thao cầu lông.

Các chức năng chính gồm:

### Admin / Quản trị hệ thống
- quản lý sản phẩm;
- quản lý danh mục;
- quản lý thương hiệu;
- quản lý nhà cung cấp;
- quản lý tài khoản;
- phân quyền;
- sao lưu và phục hồi CSDL.

### Quản lý CRM
- thêm khách hàng;
- xóa khách hàng;
- khóa/mở khóa tài khoản khách hàng;
- tiếp nhận và xử lý phản hồi;
- báo cáo khách hàng theo độ tuổi, sở thích, trình độ, giới tính;
- tạo và gửi khảo sát;
- thống kê kết quả khảo sát.

### Khách hàng
- đăng ký;
- đăng nhập;
- chỉnh sửa thông tin cá nhân;
- xem sản phẩm;
- gửi phản hồi sản phẩm;
- nhận và thực hiện khảo sát.

### Ngoài phạm vi ưu tiên
Các chức năng sau không thuộc phần điểm chính và chỉ làm khi chức năng bắt buộc đã ổn định:
- giỏ hàng;
- đặt hàng;
- thanh toán.

---

## 3. Công nghệ bắt buộc / ưu tiên

Ưu tiên đúng theo tài liệu project:

- Python 3.12
- Django 5.2
- MySQL 8.0 hoặc 8.4 LTS
- Django Templates
- Bootstrap 5
- Bootstrap Icons
- Chart.js 4
- Git + GitHub
- draw.io / diagrams.net
- MySQL Workbench

Không tự chuyển sang:
- Flask;
- FastAPI;
- Laravel;
- Node.js;
- React/Vue cho frontend chính;
- SQLite cho bản project chính;
- MariaDB 10.4 của XAMPP cũ.

Nếu người dùng yêu cầu thay công nghệ, phải nêu rõ đó là thay đổi so với kiến trúc hiện tại.

### 3.1. Quy tắc bắt buộc về technical naming

Toàn bộ **technical identifiers** phải dùng **English**.

Áp dụng cho:
- database name, table name, column name, constraint name, index name;
- Django app/model/field/manager/service/selector/form/view/middleware/decorator;
- function, method, class, variable, constant;
- URL path, URL name, namespace;
- API endpoint, JSON key, query parameter;
- role/group/permission codename;
- migration name;
- test class, test function;
- file/folder/module name;
- script, command và Git branch dùng cho code.

Ví dụ đúng:

```text
crm_db
accounts
Account
account_id
password_hash
customers
customer_preferences
feedbacks
surveys
/admin-portal/accounts/
/crm/customers/
CRM_MANAGER
CUSTOMER_SERVICE
```

Không dùng tên kỹ thuật tiếng Việt hoặc tên kỹ thuật legacy trong code/schema mới.

**Ngoại lệ được phép dùng tiếng Việt:**
- comment trong code;
- docstring giải thích;
- tài liệu mô tả nghiệp vụ;
- label/text hiển thị cho người dùng;
- dữ liệu demo như họ tên, địa chỉ, nội dung phản hồi.

Ví dụ:

```python
# Khóa tài khoản để ngăn đăng nhập
account.status = Account.Status.LOCKED
```

Tên biến `account`, field `status`, class `Account` vẫn phải là English.

---

## 4. Cấu trúc project Django mục tiêu

Cấu trúc tham chiếu:

```text
crm_project/
├── manage.py
├── requirements.txt
├── .env.example
├── readme.txt
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/
│   ├── catalog/
│   ├── shop/
│   ├── admin_portal/
│   ├── customers/
│   ├── feedback/
│   └── surveys/
├── templates/
│   ├── layouts/
│   │   ├── base_admin.html
│   │   ├── base_crm.html
│   │   └── base_customer.html
│   └── <app_name>/
├── static/
├── media/
├── database/
│   ├── crm_db.sql
│   └── backups/
└── scripts/
    ├── backup.bat
    └── restore.bat
```

Không tạo app mới nếu chức năng có thể đặt hợp lý vào app hiện có.

Khi thêm file:
1. đặt đúng app;
2. giữ naming nhất quán;
3. cập nhật `urls.py`, template và quyền nếu cần;
4. không tạo logic trùng ở nhiều app.

---

## 5. Giao diện và khu vực hệ thống

Phải giữ 3 khu vực giao diện tách biệt.

Tên hiển thị có thể dùng tiếng Việt, nhưng **URL technical paths phải dùng English**.

### Admin

Prefix:

```text
/admin-portal/
```

Layout:

```text
base_admin.html
```

### CRM Management

Prefix:

```text
/crm/
```

Layout:

```text
base_crm.html
```

### Customer

Prefix:

```text
/
```

Layout:

```text
base_customer.html
```

Không dùng Django `/admin/` mặc định để thay thế giao diện quản trị được chấm điểm. Custom admin portal của project dùng `/admin-portal/`.

---

## 6. Phân quyền

`accounts.role` trong schema chính thức chỉ có:

```text
ADMIN
CUSTOMER
```

Quy tắc:
- `ADMIN`: tài khoản quản trị hệ thống;
- `CUSTOMER`: tài khoản khách hàng.

Không tạo thêm giá trị role tiếng Việt hoặc legacy trong `accounts.role`.

Nếu cần phân quyền chi tiết cho nghiệp vụ CRM, dùng Django Groups/Permissions với **English technical identifiers**, ví dụ:

```text
CRM_MANAGER
CUSTOMER_SERVICE
```

Ví dụ kiểm tra role:

```python
@role_required("ADMIN")
```

Ví dụ kiểm tra quyền chi tiết:

```python
request.user.has_perm("feedback.change_feedback")
```

Mọi view có dữ liệu nhạy cảm phải kiểm tra authorization ở backend.
Không chỉ ẩn nút ở template.

`LOCKED` account không được phép đăng nhập hoặc tiếp tục thực hiện action được bảo vệ.

---

## 7. Quy tắc model tài khoản

Project dùng custom user chính thức:

```python
AUTH_USER_MODEL = "accounts.Account"
```

Model kỹ thuật duy nhất cho tài khoản là:

```text
Account
```

Physical table duy nhất là:

```text
accounts
```

Không dùng alias/fallback/model/table legacy cho tài khoản.

Schema vật lý của `accounts` phải giữ đúng 8 business columns:

```text
account_id
email
password_hash
role
status
last_login_at
created_at
updated_at
```

Mapping Django được phép:

```text
Account.account_id -> accounts.account_id
Account.email -> accounts.email
Django password -> accounts.password_hash
Account.role -> accounts.role
Account.status -> accounts.status
Django last_login -> accounts.last_login_at
Account.created_at -> accounts.created_at
Account.updated_at -> accounts.updated_at
```

Quy tắc:
- email là login identifier;
- không dùng `username` làm business field;
- password phải dùng `set_password()` / `check_password()` của Django;
- không lưu plain-text password;
- không expose `password_hash`;
- role chỉ dùng `ADMIN`, `CUSTOMER`;
- status chỉ dùng `ACTIVE`, `LOCKED`;
- `LOCKED` account phải bị chặn authentication;
- không thêm physical business columns ngoài schema SQL nếu chưa có owner decision;
- profile fields như `full_name`, `phone`, `date_of_birth`, `gender`, `address`, `playing_level` thuộc `Customer`, không thuộc `Account`.

Nếu Django cần behavior như `is_active` hoặc `is_staff`, ưu tiên derived property/method dựa trên `status`/`role` thay vì tự ý thêm cột mới vào `accounts`.

---

## 8. Cơ sở dữ liệu — nguyên tắc làm việc

### 8.1. Source of truth

Database chính thức:

```text
crm_db
```

Canonical SQL:

```text
database/crm_db.sql
```

Schema business chính thức dùng **English technical identifiers only**.

Khi task liên quan database, ưu tiên theo thứ tự:

1. yêu cầu mới nhất của owner;
2. `database/crm_db.sql`;
3. live MySQL `crm_db`;
4. Django model/migration đã được căn chỉnh với SQL;
5. tài liệu hướng dẫn;
6. suy luận của agent.

Không dùng tên bảng/field/model tiếng Việt từ tài liệu cũ để tạo code mới.

Nếu code/migration cũ mâu thuẫn với canonical SQL:
- coi code/migration cũ là legacy cho đến khi xác minh;
- không để legacy naming quyết định schema đích;
- căn chỉnh Django theo schema English đã được owner chốt;
- không âm thầm phá dữ liệu live.

### 8.2. Quy trình trước thay đổi database

Trước thay đổi liên quan CSDL:
1. đọc `database/crm_db.sql`;
2. kiểm tra live `crm_db` read-only nếu kết nối khả dụng;
3. đọc Django model/migration liên quan;
4. so sánh SQL ↔ live DB ↔ Django;
5. xác định migration strategy an toàn;
6. chỉ sau đó mới thay đổi schema hoặc migration.

Không rerun script có `DROP DATABASE` trên database đang dùng nếu owner không yêu cầu rõ.

### 8.3. Migration safety

- Mỗi app chỉ tạo migration cho model của app đó.
- Không sửa/xóa migration đã dùng chung hoặc đã merge nếu chưa có owner decision.
- Không tự reset database.
- Không fake migration nếu chưa hiểu rõ live schema.
- Không chạy `migrate` máy móc khi bảng business đã được tạo từ SQL.
- Migration state và physical schema phải được căn chỉnh có chủ đích.

### 8.4. Encoding

MySQL dùng:

```text
utf8mb4
utf8mb4_unicode_ci
```

để hỗ trợ dữ liệu tiếng Việt có dấu.

---

## 9. Schema SQL hiện có cần tôn trọng khi làm việc trực tiếp với file SQL

File SQL hiện tại có 13 bảng chính:

```text
accounts
customers
categories
brands
products
customer_preferences
feedbacks
surveys
survey_questions
survey_options
survey_recipients
survey_responses
survey_answers
```

Các quan hệ quan trọng:
- `customers.account_id -> accounts.account_id`
- `products.category_id -> categories.category_id`
- `products.brand_id -> brands.brand_id`
- `customer_preferences.customer_id -> customers.customer_id`
- `feedbacks.customer_id -> customers.customer_id`
- `feedbacks.product_id -> products.product_id`
- `feedbacks.handled_by -> accounts.account_id`
- `surveys.created_by -> accounts.account_id`
- `survey_questions.survey_id -> surveys.survey_id`
- `survey_options.question_id -> survey_questions.question_id`
- `survey_recipients.survey_id -> surveys.survey_id`
- `survey_recipients.customer_id -> customers.customer_id`
- `survey_responses.recipient_id -> survey_recipients.recipient_id`
- `survey_answers.response_id -> survey_responses.response_id`
- `survey_answers.question_id -> survey_questions.question_id`
- `survey_answers.option_id -> survey_options.option_id`

Không thêm/xóa foreign key tùy ý.

---

## 10. Lưu ý về xung đột schema hiện có

Schema SQL chính thức là chuẩn kỹ thuật cho business tables.

`accounts.role` chỉ hỗ trợ:

```text
ADMIN
CUSTOMER
```

Không mở rộng role bằng cách thêm giá trị tùy ý vào database.

Nếu cần quyền nghiệp vụ chi tiết hơn:
- dùng Django Groups/Permissions;
- group/permission codename phải dùng English;
- không thay đổi `accounts.role` nếu chưa có owner decision.

Schema hiện tại chưa có một số đối tượng từng xuất hiện trong tài liệu mô tả, ví dụ supplier hoặc backup log table. Không tự tạo thêm table/column chỉ vì tài liệu cũ nhắc đến chúng.

Khi task cần một đối tượng chưa có trong `database/crm_db.sql`:
1. báo rõ schema hiện tại chưa có;
2. đề xuất thay đổi bằng English technical identifiers;
3. chỉ triển khai khi owner chấp thuận.

---

## 11. URL tham chiếu

URL paths và URL names phải dùng English.

Các URL tham chiếu:

```text
/login/
/register/
/logout/

/products/
/products/<id>/

/account/profile/

/admin-portal/products/
/admin-portal/categories/
/admin-portal/brands/
/admin-portal/accounts/
/admin-portal/permissions/
/admin-portal/backups/

/crm/customers/
/crm/feedback/
/crm/reports/customers/
/crm/surveys/

/feedback/submit/
/surveys/mine/
```

User-facing menu/label có thể hiển thị tiếng Việt.

Nếu code hiện tại còn URL technical path tiếng Việt, ưu tiên chuyển sang English theo từng module và cập nhật reverse/redirect/template/test tương ứng. Không tạo hai hệ URL song song trừ khi cần compatibility tạm thời và được ghi rõ.

---

## 12. Chức năng sản phẩm / danh mục

Danh sách sản phẩm nên hỗ trợ:
- ảnh nhỏ;
- mã;
- tên;
- danh mục;
- thương hiệu;
- nhà cung cấp nếu schema có;
- giá;
- tồn kho nếu schema có;
- trạng thái;
- phân trang.

Tìm kiếm:
- theo mã hoặc tên;
- không phân biệt hoa thường.

Tìm kiếm nâng cao có thể gồm:
- danh mục;
- thương hiệu;
- nhà cung cấp;
- trọng lượng vợt;
- khoảng giá;
- tồn kho;
- trạng thái;
- ngày tạo.

Sắp xếp phải whitelist field hợp lệ.

Không đưa trực tiếp tham số sort từ request vào `order_by()` mà không kiểm tra.

---

## 13. Chức năng khách hàng

Các chức năng cần hỗ trợ:
- thêm khách hàng;
- xóa hoặc xóa mềm theo schema thực tế;
- khóa/mở tài khoản;
- chỉnh sửa hồ sơ;
- lưu sở thích;
- báo cáo phân nhóm.

Khi xóa khách hàng:
- kiểm tra dữ liệu phản hồi;
- kiểm tra khảo sát;
- tránh xóa cascade ngoài ý muốn;
- hiển thị cảnh báo nếu có dữ liệu liên quan.

Khi khóa tài khoản:
- không xóa tài khoản;
- cập nhật trạng thái hoặc `is_active` theo model thực tế;
- đảm bảo login bị chặn;
- nếu schema có lý do khóa/ngày khóa thì lưu lại.

---

## 14. Chức năng phản hồi

Phản hồi phải gắn với:
- khách hàng;
- sản phẩm;
- điểm đánh giá 1–5;
- nội dung;
- trạng thái;
- người xử lý;
- thời gian xử lý nếu có.

Quy trình:
1. khách hàng gửi phản hồi;
2. quản lý/NV CSKH xem danh sách;
3. lọc theo trạng thái/sản phẩm/số sao/ngày nếu hệ thống hỗ trợ;
4. cập nhật trạng thái;
5. trả lời hoặc ghi chú xử lý;
6. khách hàng xem lại kết quả nếu giao diện hỗ trợ.

Không để khách hàng sửa phản hồi của khách khác.

---

## 15. Chức năng khảo sát

Khảo sát cần hỗ trợ các loại câu hỏi:
- một lựa chọn;
- nhiều lựa chọn;
- thang điểm 1–5;
- tự luận.

Luồng:
1. tạo khảo sát;
2. thêm câu hỏi;
3. thêm lựa chọn;
4. chọn nhóm khách hàng;
5. gửi khảo sát;
6. khách hàng mở khảo sát;
7. khách hàng trả lời;
8. nộp;
9. thống kê kết quả.

Ràng buộc:
- không nộp khảo sát lần 2 nếu nghiệp vụ không cho phép;
- không làm khảo sát đã đóng;
- câu bắt buộc phải được kiểm tra ở backend;
- câu nhiều lựa chọn phải lưu được nhiều lựa chọn;
- thống kê phải khớp kiểu câu hỏi.

---

## 16. Báo cáo khách hàng

Báo cáo mục tiêu gồm:
- tỷ lệ theo nhóm tuổi;
- sở thích;
- trình độ chơi;
- giới tính;
- khách hàng mới theo tháng;
- điểm hài lòng trung bình theo sản phẩm nếu dữ liệu đủ.

Biểu đồ dùng Chart.js.

Nếu có biểu đồ:
- dữ liệu tính ở backend;
- template chỉ nhận labels/data;
- không hardcode số liệu;
- cần có bảng số liệu song song nếu báo cáo yêu cầu in.

---

## 17. Sao lưu và phục hồi

MySQL backup dùng:
```text
mysqldump
```

Restore dùng:
```text
mysql
```

Nên có:
```text
scripts/backup.bat
scripts/restore.bat
database/backups/
```

Khi dùng user không phải root, backup nên dùng:
```text
--no-tablespaces
```

Không commit:
```text
database/backups/
```

Không ghi mật khẩu thật trực tiếp vào source.

---

## 18. File môi trường

Dùng `.env`.

Các biến tham chiếu:

```env
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=crm_db
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306

MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.0\bin
```

Không commit `.env`.

Được commit:
```text
.env.example
```

---

## 19. Dữ liệu demo

Dữ liệu demo cần đủ để demo chức năng và vẽ biểu đồ.

Theo tài liệu project, nên có tối thiểu:
- khoảng 40 sản phẩm;
- ít nhất 6 thương hiệu;
- ít nhất 8 nhà cung cấp nếu module này tồn tại;
- khoảng 40 khách hàng;
- ít nhất 30 phản hồi;
- ít nhất 3 khảo sát;
- dữ liệu đủ nhiều nhóm tuổi, sở thích, trình độ.

Dữ liệu demo phải hợp lý:
- tên Việt Nam;
- giá sản phẩm hợp lý;
- ngày trải đều;
- có dữ liệu ở nhiều trạng thái.

Không seed toàn bộ dữ liệu giống nhau.

---

## 20. Git workflow

Không push thẳng vào `main`.

Luồng chuẩn:

```bash
git checkout develop
git pull

git checkout -b feature/<branch-name>

# code + test

git add .
git commit -m "feat(...): ..."

git push -u origin feature/<branch-name>
```

Sau đó:
1. tạo Pull Request vào `develop`;
2. kiểm thử chéo;
3. review;
4. merge;
5. xóa branch khi không còn cần.

Commit phải nhỏ và rõ nghĩa.

Ví dụ:

```text
feat(tv4): add customer account lock and unlock
fix(surveys): prevent duplicate survey submission
refactor(accounts): extract role_required decorator
docs(ch4): update installation guide
```

---

## 21. Phân công tham chiếu

### TV1
- nền tảng Django;
- accounts;
- đăng nhập/đăng ký;
- hồ sơ khách hàng;
- layout;
- shop;
- tích hợp;
- Chương 4.

### TV2
- catalog;
- sản phẩm;
- danh mục;
- thương hiệu;
- nhà cung cấp;
- tìm kiếm/lọc/sắp xếp;
- Chương 1.

### TV3
- tài khoản Admin;
- phân quyền;
- ERD;
- sao lưu/phục hồi;
- seed;
- SQL script;
- Chương 3a.

### TV4
- khách hàng;
- phản hồi;
- báo cáo khách hàng;
- mô tả bài toán;
- BFD;
- sơ đồ ngữ cảnh.

### TV5
- khảo sát;
- gửi khảo sát;
- làm khảo sát;
- thống kê;
- DFD mức đỉnh;
- Chương 5.

Khi agent sửa code thuộc phần của thành viên khác, phải nói rõ module bị ảnh hưởng.

---

## 22. Kiểm thử chéo

Tham chiếu:
- TV1 được TV5 kiểm thử;
- TV2 được TV3 kiểm thử;
- TV3 được TV4 kiểm thử;
- TV4 được TV1 kiểm thử;
- TV5 được TV2 kiểm thử.

Khi hoàn thành một chức năng, agent phải đưa checklist test tương ứng.

Ví dụ với chức năng khóa tài khoản:
- khóa thành công;
- mở khóa thành công;
- user bị khóa không đăng nhập được;
- user khác không bị ảnh hưởng;
- quyền gọi endpoint được kiểm tra;
- dữ liệu không bị xóa;
- UI hiển thị đúng trạng thái.

---

## 23. Quy trình xử lý mỗi task

Khi nhận một task coding, agent phải làm theo thứ tự:

### Bước 1 — Xác định phạm vi
Xác định:
- app nào;
- model nào;
- URL nào;
- vai trò nào;
- thành viên nào phụ trách theo phân công.

### Bước 2 — Kiểm tra hiện trạng
Trước khi viết code:
- đọc file hiện có;
- kiểm tra model;
- kiểm tra URL;
- kiểm tra template;
- kiểm tra migration;
- kiểm tra schema SQL nếu task liên quan DB.

Không viết đè dựa trên giả định.

### Bước 3 — Xác định ảnh hưởng
Nêu:
- file cần sửa;
- migration có cần không;
- quyền nào bị ảnh hưởng;
- có ảnh hưởng app khác không;
- có ảnh hưởng dữ liệu demo không.

### Bước 4 — Triển khai nhỏ nhất
Ưu tiên thay đổi nhỏ nhất để đạt yêu cầu.

Không refactor toàn project nếu task chỉ cần sửa một chức năng.

### Bước 5 — Kiểm thử
Tối thiểu kiểm tra:
- happy path;
- dữ liệu sai;
- quyền;
- trạng thái biên;
- dữ liệu liên quan.

### Bước 6 — Báo cáo kết quả
Trả lời theo dạng:
- đã làm gì;
- file nào thay đổi;
- migration;
- cách chạy;
- cách test;
- điểm cần lưu ý.

---

## 24. Quy tắc khi viết code

- Mọi technical identifier trong code phải dùng English; comment/docstring có thể dùng tiếng Việt.
- Không tạo table/column/model/field/function/URL/permission codename bằng tiếng Việt.
- Code phải dễ đọc cho sinh viên có thể giải thích khi vấn đáp.
- Không lạm dụng abstraction phức tạp.
- Không thêm thư viện nếu Django chuẩn đã đủ.
- Không hardcode mật khẩu, secret hoặc đường dẫn máy cá nhân.
- Không dùng raw SQL nếu ORM Django xử lý tốt.
- Raw SQL chỉ dùng khi thực sự cần và phải parameterized.
- Form phải validate phía backend.
- Không tin dữ liệu từ request.
- Không expose stack trace ở production.
- Tránh N+1 query; dùng `select_related()` / `prefetch_related()` khi phù hợp.
- Pagination cho danh sách dài.
- Sort field phải whitelist.
- Upload file phải kiểm tra loại/kích thước nếu có.
- Mọi action xóa/khóa/phục hồi phải có xác nhận.
- Không dùng `csrf_exempt` để xử lý nhanh trừ khi có lý do chính đáng.

---

## 25. Quy tắc template

- Dùng Bootstrap 5.
- Tái sử dụng layout và partial.
- Không copy nguyên navbar/sidebar giữa nhiều file.
- Hiển thị message từ Django messages.
- Form hiển thị lỗi validation rõ ràng.
- Nút chức năng phải ẩn/hiện phù hợp với quyền nhưng backend vẫn phải kiểm tra quyền.
- Giữ UI đủ đơn giản để demo nhanh.

---

## 26. Quy tắc bảo mật tối thiểu

- Password dùng Django password hashing.
- Không lưu plain-text password.
- Không commit `.env`.
- Không commit backup thật.
- CSRF bật cho form POST.
- Kiểm tra authorization cho mọi endpoint.
- Kiểm tra object ownership với dữ liệu khách hàng.
- Không cho customer truy cập dữ liệu customer khác.
- Không cho `CUSTOMER_SERVICE` group thực hiện action ngoài quyền được cấp.
- Không cho user tự nâng role qua form/profile.
- Không cho xóa admin cuối cùng nếu chức năng tài khoản có quy tắc này.

---

## 27. Quy tắc tài liệu đồ án

Khi viết nội dung báo cáo:
- bám sát chức năng thực tế đã code;
- không mô tả tính năng chưa có như đã hoàn thành;
- tên bảng, URL, vai trò phải khớp hệ thống thực tế;
- hình chụp phải đúng chức năng;
- mỗi thành viên viết phần mình;
- ghi rõ người thực hiện;
- ưu tiên thuật ngữ dùng thống nhất giữa BFD, ngữ cảnh, DFD và ERD.

Thứ tự phân tích tham chiếu:
```text
BFD -> Sơ đồ ngữ cảnh -> DFD -> ERD
```

Tên tiến trình và kho dữ liệu phải khớp nhau.

---

## 28. Khi tạo hoặc sửa sơ đồ

Trước khi sửa:
1. lấy danh sách chức năng thực tế;
2. lấy bảng dữ liệu thực tế;
3. đối chiếu BFD;
4. đối chiếu sơ đồ ngữ cảnh;
5. đối chiếu DFD;
6. đối chiếu ERD.

Không vẽ một bảng trong ERD nếu code/schema không có, trừ khi đang thiết kế đề xuất.

Phải phân biệt:
- **thiết kế đề xuất**
- **schema hiện tại**
- **schema sau khi thay đổi**

---

## 29. Khi có mâu thuẫn giữa tài liệu và code

Ưu tiên theo thứ tự cho task kỹ thuật:

1. yêu cầu mới nhất của người dùng/owner;
2. canonical SQL `database/crm_db.sql`;
3. live MySQL `crm_db`;
4. Django code/model/migration đã được căn chỉnh với SQL;
5. tài liệu hướng dẫn;
6. tài liệu phân công;
7. suy luận của agent.

Không âm thầm sửa mâu thuẫn.

Nếu phát hiện code legacy dùng naming hoặc schema khác với SQL chính thức:
- không dùng legacy làm schema đích;
- báo rõ phần lệch;
- giữ English technical naming;
- chọn migration/alignment strategy an toàn.

Ví dụ:

```text
Canonical SQL defines Account -> accounts with role ADMIN/CUSTOMER.
Legacy code must be aligned to the canonical SQL before feature work continues.
```

---

## 30. Khi người dùng yêu cầu “làm luôn”

Nếu đủ file và đủ thông tin:
- triển khai trực tiếp;
- không hỏi lại các chi tiết có thể xác định từ project.

Chỉ hỏi lại khi:
- có xung đột schema ảnh hưởng trực tiếp;
- thao tác có nguy cơ phá dữ liệu;
- có nhiều hướng triển khai khác nhau dẫn đến cấu trúc DB khác nhau;
- thiếu file bắt buộc để chỉnh đúng code.

---

## 31. Khi review code

Review theo các tiêu chí:
- đúng yêu cầu đồ án;
- đúng app;
- đúng quyền;
- đúng schema;
- có validation;
- không phá migration;
- query hợp lý;
- template không lặp quá mức;
- UX demo được;
- code đủ đơn giản để sinh viên giải thích;
- có test case.

Không chỉ review style.

---

## 32. Khi sửa bug

Quy trình:
1. mô tả symptom;
2. xác định reproduction steps;
3. tìm nguyên nhân;
4. sửa ít nhất có thể;
5. kiểm tra regression;
6. nêu file bị sửa;
7. đưa lệnh test/chạy lại.

Không “sửa mò” nhiều file cùng lúc.

---

## 33. Lệnh chạy tham chiếu

```bash
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py seed_data

python manage.py runserver
```

Nếu import SQL:

```bash
mysql -u root -p crm_db < database\crm_db.sql
```

Không vừa import SQL vừa chạy seed/migration một cách máy móc trên cùng DB nếu hai cách khởi tạo không tương thích.

---

## 34. Checklist trước khi kết thúc task

Agent phải tự kiểm tra:

```text
[ ] Đúng app
[ ] Đúng URL
[ ] Đúng role/quyền
[ ] Đúng schema hiện tại
[ ] Technical identifiers dùng English
[ ] Không có legacy database/model naming trong active code
[ ] Không hardcode secret
[ ] Không phá migration cũ
[ ] Form có validation
[ ] Query không quá tệ
[ ] Có kiểm tra quyền backend
[ ] Có test case
[ ] Có hướng dẫn chạy
[ ] Tài liệu liên quan được cập nhật nếu cần
```

---

## 35. Mục tiêu cuối cùng

Mọi thay đổi phải phục vụ 4 mục tiêu:

1. **Chạy được**
2. **Đúng yêu cầu đồ án**
3. **Dễ demo và vấn đáp**
4. **Không làm hỏng phần của thành viên khác**

Khi phải chọn giữa kiến trúc quá phức tạp và cách làm đơn giản nhưng đúng yêu cầu, ưu tiên cách đơn giản, rõ ràng, dễ giải thích và phù hợp phạm vi đồ án.

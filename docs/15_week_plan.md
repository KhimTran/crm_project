# Kế hoạch 15 tuần

Đề tài: Website bán đồ cầu lông tích hợp CRM.
Nhóm: [Tên nhóm]. Lớp: [Lớp]. Giảng viên: [Họ tên].
TV1: [Họ tên] — [MSSV]. TV2/TV3/TV4/TV5: [Họ tên — MSSV].
Ngày bắt đầu: [Ngày]. Ngày kết thúc: [Ngày].

Đây là kế hoạch đề xuất theo tuần học, không phải bảng xác nhận đóng góp thực tế.
Ngày hoàn thành, người thực hiện và kết quả phải được nhóm cập nhật bằng bằng chứng.
Thứ tự: yêu cầu → DB → backend/service/API → validation/quyền → test → UI → tích hợp.

| Tuần | Công việc dự kiến | Sản phẩm / điều kiện hoàn thành |
| --- | --- | --- |
| 1 | Khảo sát bài toán, phạm vi, yêu cầu và phân công | Danh mục nghiệp vụ, giới hạn, thông tin nhóm đã xác nhận |
| 2 | Phân tích chức năng, BFD và sơ đồ ngữ cảnh | Tên tiến trình thống nhất; yêu cầu cần quyết định được ghi rõ |
| 3 | DFD và thiết kế dữ liệu, ERD | Mapping English, quan hệ và ràng buộc được review |
| 4 | Nền tảng Django/MySQL, models/migrations | Auth Account, schema đã xác minh trên DB riêng; kế hoạch backup |
| 5 | Backend auth và quản trị tài khoản TV1/TV3 | Hash, CSRF, role/group, lock và API được kiểm thử |
| 6 | Backend catalog TV2 | Product/Category/Brand/Supplier, validation và test |
| 7 | Hồ sơ TV1, quản lý khách hàng TV4 | Ownership, transaction, contract sở thích; backend đủ test |
| 8 | Phản hồi TV4 | Quyền gửi/xử lý, lịch sử và validation; test cross-module |
| 9 | Khảo sát TV5 | Gửi/trả lời/thống kê, kiểm tra quan hệ và unique |
| 10 | Hoàn thiện UI TV1/TV2/TV3/TV4/TV5 | Django Templates theo layout khu vực; route thật và tài nguyên offline |
| 11 | Tích hợp các nhánh vào develop theo review | Contract URL/model/quyền thống nhất; không gộp mù quáng |
| 12 | Kiểm thử chéo và regression | TV1←TV5, TV2←TV3, TV3←TV4, TV4←TV1, TV5←TV2; log lỗi thật |
| 13 | Chuẩn bị dữ liệu/demo và backup/restore TV3 | Bộ demo tái tạo, restore disposable có bằng chứng; không ảnh hưởng DB chung |
| 14 | Hoàn thiện báo cáo và Chương 4 | Ảnh chụp đúng revision; hướng dẫn cài đặt và test có kết quả thật |
| 15 | Diễn tập bảo vệ, sửa lỗi cuối và bàn giao | Kịch bản chạy được, tài liệu/nguồn code/SQL đã review, phân công ký xác nhận |

TV1 hiện triển khai auth, hồ sơ cá nhân, shop và trang CRM tổng quan trên develop,
chưa xác nhận toàn bộ tiến độ của nhóm. Tích hợp phản hồi, khảo sát, báo cáo CRM,
SMTP thật và live DB phụ thuộc người phụ trách. Không coi “Sắp có” là chức năng hoàn tất.

-- =====================================================================
-- seed_survey_report.sql (TV5) – BỘ 8 CÂU HỎI CHÍNH THỨC + khách hàng + phiếu đã trả lời
-- Bộ câu hỏi lấy từ apps/surveys/questionnaire.py (template BADMINTON_SHOP_EXPERIENCE_V1).
--
-- ĐIỀU KIỆN: DB đồng bộ với schema database/crm_db.sql (bảng customers đã gộp vào accounts;
--   surveys có template_key / objective / audience, survey_questions có config JSON).
-- CÁCH CHẠY:
--   mysql -u root -p --default-character-set=utf8mb4 crm_db < seed_survey_report.sql
-- ĐÁNH DẤU DỮ LIỆU THỬ (giống lệnh seed_survey_report_demo): tiêu đề "[DỮ LIỆU THỬ]", email "@survey-report-demo.test",
--   tên "[Thử] ...". Xóa sạch bằng: python manage.py seed_survey_report_demo --clear --confirm
-- Mật khẩu 30 tài khoản khách = mật khẩu của demo-customer@example.test.
-- Chạy lại nhiều lần không bị nhân đôi (ID cố định + INSERT IGNORE).
-- =====================================================================
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
START TRANSACTION;

-- 1) Tài khoản & hồ sơ khách hàng thử (playing_level để NULL: sẽ được cập nhật từ câu trả lời ở bước 8)
INSERT IGNORE INTO `accounts` (
  `account_id`, `email`, `password_hash`, `role`, `status`,
  `full_name`, `phone`, `date_of_birth`, `gender`, `address`, `playing_level`,
  `created_at`, `updated_at`
) VALUES
  (101, 'khach01@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Nguyễn Minh Anh', '0933000001', '2010-06-20', 'MALE', 'Quận 1, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (102, 'khach02@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Trần Quốc Bảo', '0933000002', '1985-05-14', 'MALE', 'Quận Bình Thạnh, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (103, 'khach03@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Lê Thị Cẩm Tú', '0933000003', '1997-06-18', 'FEMALE', 'Thủ Đức, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (104, 'khach04@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Phạm Hoàng Dũng', '0933000004', '1979-10-10', 'FEMALE', 'Cầu Giấy, Hà Nội', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (105, 'khach05@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Võ Thanh Hà', '0933000005', '2002-12-31', 'FEMALE', 'Đống Đa, Hà Nội', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (106, 'khach06@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Đặng Gia Huy', '0933000006', '2006-05-19', 'MALE', 'Hải Châu, Đà Nẵng', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (107, 'khach07@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Bùi Ngọc Lan', '0933000007', '1994-05-09', 'MALE', 'Ninh Kiều, Cần Thơ', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (108, 'khach08@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Hoàng Văn Khải', '0933000008', '1987-07-12', 'FEMALE', 'Biên Hòa, Đồng Nai', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (109, 'khach09@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Phan Thị Mai', '0933000009', '1993-05-07', 'MALE', 'Quận 1, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (110, 'khach10@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Vũ Đức Nam', '0933000010', '1976-08-04', 'MALE', 'Quận Bình Thạnh, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (111, 'khach11@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Đỗ Thùy Linh', '0933000011', '1988-03-01', 'MALE', 'Thủ Đức, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (112, 'khach12@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Ngô Tuấn Kiệt', '0933000012', '1966-07-02', 'MALE', 'Cầu Giấy, Hà Nội', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (113, 'khach13@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Dương Bảo Ngọc', '0933000013', '2004-08-03', 'MALE', 'Đống Đa, Hà Nội', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (114, 'khach14@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Lý Thành Đạt', '0933000014', '1996-06-28', 'MALE', 'Hải Châu, Đà Nẵng', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (115, 'khach15@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Trịnh Hải Yến', '0933000015', '2006-04-27', 'MALE', 'Ninh Kiều, Cần Thơ', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (116, 'khach16@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Huỳnh Minh Khôi', '0933000016', '1997-02-26', 'MALE', 'Biên Hòa, Đồng Nai', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (117, 'khach17@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Mai Phương Thảo', '0933000017', '1999-04-18', 'FEMALE', 'Quận 1, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (118, 'khach18@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Tô Nhật Minh', '0933000018', '1984-04-24', 'MALE', 'Quận Bình Thạnh, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (119, 'khach19@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Châu Anh Thư', '0933000019', '2009-10-04', 'MALE', 'Thủ Đức, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (120, 'khach20@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Lâm Quang Vinh', '0933000020', '1993-09-18', 'FEMALE', 'Cầu Giấy, Hà Nội', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (121, 'khach21@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Đinh Thị Hồng', '0933000021', '1981-01-21', 'FEMALE', 'Đống Đa, Hà Nội', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (122, 'khach22@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Cao Xuân Trường', '0933000022', '2010-07-04', 'FEMALE', 'Hải Châu, Đà Nẵng', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (123, 'khach23@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Tạ Khánh Vy', '0933000023', '1990-07-18', 'FEMALE', 'Ninh Kiều, Cần Thơ', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (124, 'khach24@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Hà Đình Phong', '0933000024', '2001-08-28', 'MALE', 'Biên Hòa, Đồng Nai', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (125, 'khach25@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Kiều Mỹ Duyên', '0933000025', '1990-01-21', 'MALE', 'Quận 1, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (126, 'khach26@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Lương Gia Bảo', '0933000026', '2005-05-01', 'MALE', 'Quận Bình Thạnh, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (127, 'khach27@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Quách Thanh Tùng', '0933000027', '2000-01-26', 'MALE', 'Thủ Đức, TP. Hồ Chí Minh', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (128, 'khach28@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Thái Bích Ngọc', '0933000028', '2006-02-11', 'MALE', 'Cầu Giấy, Hà Nội', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (129, 'khach29@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Nghiêm Duy Anh', '0933000029', '1975-10-02', 'MALE', 'Đống Đa, Hà Nội', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00'),
  (130, 'khach30@survey-report-demo.test', 'pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=', 'CUSTOMER', 'ACTIVE', '[Thử] Từ Hoài Thương', '0933000030', '2008-01-22', 'MALE', 'Hải Châu, Đà Nẵng', NULL, '2026-04-20 08:00:00', '2026-04-20 08:00:00');

-- 3) Lối chơi (PLAY_STYLE) – thông tin hồ sơ khi đăng ký, khảo sát không hỏi
INSERT INTO `customer_preferences` (`preference_type`, `preference_value`, `customer_id`)
SELECT t.ptype, t.pvalue, t.cid FROM (
  SELECT 'PLAY_STYLE' AS ptype, 'Tấn công' AS pvalue, 101 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 101 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đôi' AS pvalue, 102 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Tấn công' AS pvalue, 103 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 103 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đôi' AS pvalue, 104 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đôi' AS pvalue, 105 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đơn' AS pvalue, 106 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Tấn công' AS pvalue, 106 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đôi' AS pvalue, 107 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 107 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 108 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Tấn công' AS pvalue, 108 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đôi' AS pvalue, 109 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đơn' AS pvalue, 109 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đơn' AS pvalue, 110 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 110 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Phòng thủ' AS pvalue, 111 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 111 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 112 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 113 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đôi' AS pvalue, 113 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đôi' AS pvalue, 114 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Phòng thủ' AS pvalue, 115 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Tấn công' AS pvalue, 116 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Phòng thủ' AS pvalue, 116 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Tấn công' AS pvalue, 117 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Tấn công' AS pvalue, 118 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đơn' AS pvalue, 119 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Phòng thủ' AS pvalue, 119 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đôi' AS pvalue, 120 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 120 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Phòng thủ' AS pvalue, 121 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đơn' AS pvalue, 121 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đơn' AS pvalue, 122 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đôi' AS pvalue, 123 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Tấn công' AS pvalue, 123 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đôi' AS pvalue, 124 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 125 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Phòng thủ' AS pvalue, 126 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đơn' AS pvalue, 127 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 128 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đơn' AS pvalue, 129 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Toàn diện' AS pvalue, 130 AS cid
  UNION ALL
  SELECT 'PLAY_STYLE' AS ptype, 'Đánh đơn' AS pvalue, 130 AS cid
) t
WHERE NOT EXISTS (SELECT 1 FROM customer_preferences p WHERE p.customer_id = t.cid
                  AND p.preference_type = t.ptype AND p.preference_value = t.pvalue);

-- 4) Khảo sát (người tạo = tài khoản MANAGER/ADMIN có ID nhỏ nhất)
INSERT IGNORE INTO `surveys` (`survey_id`,`title`,`template_key`,`objective`,`audience`,`description`,`start_at`,`end_at`,`status`,`created_at`,`updated_at`,`created_by`)
VALUES
  (101, '[DỮ LIỆU THỬ] Trải nghiệm mua sắm – đợt 1 (SQL)', 'BADMINTON_SHOP_EXPERIENCE_V1', 'SATISFACTION', '{}', 'Dữ liệu thử cho báo cáo – có thể xóa bằng --clear.', '2026-04-25 08:00:00', '2026-12-31 23:59:00', 'ACTIVE', '2026-04-25 08:00:00', '2026-04-25 08:00:00', (SELECT account_id FROM (SELECT account_id FROM accounts WHERE role IN ('MANAGER','ADMIN') ORDER BY account_id LIMIT 1) x)),
  (102, '[DỮ LIỆU THỬ] Trải nghiệm mua sắm – đợt 2 (SQL)', 'BADMINTON_SHOP_EXPERIENCE_V1', 'SATISFACTION', '{}', 'Dữ liệu thử cho báo cáo – có thể xóa bằng --clear.', '2026-08-20 08:00:00', '2026-12-31 23:59:00', 'ACTIVE', '2026-08-20 08:00:00', '2026-08-20 08:00:00', (SELECT account_id FROM (SELECT account_id FROM accounts WHERE role IN ('MANAGER','ADMIN') ORDER BY account_id LIMIT 1) x));

-- 5) 8 câu hỏi × 2 khảo sát (cột config lưu key câu hỏi, thang điểm, số lựa chọn tối đa, option 'Khác')
INSERT IGNORE INTO `survey_questions` (`question_id`, `question_text`, `question_type`, `is_required`, `sort_order`, `survey_id`, `config`) VALUES
  (1001, 'Hôm nay bạn đã mua sản phẩm hoặc sử dụng dịch vụ nào tại shop?', 'MULTI_CHOICE', 1, 1, 101, '{"key": "purchases", "section": "Phần 1: Phân loại khách hàng & Nhu cầu"}'),
  (1002, 'Phong cách hoặc tần suất chơi cầu lông hiện tại của bạn là gì?', 'SINGLE_CHOICE', 1, 2, 101, '{"key": "playing_frequency", "section": "Phần 1: Phân loại khách hàng & Nhu cầu"}'),
  (1003, 'Nhìn chung, bạn hài lòng như thế nào với trải nghiệm tại shop hôm nay?', 'RATING', 1, 3, 101, '{"key": "overall_satisfaction", "section": "Phần 2: Đánh giá Chất lượng Sản phẩm & Dịch vụ", "rating_min": 1, "rating_max": 5}'),
  (1004, 'Bạn đánh giá chi tiết các yếu tố sau của shop ở mức độ nào?', 'MATRIX', 1, 4, 101, '{"key": "service_criteria", "section": "Phần 2: Đánh giá Chất lượng Sản phẩm & Dịch vụ"}'),
  (1005, 'Điều gì làm bạn ưng ý nhất khi mua đồ tại shop?', 'MULTI_CHOICE', 1, 5, 101, '{"key": "highlights", "section": "Phần 2: Đánh giá Chất lượng Sản phẩm & Dịch vụ", "max_selections": 3}'),
  (1006, 'Bạn mong muốn shop nhập thêm nhiều mẫu mới của thương hiệu nào trong thời gian tới?', 'MULTI_CHOICE', 1, 6, 101, '{"key": "future_brands", "section": "Phần 3: Định hướng Sản phẩm & Góp ý mở", "other_option_id": 2024}'),
  (1007, 'Bạn có sẵn sàng giới thiệu shop cho đồng đội hoặc hội nhóm đánh cầu của mình không?', 'RATING', 1, 7, 101, '{"key": "recommendation", "section": "Phần 3: Định hướng Sản phẩm & Góp ý mở", "rating_min": 1, "rating_max": 10}'),
  (1008, 'Bạn có góp ý gì thêm để shop cải thiện dịch vụ phục vụ anh em lông thủ tốt hơn không?', 'TEXT', 0, 8, 101, '{"key": "suggestions", "section": "Phần 3: Định hướng Sản phẩm & Góp ý mở", "placeholder": "Ví dụ: Cần đan vợt lấy liền nhanh hơn, nhập thêm mẫu giày size lớn, cải thiện khâu đóng gói..."}'),
  (1101, 'Hôm nay bạn đã mua sản phẩm hoặc sử dụng dịch vụ nào tại shop?', 'MULTI_CHOICE', 1, 1, 102, '{"key": "purchases", "section": "Phần 1: Phân loại khách hàng & Nhu cầu"}'),
  (1102, 'Phong cách hoặc tần suất chơi cầu lông hiện tại của bạn là gì?', 'SINGLE_CHOICE', 1, 2, 102, '{"key": "playing_frequency", "section": "Phần 1: Phân loại khách hàng & Nhu cầu"}'),
  (1103, 'Nhìn chung, bạn hài lòng như thế nào với trải nghiệm tại shop hôm nay?', 'RATING', 1, 3, 102, '{"key": "overall_satisfaction", "section": "Phần 2: Đánh giá Chất lượng Sản phẩm & Dịch vụ", "rating_min": 1, "rating_max": 5}'),
  (1104, 'Bạn đánh giá chi tiết các yếu tố sau của shop ở mức độ nào?', 'MATRIX', 1, 4, 102, '{"key": "service_criteria", "section": "Phần 2: Đánh giá Chất lượng Sản phẩm & Dịch vụ"}'),
  (1105, 'Điều gì làm bạn ưng ý nhất khi mua đồ tại shop?', 'MULTI_CHOICE', 1, 5, 102, '{"key": "highlights", "section": "Phần 2: Đánh giá Chất lượng Sản phẩm & Dịch vụ", "max_selections": 3}'),
  (1106, 'Bạn mong muốn shop nhập thêm nhiều mẫu mới của thương hiệu nào trong thời gian tới?', 'MULTI_CHOICE', 1, 6, 102, '{"key": "future_brands", "section": "Phần 3: Định hướng Sản phẩm & Góp ý mở", "other_option_id": 2124}'),
  (1107, 'Bạn có sẵn sàng giới thiệu shop cho đồng đội hoặc hội nhóm đánh cầu của mình không?', 'RATING', 1, 7, 102, '{"key": "recommendation", "section": "Phần 3: Định hướng Sản phẩm & Góp ý mở", "rating_min": 1, "rating_max": 10}'),
  (1108, 'Bạn có góp ý gì thêm để shop cải thiện dịch vụ phục vụ anh em lông thủ tốt hơn không?', 'TEXT', 0, 8, 102, '{"key": "suggestions", "section": "Phần 3: Định hướng Sản phẩm & Góp ý mở", "placeholder": "Ví dụ: Cần đan vợt lấy liền nhanh hơn, nhập thêm mẫu giày size lớn, cải thiện khâu đóng gói..."}');

-- 6) Các lựa chọn (thứ tự sort_order bắt đầu từ 1 – báo cáo nhận diện lựa chọn theo vị trí)
INSERT IGNORE INTO `survey_options` (`option_id`, `option_text`, `sort_order`, `question_id`) VALUES
  (2001, 'Vợt cầu lông.', 1, 1001),
  (2002, 'Giày cầu lông.', 2, 1001),
  (2003, 'Quần áo / Balo / Bao vợt.', 3, 1001),
  (2004, 'Phụ kiện (Ống cầu, quấn cán, vớ, băng bảo vệ...).', 4, 1001),
  (2005, 'Dịch vụ đan / căng cước vợt.', 5, 1001),
  (2006, 'Người mới bắt đầu chơi (Newbie).', 1, 1002),
  (2007, 'Chơi phong trào, rèn luyện sức khỏe (1–3 buổi/tuần).', 2, 1002),
  (2008, 'Chơi nâng cao / Đánh giải phong trào (> 3 buổi/tuần).', 3, 1002),
  (2009, 'Mua làm quà tặng cho người khác.', 4, 1002),
  (2010, 'Sản phẩm: Độ đa dạng mẫu mã & cam kết chính hãng.', 1, 1004),
  (2011, 'Tư vấn: Nhân viên hiểu rõ thông số vợt/giày, tư vấn đúng trình độ và lối đánh (công/thủ).', 2, 1004),
  (2012, 'Dịch vụ đan vợt: Căng chuẩn số kg, đi dây đẹp, thời gian chờ lấy vợt nhanh.', 3, 1004),
  (2013, 'Giá cả: Mức giá hợp lý, chương trình khuyến mãi/tích điểm hấp dẫn.', 4, 1004),
  (2014, 'Hàng chuẩn chính hãng.', 1, 1005),
  (2015, 'Thợ đan vợt mát tay, chuẩn kg.', 2, 1005),
  (2016, 'Tư vấn nhiệt tình, không chèo kéo.', 3, 1005),
  (2017, 'Giao hàng nhanh.', 4, 1005),
  (2018, 'Giá tốt / Tặng kèm phụ kiện xịn.', 5, 1005),
  (2019, 'Yonex.', 1, 1006),
  (2020, 'Lining.', 2, 1006),
  (2021, 'Victor.', 3, 1006),
  (2022, 'Mizuno.', 4, 1006),
  (2023, 'Các hãng tầm trung/giá rẻ (Kumpoo, Felet, Vicleo, Kawasaki...).', 5, 1006),
  (2024, 'Khác.', 6, 1006),
  (2101, 'Vợt cầu lông.', 1, 1101),
  (2102, 'Giày cầu lông.', 2, 1101),
  (2103, 'Quần áo / Balo / Bao vợt.', 3, 1101),
  (2104, 'Phụ kiện (Ống cầu, quấn cán, vớ, băng bảo vệ...).', 4, 1101),
  (2105, 'Dịch vụ đan / căng cước vợt.', 5, 1101),
  (2106, 'Người mới bắt đầu chơi (Newbie).', 1, 1102),
  (2107, 'Chơi phong trào, rèn luyện sức khỏe (1–3 buổi/tuần).', 2, 1102),
  (2108, 'Chơi nâng cao / Đánh giải phong trào (> 3 buổi/tuần).', 3, 1102),
  (2109, 'Mua làm quà tặng cho người khác.', 4, 1102),
  (2110, 'Sản phẩm: Độ đa dạng mẫu mã & cam kết chính hãng.', 1, 1104),
  (2111, 'Tư vấn: Nhân viên hiểu rõ thông số vợt/giày, tư vấn đúng trình độ và lối đánh (công/thủ).', 2, 1104),
  (2112, 'Dịch vụ đan vợt: Căng chuẩn số kg, đi dây đẹp, thời gian chờ lấy vợt nhanh.', 3, 1104),
  (2113, 'Giá cả: Mức giá hợp lý, chương trình khuyến mãi/tích điểm hấp dẫn.', 4, 1104),
  (2114, 'Hàng chuẩn chính hãng.', 1, 1105),
  (2115, 'Thợ đan vợt mát tay, chuẩn kg.', 2, 1105),
  (2116, 'Tư vấn nhiệt tình, không chèo kéo.', 3, 1105),
  (2117, 'Giao hàng nhanh.', 4, 1105),
  (2118, 'Giá tốt / Tặng kèm phụ kiện xịn.', 5, 1105),
  (2119, 'Yonex.', 1, 1106),
  (2120, 'Lining.', 2, 1106),
  (2121, 'Victor.', 3, 1106),
  (2122, 'Mizuno.', 4, 1106),
  (2123, 'Các hãng tầm trung/giá rẻ (Kumpoo, Felet, Vicleo, Kawasaki...).', 5, 1106),
  (2124, 'Khác.', 6, 1106);

-- 7) Người nhận, phiếu đã nộp và câu trả lời
INSERT IGNORE INTO `survey_recipients` (`recipient_id`, `survey_id`, `customer_id`, `status`, `sent_at`, `opened_at`, `completed_at`) VALUES
  (3001, 101, 126, 'COMPLETED', '2026-04-25 08:26:00', '2026-08-11 15:36:29', '2026-08-11 15:42:29'),
  (3002, 101, 104, 'COMPLETED', '2026-04-25 08:04:00', '2026-06-29 13:19:12', '2026-06-29 13:25:12'),
  (3003, 101, 111, 'COMPLETED', '2026-04-25 08:11:00', '2026-07-23 10:32:15', '2026-07-23 10:38:15'),
  (3004, 101, 125, 'COMPLETED', '2026-04-25 08:25:00', '2026-06-07 04:36:52', '2026-06-07 04:42:52'),
  (3005, 101, 130, 'COMPLETED', '2026-04-25 08:30:00', '2026-05-10 02:35:35', '2026-05-10 02:41:35'),
  (3006, 101, 101, 'COMPLETED', '2026-04-25 08:01:00', '2026-08-04 07:51:04', '2026-08-04 07:57:04'),
  (3007, 101, 128, 'COMPLETED', '2026-04-25 08:28:00', '2026-07-22 03:11:13', '2026-07-22 03:17:13'),
  (3008, 101, 103, 'COMPLETED', '2026-04-25 08:03:00', '2026-05-17 11:22:20', '2026-05-17 11:28:20'),
  (3009, 101, 115, 'COMPLETED', '2026-04-25 08:15:00', '2026-07-20 02:00:54', '2026-07-20 02:06:54'),
  (3010, 101, 113, 'COMPLETED', '2026-04-25 08:13:00', '2026-06-27 14:28:33', '2026-06-27 14:34:33'),
  (3011, 101, 118, 'COMPLETED', '2026-04-25 08:18:00', '2026-05-02 13:36:35', '2026-05-02 13:42:35'),
  (3012, 101, 119, 'COMPLETED', '2026-04-25 08:19:00', '2026-07-08 03:44:20', '2026-07-08 03:50:20'),
  (3013, 102, 105, 'COMPLETED', '2026-08-20 08:05:00', '2026-09-25 16:08:09', '2026-09-25 16:14:09'),
  (3014, 102, 117, 'COMPLETED', '2026-08-20 08:17:00', '2026-09-02 07:17:39', '2026-09-02 07:23:39'),
  (3015, 102, 108, 'COMPLETED', '2026-08-20 08:08:00', '2026-09-23 15:14:57', '2026-09-23 15:20:57'),
  (3016, 102, 112, 'COMPLETED', '2026-08-20 08:12:00', '2026-10-03 19:11:40', '2026-10-03 19:17:40'),
  (3017, 102, 127, 'COMPLETED', '2026-08-20 08:27:00', '2026-10-01 21:12:22', '2026-10-01 21:18:22'),
  (3018, 102, 106, 'COMPLETED', '2026-08-20 08:06:00', '2026-09-17 22:00:47', '2026-09-17 22:06:47'),
  (3019, 102, 121, 'COMPLETED', '2026-08-20 08:21:00', '2026-10-12 12:50:17', '2026-10-12 12:56:17'),
  (3020, 102, 124, 'COMPLETED', '2026-08-20 08:24:00', '2026-10-12 06:46:13', '2026-10-12 06:52:13'),
  (3021, 102, 110, 'COMPLETED', '2026-08-20 08:10:00', '2026-09-30 06:41:49', '2026-09-30 06:47:49'),
  (3022, 102, 107, 'COMPLETED', '2026-08-20 08:07:00', '2026-09-11 16:49:31', '2026-09-11 16:55:31'),
  (3023, 102, 129, 'COMPLETED', '2026-08-20 08:29:00', '2026-10-11 14:07:47', '2026-10-11 14:13:47'),
  (3024, 102, 120, 'COMPLETED', '2026-08-20 08:20:00', '2026-09-24 13:11:05', '2026-09-24 13:17:05'),
  (3025, 102, 114, 'COMPLETED', '2026-08-20 08:14:00', '2026-09-26 14:40:44', '2026-09-26 14:46:44'),
  (3026, 102, 122, 'COMPLETED', '2026-08-20 08:22:00', '2026-09-14 18:31:35', '2026-09-14 18:37:35'),
  (3027, 102, 109, 'SENT', '2026-08-20 08:09:00', NULL, NULL),
  (3028, 102, 102, 'OPENED', '2026-08-20 08:02:00', '2026-08-21 08:02:00', NULL),
  (3029, 102, 123, 'SENT', '2026-08-20 08:23:00', NULL, NULL),
  (3030, 102, 116, 'OPENED', '2026-08-20 08:16:00', '2026-08-21 08:16:00', NULL);
INSERT IGNORE INTO `survey_responses` (`response_id`, `recipient_id`, `status`, `started_at`, `submitted_at`) VALUES
  (4001, 3001, 'SUBMITTED', '2026-08-11 15:37:29', '2026-08-11 15:42:29'),
  (4002, 3002, 'SUBMITTED', '2026-06-29 13:20:12', '2026-06-29 13:25:12'),
  (4003, 3003, 'SUBMITTED', '2026-07-23 10:33:15', '2026-07-23 10:38:15'),
  (4004, 3004, 'SUBMITTED', '2026-06-07 04:37:52', '2026-06-07 04:42:52'),
  (4005, 3005, 'SUBMITTED', '2026-05-10 02:36:35', '2026-05-10 02:41:35'),
  (4006, 3006, 'SUBMITTED', '2026-08-04 07:52:04', '2026-08-04 07:57:04'),
  (4007, 3007, 'SUBMITTED', '2026-07-22 03:12:13', '2026-07-22 03:17:13'),
  (4008, 3008, 'SUBMITTED', '2026-05-17 11:23:20', '2026-05-17 11:28:20'),
  (4009, 3009, 'SUBMITTED', '2026-07-20 02:01:54', '2026-07-20 02:06:54'),
  (4010, 3010, 'SUBMITTED', '2026-06-27 14:29:33', '2026-06-27 14:34:33'),
  (4011, 3011, 'SUBMITTED', '2026-05-02 13:37:35', '2026-05-02 13:42:35'),
  (4012, 3012, 'SUBMITTED', '2026-07-08 03:45:20', '2026-07-08 03:50:20'),
  (4013, 3013, 'SUBMITTED', '2026-09-25 16:09:09', '2026-09-25 16:14:09'),
  (4014, 3014, 'SUBMITTED', '2026-09-02 07:18:39', '2026-09-02 07:23:39'),
  (4015, 3015, 'SUBMITTED', '2026-09-23 15:15:57', '2026-09-23 15:20:57'),
  (4016, 3016, 'SUBMITTED', '2026-10-03 19:12:40', '2026-10-03 19:17:40'),
  (4017, 3017, 'SUBMITTED', '2026-10-01 21:13:22', '2026-10-01 21:18:22'),
  (4018, 3018, 'SUBMITTED', '2026-09-17 22:01:47', '2026-09-17 22:06:47'),
  (4019, 3019, 'SUBMITTED', '2026-10-12 12:51:17', '2026-10-12 12:56:17'),
  (4020, 3020, 'SUBMITTED', '2026-10-12 06:47:13', '2026-10-12 06:52:13'),
  (4021, 3021, 'SUBMITTED', '2026-09-30 06:42:49', '2026-09-30 06:47:49'),
  (4022, 3022, 'SUBMITTED', '2026-09-11 16:50:31', '2026-09-11 16:55:31'),
  (4023, 3023, 'SUBMITTED', '2026-10-11 14:08:47', '2026-10-11 14:13:47'),
  (4024, 3024, 'SUBMITTED', '2026-09-24 13:12:05', '2026-09-24 13:17:05'),
  (4025, 3025, 'SUBMITTED', '2026-09-26 14:41:44', '2026-09-26 14:46:44'),
  (4026, 3026, 'SUBMITTED', '2026-09-14 18:32:35', '2026-09-14 18:37:35');
INSERT IGNORE INTO `survey_answers` (`answer_id`, `response_id`, `question_id`, `option_id`, `rating_value`, `answer_text`, `created_at`) VALUES
  (5001, 4001, 1001, 2001, NULL, NULL, '2026-08-11 15:42:29'),
  (5002, 4001, 1001, 2003, NULL, NULL, '2026-08-11 15:42:29'),
  (5003, 4001, 1002, 2007, NULL, NULL, '2026-08-11 15:42:29'),
  (5004, 4001, 1003, NULL, 5, NULL, '2026-08-11 15:42:29'),
  (5005, 4001, 1004, 2010, 4, NULL, '2026-08-11 15:42:29'),
  (5006, 4001, 1004, 2011, 5, NULL, '2026-08-11 15:42:29'),
  (5007, 4001, 1004, 2012, 4, NULL, '2026-08-11 15:42:29'),
  (5008, 4001, 1004, 2013, 3, NULL, '2026-08-11 15:42:29'),
  (5009, 4001, 1005, 2014, NULL, NULL, '2026-08-11 15:42:29'),
  (5010, 4001, 1006, 2021, NULL, NULL, '2026-08-11 15:42:29'),
  (5011, 4001, 1006, 2022, NULL, NULL, '2026-08-11 15:42:29'),
  (5012, 4001, 1007, NULL, 9, NULL, '2026-08-11 15:42:29'),
  (5013, 4001, 1008, NULL, NULL, 'Mong shop nhập thêm nhiều giày Yonex và Mizuno size lớn.', '2026-08-11 15:42:29'),
  (5014, 4002, 1001, 2001, NULL, NULL, '2026-06-29 13:25:12'),
  (5015, 4002, 1001, 2004, NULL, NULL, '2026-06-29 13:25:12'),
  (5016, 4002, 1001, 2005, NULL, NULL, '2026-06-29 13:25:12'),
  (5017, 4002, 1002, 2007, NULL, NULL, '2026-06-29 13:25:12'),
  (5018, 4002, 1003, NULL, 5, NULL, '2026-06-29 13:25:12'),
  (5019, 4002, 1004, 2010, 5, NULL, '2026-06-29 13:25:12'),
  (5020, 4002, 1004, 2011, 4, NULL, '2026-06-29 13:25:12'),
  (5021, 4002, 1004, 2012, 4, NULL, '2026-06-29 13:25:12'),
  (5022, 4002, 1004, 2013, NULL, 'NOT_USED', '2026-06-29 13:25:12'),
  (5023, 4002, 1005, 2015, NULL, NULL, '2026-06-29 13:25:12'),
  (5024, 4002, 1005, 2016, NULL, NULL, '2026-06-29 13:25:12'),
  (5025, 4002, 1005, 2018, NULL, NULL, '2026-06-29 13:25:12'),
  (5026, 4002, 1006, 2021, NULL, NULL, '2026-06-29 13:25:12'),
  (5027, 4002, 1007, NULL, 9, NULL, '2026-06-29 13:25:12'),
  (5028, 4002, 1008, NULL, NULL, 'Giá hơi cao so với mặt bằng chung, mong có thêm khuyến mãi.', '2026-06-29 13:25:12'),
  (5029, 4003, 1001, 2001, NULL, NULL, '2026-07-23 10:38:15'),
  (5030, 4003, 1001, 2003, NULL, NULL, '2026-07-23 10:38:15'),
  (5031, 4003, 1001, 2005, NULL, NULL, '2026-07-23 10:38:15'),
  (5032, 4003, 1002, 2007, NULL, NULL, '2026-07-23 10:38:15'),
  (5033, 4003, 1003, NULL, 5, NULL, '2026-07-23 10:38:15'),
  (5034, 4003, 1004, 2010, 3, NULL, '2026-07-23 10:38:15'),
  (5035, 4003, 1004, 2011, 4, NULL, '2026-07-23 10:38:15'),
  (5036, 4003, 1004, 2012, 3, NULL, '2026-07-23 10:38:15'),
  (5037, 4003, 1004, 2013, 3, NULL, '2026-07-23 10:38:15'),
  (5038, 4003, 1005, 2016, NULL, NULL, '2026-07-23 10:38:15'),
  (5039, 4003, 1006, 2019, NULL, NULL, '2026-07-23 10:38:15'),
  (5040, 4003, 1006, 2020, NULL, NULL, '2026-07-23 10:38:15'),
  (5041, 4003, 1006, 2024, NULL, 'Apacs', '2026-07-23 10:38:15'),
  (5042, 4003, 1007, NULL, 8, NULL, '2026-07-23 10:38:15'),
  (5043, 4003, 1008, NULL, NULL, 'Căng vợt chuẩn số kg, thợ đan rất khéo.', '2026-07-23 10:38:15'),
  (5044, 4004, 1001, 2003, NULL, NULL, '2026-06-07 04:42:52'),
  (5045, 4004, 1001, 2004, NULL, NULL, '2026-06-07 04:42:52'),
  (5046, 4004, 1002, 2007, NULL, NULL, '2026-06-07 04:42:52'),
  (5047, 4004, 1003, NULL, 4, NULL, '2026-06-07 04:42:52'),
  (5048, 4004, 1004, 2010, 4, NULL, '2026-06-07 04:42:52'),
  (5049, 4004, 1004, 2011, 4, NULL, '2026-06-07 04:42:52'),
  (5050, 4004, 1004, 2012, 4, NULL, '2026-06-07 04:42:52'),
  (5051, 4004, 1004, 2013, 4, NULL, '2026-06-07 04:42:52'),
  (5052, 4004, 1005, 2015, NULL, NULL, '2026-06-07 04:42:52'),
  (5053, 4004, 1006, 2019, NULL, NULL, '2026-06-07 04:42:52'),
  (5054, 4004, 1006, 2023, NULL, NULL, '2026-06-07 04:42:52'),
  (5055, 4004, 1006, 2024, NULL, 'Apacs', '2026-06-07 04:42:52'),
  (5056, 4004, 1007, NULL, 8, NULL, '2026-06-07 04:42:52'),
  (5057, 4005, 1001, 2002, NULL, NULL, '2026-05-10 02:41:35'),
  (5058, 4005, 1001, 2005, NULL, NULL, '2026-05-10 02:41:35'),
  (5059, 4005, 1002, 2008, NULL, NULL, '2026-05-10 02:41:35'),
  (5060, 4005, 1003, NULL, 5, NULL, '2026-05-10 02:41:35'),
  (5061, 4005, 1004, 2010, NULL, 'NOT_USED', '2026-05-10 02:41:35'),
  (5062, 4005, 1004, 2011, 5, NULL, '2026-05-10 02:41:35'),
  (5063, 4005, 1004, 2012, NULL, 'NOT_USED', '2026-05-10 02:41:35'),
  (5064, 4005, 1004, 2013, 3, NULL, '2026-05-10 02:41:35'),
  (5065, 4005, 1005, 2015, NULL, NULL, '2026-05-10 02:41:35'),
  (5066, 4005, 1005, 2017, NULL, NULL, '2026-05-10 02:41:35'),
  (5067, 4005, 1005, 2018, NULL, NULL, '2026-05-10 02:41:35'),
  (5068, 4005, 1006, 2020, NULL, NULL, '2026-05-10 02:41:35'),
  (5069, 4005, 1007, NULL, 8, NULL, '2026-05-10 02:41:35'),
  (5070, 4006, 1001, 2002, NULL, NULL, '2026-08-04 07:57:04'),
  (5071, 4006, 1001, 2005, NULL, NULL, '2026-08-04 07:57:04'),
  (5072, 4006, 1002, 2008, NULL, NULL, '2026-08-04 07:57:04'),
  (5073, 4006, 1003, NULL, 4, NULL, '2026-08-04 07:57:04'),
  (5074, 4006, 1004, 2010, NULL, 'NOT_USED', '2026-08-04 07:57:04'),
  (5075, 4006, 1004, 2011, 5, NULL, '2026-08-04 07:57:04'),
  (5076, 4006, 1004, 2012, NULL, 'NOT_USED', '2026-08-04 07:57:04'),
  (5077, 4006, 1004, 2013, NULL, 'NOT_USED', '2026-08-04 07:57:04'),
  (5078, 4006, 1005, 2015, NULL, NULL, '2026-08-04 07:57:04'),
  (5079, 4006, 1005, 2017, NULL, NULL, '2026-08-04 07:57:04'),
  (5080, 4006, 1005, 2018, NULL, NULL, '2026-08-04 07:57:04'),
  (5081, 4006, 1006, 2020, NULL, NULL, '2026-08-04 07:57:04'),
  (5082, 4006, 1006, 2021, NULL, NULL, '2026-08-04 07:57:04'),
  (5083, 4006, 1007, NULL, 9, NULL, '2026-08-04 07:57:04'),
  (5084, 4006, 1008, NULL, NULL, 'Mong shop nhập thêm nhiều giày Yonex và Mizuno size lớn.', '2026-08-04 07:57:04'),
  (5085, 4007, 1001, 2003, NULL, NULL, '2026-07-22 03:17:13'),
  (5086, 4007, 1001, 2004, NULL, NULL, '2026-07-22 03:17:13'),
  (5087, 4007, 1001, 2005, NULL, NULL, '2026-07-22 03:17:13'),
  (5088, 4007, 1002, 2007, NULL, NULL, '2026-07-22 03:17:13'),
  (5089, 4007, 1003, NULL, 5, NULL, '2026-07-22 03:17:13'),
  (5090, 4007, 1004, 2010, NULL, 'NOT_USED', '2026-07-22 03:17:13'),
  (5091, 4007, 1004, 2011, 3, NULL, '2026-07-22 03:17:13'),
  (5092, 4007, 1004, 2012, 3, NULL, '2026-07-22 03:17:13'),
  (5093, 4007, 1004, 2013, 4, NULL, '2026-07-22 03:17:13'),
  (5094, 4007, 1005, 2014, NULL, NULL, '2026-07-22 03:17:13'),
  (5095, 4007, 1005, 2017, NULL, NULL, '2026-07-22 03:17:13'),
  (5096, 4007, 1006, 2023, NULL, NULL, '2026-07-22 03:17:13'),
  (5097, 4007, 1006, 2024, NULL, 'Apacs', '2026-07-22 03:17:13'),
  (5098, 4007, 1007, NULL, 7, NULL, '2026-07-22 03:17:13'),
  (5099, 4007, 1008, NULL, NULL, 'Cần đan vợt lấy liền nhanh hơn vào cuối tuần.', '2026-07-22 03:17:13'),
  (5100, 4008, 1001, 2001, NULL, NULL, '2026-05-17 11:28:20'),
  (5101, 4008, 1001, 2004, NULL, NULL, '2026-05-17 11:28:20'),
  (5102, 4008, 1002, 2007, NULL, NULL, '2026-05-17 11:28:20'),
  (5103, 4008, 1003, NULL, 5, NULL, '2026-05-17 11:28:20'),
  (5104, 4008, 1004, 2010, 4, NULL, '2026-05-17 11:28:20'),
  (5105, 4008, 1004, 2011, 4, NULL, '2026-05-17 11:28:20'),
  (5106, 4008, 1004, 2012, 4, NULL, '2026-05-17 11:28:20'),
  (5107, 4008, 1004, 2013, 4, NULL, '2026-05-17 11:28:20'),
  (5108, 4008, 1005, 2014, NULL, NULL, '2026-05-17 11:28:20'),
  (5109, 4008, 1005, 2015, NULL, NULL, '2026-05-17 11:28:20'),
  (5110, 4008, 1006, 2019, NULL, NULL, '2026-05-17 11:28:20'),
  (5111, 4008, 1006, 2022, NULL, NULL, '2026-05-17 11:28:20'),
  (5112, 4008, 1007, NULL, 8, NULL, '2026-05-17 11:28:20'),
  (5113, 4008, 1008, NULL, NULL, 'Căng vợt chuẩn số kg, thợ đan rất khéo.', '2026-05-17 11:28:20'),
  (5114, 4009, 1001, 2001, NULL, NULL, '2026-07-20 02:06:54'),
  (5115, 4009, 1001, 2004, NULL, NULL, '2026-07-20 02:06:54'),
  (5116, 4009, 1002, 2009, NULL, NULL, '2026-07-20 02:06:54'),
  (5117, 4009, 1003, NULL, 5, NULL, '2026-07-20 02:06:54'),
  (5118, 4009, 1004, 2010, 4, NULL, '2026-07-20 02:06:54'),
  (5119, 4009, 1004, 2011, 5, NULL, '2026-07-20 02:06:54'),
  (5120, 4009, 1004, 2012, 4, NULL, '2026-07-20 02:06:54'),
  (5121, 4009, 1004, 2013, 4, NULL, '2026-07-20 02:06:54'),
  (5122, 4009, 1005, 2015, NULL, NULL, '2026-07-20 02:06:54'),
  (5123, 4009, 1006, 2020, NULL, NULL, '2026-07-20 02:06:54'),
  (5124, 4009, 1006, 2021, NULL, NULL, '2026-07-20 02:06:54'),
  (5125, 4009, 1006, 2024, NULL, 'Apacs', '2026-07-20 02:06:54'),
  (5126, 4009, 1007, NULL, 10, NULL, '2026-07-20 02:06:54'),
  (5127, 4009, 1008, NULL, NULL, 'Mong shop nhập thêm nhiều giày Yonex và Mizuno size lớn.', '2026-07-20 02:06:54'),
  (5128, 4010, 1001, 2005, NULL, NULL, '2026-06-27 14:34:33'),
  (5129, 4010, 1002, 2008, NULL, NULL, '2026-06-27 14:34:33'),
  (5130, 4010, 1003, NULL, 5, NULL, '2026-06-27 14:34:33'),
  (5131, 4010, 1004, 2010, 5, NULL, '2026-06-27 14:34:33'),
  (5132, 4010, 1004, 2011, NULL, 'NOT_USED', '2026-06-27 14:34:33'),
  (5133, 4010, 1004, 2012, 2, NULL, '2026-06-27 14:34:33'),
  (5134, 4010, 1004, 2013, 5, NULL, '2026-06-27 14:34:33'),
  (5135, 4010, 1005, 2014, NULL, NULL, '2026-06-27 14:34:33'),
  (5136, 4010, 1006, 2021, NULL, NULL, '2026-06-27 14:34:33'),
  (5137, 4010, 1007, NULL, 10, NULL, '2026-06-27 14:34:33'),
  (5138, 4011, 1001, 2002, NULL, NULL, '2026-05-02 13:42:35'),
  (5139, 4011, 1001, 2005, NULL, NULL, '2026-05-02 13:42:35'),
  (5140, 4011, 1002, 2006, NULL, NULL, '2026-05-02 13:42:35'),
  (5141, 4011, 1003, NULL, 5, NULL, '2026-05-02 13:42:35'),
  (5142, 4011, 1004, 2010, NULL, 'NOT_USED', '2026-05-02 13:42:35'),
  (5143, 4011, 1004, 2011, 4, NULL, '2026-05-02 13:42:35'),
  (5144, 4011, 1004, 2012, 5, NULL, '2026-05-02 13:42:35'),
  (5145, 4011, 1004, 2013, 4, NULL, '2026-05-02 13:42:35'),
  (5146, 4011, 1005, 2014, NULL, NULL, '2026-05-02 13:42:35'),
  (5147, 4011, 1006, 2021, NULL, NULL, '2026-05-02 13:42:35'),
  (5148, 4011, 1007, NULL, 8, NULL, '2026-05-02 13:42:35'),
  (5149, 4011, 1008, NULL, NULL, 'Mong shop nhập thêm nhiều giày Yonex và Mizuno size lớn.', '2026-05-02 13:42:35'),
  (5150, 4012, 1001, 2003, NULL, NULL, '2026-07-08 03:50:20'),
  (5151, 4012, 1001, 2004, NULL, NULL, '2026-07-08 03:50:20'),
  (5152, 4012, 1001, 2005, NULL, NULL, '2026-07-08 03:50:20'),
  (5153, 4012, 1002, 2006, NULL, NULL, '2026-07-08 03:50:20'),
  (5154, 4012, 1003, NULL, 5, NULL, '2026-07-08 03:50:20'),
  (5155, 4012, 1004, 2010, 5, NULL, '2026-07-08 03:50:20'),
  (5156, 4012, 1004, 2011, 5, NULL, '2026-07-08 03:50:20'),
  (5157, 4012, 1004, 2012, 2, NULL, '2026-07-08 03:50:20'),
  (5158, 4012, 1004, 2013, 3, NULL, '2026-07-08 03:50:20'),
  (5159, 4012, 1005, 2014, NULL, NULL, '2026-07-08 03:50:20'),
  (5160, 4012, 1005, 2015, NULL, NULL, '2026-07-08 03:50:20'),
  (5161, 4012, 1006, 2021, NULL, NULL, '2026-07-08 03:50:20'),
  (5162, 4012, 1006, 2024, NULL, 'Fleet', '2026-07-08 03:50:20'),
  (5163, 4012, 1007, NULL, 10, NULL, '2026-07-08 03:50:20'),
  (5164, 4013, 1101, 2102, NULL, NULL, '2026-09-25 16:14:09'),
  (5165, 4013, 1101, 2103, NULL, NULL, '2026-09-25 16:14:09'),
  (5166, 4013, 1101, 2105, NULL, NULL, '2026-09-25 16:14:09'),
  (5167, 4013, 1102, 2107, NULL, NULL, '2026-09-25 16:14:09'),
  (5168, 4013, 1103, NULL, 4, NULL, '2026-09-25 16:14:09'),
  (5169, 4013, 1104, 2110, 4, NULL, '2026-09-25 16:14:09'),
  (5170, 4013, 1104, 2111, 4, NULL, '2026-09-25 16:14:09'),
  (5171, 4013, 1104, 2112, 4, NULL, '2026-09-25 16:14:09'),
  (5172, 4013, 1104, 2113, 5, NULL, '2026-09-25 16:14:09'),
  (5173, 4013, 1105, 2115, NULL, NULL, '2026-09-25 16:14:09'),
  (5174, 4013, 1105, 2117, NULL, NULL, '2026-09-25 16:14:09'),
  (5175, 4013, 1106, 2123, NULL, NULL, '2026-09-25 16:14:09'),
  (5176, 4013, 1107, NULL, 1, NULL, '2026-09-25 16:14:09'),
  (5177, 4014, 1101, 2103, NULL, NULL, '2026-09-02 07:23:39'),
  (5178, 4014, 1102, 2107, NULL, NULL, '2026-09-02 07:23:39'),
  (5179, 4014, 1103, NULL, 4, NULL, '2026-09-02 07:23:39'),
  (5180, 4014, 1104, 2110, 4, NULL, '2026-09-02 07:23:39'),
  (5181, 4014, 1104, 2111, NULL, 'NOT_USED', '2026-09-02 07:23:39'),
  (5182, 4014, 1104, 2112, 5, NULL, '2026-09-02 07:23:39'),
  (5183, 4014, 1104, 2113, 4, NULL, '2026-09-02 07:23:39'),
  (5184, 4014, 1105, 2114, NULL, NULL, '2026-09-02 07:23:39'),
  (5185, 4014, 1105, 2116, NULL, NULL, '2026-09-02 07:23:39'),
  (5186, 4014, 1105, 2118, NULL, NULL, '2026-09-02 07:23:39'),
  (5187, 4014, 1106, 2119, NULL, NULL, '2026-09-02 07:23:39'),
  (5188, 4014, 1106, 2120, NULL, NULL, '2026-09-02 07:23:39'),
  (5189, 4014, 1107, NULL, 8, NULL, '2026-09-02 07:23:39'),
  (5190, 4014, 1108, NULL, NULL, 'Nhân viên tư vấn nhiệt tình, có hiểu biết sâu về vợt.', '2026-09-02 07:23:39'),
  (5191, 4015, 1101, 2102, NULL, NULL, '2026-09-23 15:20:57'),
  (5192, 4015, 1101, 2104, NULL, NULL, '2026-09-23 15:20:57'),
  (5193, 4015, 1102, 2107, NULL, NULL, '2026-09-23 15:20:57'),
  (5194, 4015, 1103, NULL, 5, NULL, '2026-09-23 15:20:57'),
  (5195, 4015, 1104, 2110, NULL, 'NOT_USED', '2026-09-23 15:20:57'),
  (5196, 4015, 1104, 2111, 4, NULL, '2026-09-23 15:20:57'),
  (5197, 4015, 1104, 2112, 3, NULL, '2026-09-23 15:20:57'),
  (5198, 4015, 1104, 2113, 3, NULL, '2026-09-23 15:20:57'),
  (5199, 4015, 1105, 2115, NULL, NULL, '2026-09-23 15:20:57'),
  (5200, 4015, 1105, 2116, NULL, NULL, '2026-09-23 15:20:57'),
  (5201, 4015, 1106, 2122, NULL, NULL, '2026-09-23 15:20:57'),
  (5202, 4015, 1106, 2124, NULL, 'Fleet', '2026-09-23 15:20:57'),
  (5203, 4015, 1107, NULL, 6, NULL, '2026-09-23 15:20:57'),
  (5204, 4015, 1108, NULL, NULL, 'Giá hơi cao so với mặt bằng chung, mong có thêm khuyến mãi.', '2026-09-23 15:20:57'),
  (5205, 4016, 1101, 2102, NULL, NULL, '2026-10-03 19:17:40'),
  (5206, 4016, 1101, 2104, NULL, NULL, '2026-10-03 19:17:40'),
  (5207, 4016, 1102, 2106, NULL, NULL, '2026-10-03 19:17:40'),
  (5208, 4016, 1103, NULL, 5, NULL, '2026-10-03 19:17:40'),
  (5209, 4016, 1104, 2110, 5, NULL, '2026-10-03 19:17:40'),
  (5210, 4016, 1104, 2111, 4, NULL, '2026-10-03 19:17:40'),
  (5211, 4016, 1104, 2112, 5, NULL, '2026-10-03 19:17:40'),
  (5212, 4016, 1104, 2113, NULL, 'NOT_USED', '2026-10-03 19:17:40'),
  (5213, 4016, 1105, 2115, NULL, NULL, '2026-10-03 19:17:40'),
  (5214, 4016, 1106, 2122, NULL, NULL, '2026-10-03 19:17:40'),
  (5215, 4016, 1107, NULL, 8, NULL, '2026-10-03 19:17:40'),
  (5216, 4017, 1101, 2102, NULL, NULL, '2026-10-01 21:18:22'),
  (5217, 4017, 1101, 2104, NULL, NULL, '2026-10-01 21:18:22'),
  (5218, 4017, 1101, 2105, NULL, NULL, '2026-10-01 21:18:22'),
  (5219, 4017, 1102, 2107, NULL, NULL, '2026-10-01 21:18:22'),
  (5220, 4017, 1103, NULL, 2, NULL, '2026-10-01 21:18:22'),
  (5221, 4017, 1104, 2110, 5, NULL, '2026-10-01 21:18:22'),
  (5222, 4017, 1104, 2111, 3, NULL, '2026-10-01 21:18:22'),
  (5223, 4017, 1104, 2112, 4, NULL, '2026-10-01 21:18:22'),
  (5224, 4017, 1104, 2113, 5, NULL, '2026-10-01 21:18:22'),
  (5225, 4017, 1105, 2114, NULL, NULL, '2026-10-01 21:18:22'),
  (5226, 4017, 1105, 2118, NULL, NULL, '2026-10-01 21:18:22'),
  (5227, 4017, 1106, 2120, NULL, NULL, '2026-10-01 21:18:22'),
  (5228, 4017, 1106, 2122, NULL, NULL, '2026-10-01 21:18:22'),
  (5229, 4017, 1106, 2123, NULL, NULL, '2026-10-01 21:18:22'),
  (5230, 4017, 1107, NULL, 6, NULL, '2026-10-01 21:18:22'),
  (5231, 4017, 1108, NULL, NULL, 'Đóng gói cẩn thận hơn khi giao hàng.', '2026-10-01 21:18:22'),
  (5232, 4018, 1101, 2102, NULL, NULL, '2026-09-17 22:06:47'),
  (5233, 4018, 1102, 2108, NULL, NULL, '2026-09-17 22:06:47'),
  (5234, 4018, 1103, NULL, 5, NULL, '2026-09-17 22:06:47'),
  (5235, 4018, 1104, 2110, 3, NULL, '2026-09-17 22:06:47'),
  (5236, 4018, 1104, 2111, 5, NULL, '2026-09-17 22:06:47'),
  (5237, 4018, 1104, 2112, NULL, 'NOT_USED', '2026-09-17 22:06:47'),
  (5238, 4018, 1104, 2113, 3, NULL, '2026-09-17 22:06:47'),
  (5239, 4018, 1105, 2118, NULL, NULL, '2026-09-17 22:06:47'),
  (5240, 4018, 1106, 2119, NULL, NULL, '2026-09-17 22:06:47'),
  (5241, 4018, 1107, NULL, 7, NULL, '2026-09-17 22:06:47'),
  (5242, 4019, 1101, 2103, NULL, NULL, '2026-10-12 12:56:17'),
  (5243, 4019, 1101, 2104, NULL, NULL, '2026-10-12 12:56:17'),
  (5244, 4019, 1102, 2108, NULL, NULL, '2026-10-12 12:56:17'),
  (5245, 4019, 1103, NULL, 5, NULL, '2026-10-12 12:56:17'),
  (5246, 4019, 1104, 2110, 2, NULL, '2026-10-12 12:56:17'),
  (5247, 4019, 1104, 2111, 5, NULL, '2026-10-12 12:56:17'),
  (5248, 4019, 1104, 2112, 2, NULL, '2026-10-12 12:56:17'),
  (5249, 4019, 1104, 2113, 5, NULL, '2026-10-12 12:56:17'),
  (5250, 4019, 1105, 2116, NULL, NULL, '2026-10-12 12:56:17'),
  (5251, 4019, 1105, 2117, NULL, NULL, '2026-10-12 12:56:17'),
  (5252, 4019, 1105, 2118, NULL, NULL, '2026-10-12 12:56:17'),
  (5253, 4019, 1106, 2122, NULL, NULL, '2026-10-12 12:56:17'),
  (5254, 4019, 1106, 2123, NULL, NULL, '2026-10-12 12:56:17'),
  (5255, 4019, 1107, NULL, 8, NULL, '2026-10-12 12:56:17'),
  (5256, 4020, 1101, 2104, NULL, NULL, '2026-10-12 06:52:13'),
  (5257, 4020, 1102, 2108, NULL, NULL, '2026-10-12 06:52:13'),
  (5258, 4020, 1103, NULL, 5, NULL, '2026-10-12 06:52:13'),
  (5259, 4020, 1104, 2110, NULL, 'NOT_USED', '2026-10-12 06:52:13'),
  (5260, 4020, 1104, 2111, 4, NULL, '2026-10-12 06:52:13'),
  (5261, 4020, 1104, 2112, NULL, 'NOT_USED', '2026-10-12 06:52:13'),
  (5262, 4020, 1104, 2113, 5, NULL, '2026-10-12 06:52:13'),
  (5263, 4020, 1105, 2114, NULL, NULL, '2026-10-12 06:52:13'),
  (5264, 4020, 1105, 2115, NULL, NULL, '2026-10-12 06:52:13'),
  (5265, 4020, 1105, 2117, NULL, NULL, '2026-10-12 06:52:13'),
  (5266, 4020, 1106, 2119, NULL, NULL, '2026-10-12 06:52:13'),
  (5267, 4020, 1106, 2121, NULL, NULL, '2026-10-12 06:52:13'),
  (5268, 4020, 1106, 2124, NULL, 'Apacs', '2026-10-12 06:52:13'),
  (5269, 4020, 1107, NULL, 1, NULL, '2026-10-12 06:52:13'),
  (5270, 4020, 1108, NULL, NULL, 'Đóng gói cẩn thận hơn khi giao hàng.', '2026-10-12 06:52:13'),
  (5271, 4021, 1101, 2102, NULL, NULL, '2026-09-30 06:47:49'),
  (5272, 4021, 1101, 2105, NULL, NULL, '2026-09-30 06:47:49'),
  (5273, 4021, 1102, 2108, NULL, NULL, '2026-09-30 06:47:49'),
  (5274, 4021, 1103, NULL, 3, NULL, '2026-09-30 06:47:49'),
  (5275, 4021, 1104, 2110, NULL, 'NOT_USED', '2026-09-30 06:47:49'),
  (5276, 4021, 1104, 2111, 4, NULL, '2026-09-30 06:47:49'),
  (5277, 4021, 1104, 2112, 5, NULL, '2026-09-30 06:47:49'),
  (5278, 4021, 1104, 2113, 4, NULL, '2026-09-30 06:47:49'),
  (5279, 4021, 1105, 2114, NULL, NULL, '2026-09-30 06:47:49'),
  (5280, 4021, 1105, 2115, NULL, NULL, '2026-09-30 06:47:49'),
  (5281, 4021, 1106, 2122, NULL, NULL, '2026-09-30 06:47:49'),
  (5282, 4021, 1107, NULL, 7, NULL, '2026-09-30 06:47:49'),
  (5283, 4021, 1108, NULL, NULL, 'Cần đan vợt lấy liền nhanh hơn vào cuối tuần.', '2026-09-30 06:47:49'),
  (5284, 4022, 1101, 2102, NULL, NULL, '2026-09-11 16:55:31'),
  (5285, 4022, 1101, 2104, NULL, NULL, '2026-09-11 16:55:31'),
  (5286, 4022, 1101, 2105, NULL, NULL, '2026-09-11 16:55:31'),
  (5287, 4022, 1102, 2107, NULL, NULL, '2026-09-11 16:55:31'),
  (5288, 4022, 1103, NULL, 4, NULL, '2026-09-11 16:55:31'),
  (5289, 4022, 1104, 2110, 5, NULL, '2026-09-11 16:55:31'),
  (5290, 4022, 1104, 2111, 5, NULL, '2026-09-11 16:55:31'),
  (5291, 4022, 1104, 2112, 2, NULL, '2026-09-11 16:55:31'),
  (5292, 4022, 1104, 2113, 4, NULL, '2026-09-11 16:55:31'),
  (5293, 4022, 1105, 2116, NULL, NULL, '2026-09-11 16:55:31'),
  (5294, 4022, 1105, 2118, NULL, NULL, '2026-09-11 16:55:31'),
  (5295, 4022, 1106, 2119, NULL, NULL, '2026-09-11 16:55:31'),
  (5296, 4022, 1106, 2120, NULL, NULL, '2026-09-11 16:55:31'),
  (5297, 4022, 1106, 2122, NULL, NULL, '2026-09-11 16:55:31'),
  (5298, 4022, 1107, NULL, 7, NULL, '2026-09-11 16:55:31'),
  (5299, 4023, 1101, 2102, NULL, NULL, '2026-10-11 14:13:47'),
  (5300, 4023, 1101, 2104, NULL, NULL, '2026-10-11 14:13:47'),
  (5301, 4023, 1102, 2107, NULL, NULL, '2026-10-11 14:13:47'),
  (5302, 4023, 1103, NULL, 3, NULL, '2026-10-11 14:13:47'),
  (5303, 4023, 1104, 2110, 4, NULL, '2026-10-11 14:13:47'),
  (5304, 4023, 1104, 2111, 5, NULL, '2026-10-11 14:13:47'),
  (5305, 4023, 1104, 2112, 4, NULL, '2026-10-11 14:13:47'),
  (5306, 4023, 1104, 2113, 4, NULL, '2026-10-11 14:13:47'),
  (5307, 4023, 1105, 2115, NULL, NULL, '2026-10-11 14:13:47'),
  (5308, 4023, 1106, 2124, NULL, 'Apacs', '2026-10-11 14:13:47'),
  (5309, 4023, 1107, NULL, 7, NULL, '2026-10-11 14:13:47'),
  (5310, 4024, 1101, 2101, NULL, NULL, '2026-09-24 13:17:05'),
  (5311, 4024, 1102, 2107, NULL, NULL, '2026-09-24 13:17:05'),
  (5312, 4024, 1103, NULL, 4, NULL, '2026-09-24 13:17:05'),
  (5313, 4024, 1104, 2110, NULL, 'NOT_USED', '2026-09-24 13:17:05'),
  (5314, 4024, 1104, 2111, 4, NULL, '2026-09-24 13:17:05'),
  (5315, 4024, 1104, 2112, 4, NULL, '2026-09-24 13:17:05'),
  (5316, 4024, 1104, 2113, NULL, 'NOT_USED', '2026-09-24 13:17:05'),
  (5317, 4024, 1105, 2116, NULL, NULL, '2026-09-24 13:17:05'),
  (5318, 4024, 1106, 2121, NULL, NULL, '2026-09-24 13:17:05'),
  (5319, 4024, 1106, 2123, NULL, NULL, '2026-09-24 13:17:05'),
  (5320, 4024, 1107, NULL, 7, NULL, '2026-09-24 13:17:05'),
  (5321, 4025, 1101, 2101, NULL, NULL, '2026-09-26 14:46:44'),
  (5322, 4025, 1101, 2103, NULL, NULL, '2026-09-26 14:46:44'),
  (5323, 4025, 1101, 2104, NULL, NULL, '2026-09-26 14:46:44'),
  (5324, 4025, 1102, 2107, NULL, NULL, '2026-09-26 14:46:44'),
  (5325, 4025, 1103, NULL, 3, NULL, '2026-09-26 14:46:44'),
  (5326, 4025, 1104, 2110, 3, NULL, '2026-09-26 14:46:44'),
  (5327, 4025, 1104, 2111, 2, NULL, '2026-09-26 14:46:44'),
  (5328, 4025, 1104, 2112, 5, NULL, '2026-09-26 14:46:44'),
  (5329, 4025, 1104, 2113, 2, NULL, '2026-09-26 14:46:44'),
  (5330, 4025, 1105, 2114, NULL, NULL, '2026-09-26 14:46:44'),
  (5331, 4025, 1105, 2116, NULL, NULL, '2026-09-26 14:46:44'),
  (5332, 4025, 1105, 2117, NULL, NULL, '2026-09-26 14:46:44'),
  (5333, 4025, 1106, 2120, NULL, NULL, '2026-09-26 14:46:44'),
  (5334, 4025, 1107, NULL, 7, NULL, '2026-09-26 14:46:44'),
  (5335, 4026, 1101, 2103, NULL, NULL, '2026-09-14 18:37:35'),
  (5336, 4026, 1102, 2108, NULL, NULL, '2026-09-14 18:37:35'),
  (5337, 4026, 1103, NULL, 5, NULL, '2026-09-14 18:37:35'),
  (5338, 4026, 1104, 2110, 4, NULL, '2026-09-14 18:37:35'),
  (5339, 4026, 1104, 2111, 5, NULL, '2026-09-14 18:37:35'),
  (5340, 4026, 1104, 2112, 3, NULL, '2026-09-14 18:37:35'),
  (5341, 4026, 1104, 2113, 3, NULL, '2026-09-14 18:37:35'),
  (5342, 4026, 1105, 2114, NULL, NULL, '2026-09-14 18:37:35'),
  (5343, 4026, 1106, 2123, NULL, NULL, '2026-09-14 18:37:35'),
  (5344, 4026, 1106, 2124, NULL, 'Apacs', '2026-09-14 18:37:35'),
  (5345, 4026, 1107, NULL, 9, NULL, '2026-09-14 18:37:35');

-- 8) ĐỒNG BỘ SỞ THÍCH TỪ KHẢO SÁT -> hồ sơ khách (báo cáo "Sở thích" chỉ đọc customer_preferences).
--    Chạy lại được bất cứ lúc nào có phiếu mới của bộ câu hỏi V1.
--    Q1 purchases      -> CATEGORY (vợt/giày/quần áo/phụ kiện)   [dịch vụ đan vợt không có nhóm hàng nên bỏ qua]
--    Q6 future_brands  -> BRAND (Yonex, Li-Ning, Victor, Mizuno; ô "Khác" chỉ lấy khi gõ Apacs/Kumpoo)
--    Q2 playing_freq.  -> accounts.playing_level (BEGINNER / RECREATIONAL / COMPETITIVE; "mua quà" giữ nguyên)
INSERT INTO customer_preferences (preference_type, preference_value, customer_id)
SELECT s.ptype, s.pvalue, s.customer_id
FROM (
  SELECT DISTINCT
    CASE k.qkey WHEN 'purchases' THEN 'CATEGORY' ELSE 'BRAND' END AS ptype,
    CASE
      WHEN k.qkey = 'purchases' AND o.sort_order = 1 THEN 'Badminton rackets'
      WHEN k.qkey = 'purchases' AND o.sort_order = 2 THEN 'Badminton shoes'
      WHEN k.qkey = 'purchases' AND o.sort_order = 3 THEN 'Badminton apparel'
      WHEN k.qkey = 'purchases' AND o.sort_order = 4 THEN 'Shuttlecocks'
      WHEN k.qkey = 'future_brands' AND o.sort_order = 1 THEN 'Yonex'
      WHEN k.qkey = 'future_brands' AND o.sort_order = 2 THEN 'Li-Ning'
      WHEN k.qkey = 'future_brands' AND o.sort_order = 3 THEN 'Victor'
      WHEN k.qkey = 'future_brands' AND o.sort_order = 4 THEN 'Mizuno'
      WHEN k.qkey = 'future_brands' AND o.sort_order = 6 AND a.answer_text LIKE 'Apacs%'  THEN 'Apacs'
      WHEN k.qkey = 'future_brands' AND o.sort_order = 6 AND a.answer_text LIKE 'Kumpoo%' THEN 'Kumpoo'
    END AS pvalue,
    rc.customer_id
  FROM survey_answers a
  JOIN (SELECT question_id, JSON_UNQUOTE(JSON_EXTRACT(config, '$.key')) AS qkey FROM survey_questions) k
        ON k.question_id = a.question_id AND k.qkey IN ('purchases', 'future_brands')
  JOIN survey_options    o  ON o.option_id = a.option_id
  JOIN survey_responses  r  ON r.response_id = a.response_id AND r.status = 'SUBMITTED'
  JOIN survey_recipients rc ON rc.recipient_id = r.recipient_id
  JOIN surveys           sv ON sv.survey_id = rc.survey_id AND sv.template_key = 'BADMINTON_SHOP_EXPERIENCE_V1'
) s
WHERE s.pvalue IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM customer_preferences p WHERE p.customer_id = s.customer_id
                  AND p.preference_type = s.ptype AND p.preference_value = s.pvalue);

UPDATE accounts a
JOIN (
  SELECT rc.customer_id,
         CAST(SUBSTRING_INDEX(GROUP_CONCAT(o.sort_order ORDER BY r.submitted_at DESC), ',', 1) AS UNSIGNED) AS pos
  FROM survey_answers a
  JOIN (SELECT question_id FROM survey_questions
        WHERE JSON_UNQUOTE(JSON_EXTRACT(config, '$.key')) = 'playing_frequency') k ON k.question_id = a.question_id
  JOIN survey_options    o  ON o.option_id = a.option_id
  JOIN survey_responses  r  ON r.response_id = a.response_id AND r.status = 'SUBMITTED'
  JOIN survey_recipients rc ON rc.recipient_id = r.recipient_id
  GROUP BY rc.customer_id
) x ON x.customer_id = a.account_id
SET a.playing_level = CASE x.pos WHEN 1 THEN 'BEGINNER' WHEN 2 THEN 'RECREATIONAL'
                                 WHEN 3 THEN 'COMPETITIVE' ELSE a.playing_level END
WHERE a.email LIKE '%@survey-report-demo.test';

COMMIT;
SET FOREIGN_KEY_CHECKS = 1;

-- KIỂM TRA NHANH (chạy tay)
-- SELECT (SELECT COUNT(*) FROM accounts WHERE full_name LIKE '[Thử]%') AS test_customers,
--        (SELECT COUNT(*) FROM survey_recipients WHERE survey_id IN (101,102)) AS sent,
--        (SELECT COUNT(*) FROM survey_responses WHERE status='SUBMITTED' AND recipient_id BETWEEN 3001 AND 3099) AS done;
-- SELECT preference_type, preference_value, COUNT(*) FROM customer_preferences GROUP BY 1,2 ORDER BY 1,3 DESC;

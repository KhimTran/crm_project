-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: crm_db
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounts`
--

DROP TABLE IF EXISTS `accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts` (
  `account_id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `last_login_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `full_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `playing_level` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`account_id`),
  UNIQUE KEY `uq_accounts_email` (`email`),
  KEY `idx_accounts_role` (`role`),
  CONSTRAINT `fk_accounts_role` FOREIGN KEY (`role`) REFERENCES `roles` (`role_code`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_accounts_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'LOCKED')))
) ENGINE=InnoDB AUTO_INCREMENT=48 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts`
--

LOCK TABLES `accounts` WRITE;
/*!40000 ALTER TABLE `accounts` DISABLE KEYS */;
INSERT INTO `accounts` VALUES (1,'demo-admin@example.test','pbkdf2_sha256$1000000$erQI2JiefbNHET6B9B2y6u$Sm8aQVT+AlNktOqm1NLKScZpiufFa8xKB9GbLWNidnw=','ADMIN','ACTIVE',NULL,'2026-10-16 08:20:14','2026-10-20 00:06:28','Nguyễn Văn Quản Trị','0901000001','1985-05-15','MALE','123 Lê Lợi, Quận 1, TP. Hồ Chí Minh',NULL),(2,'demo-customer@example.test','pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:14','2026-10-20 00:06:28','Demo customer',NULL,NULL,NULL,NULL,NULL),(3,'kh01@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:14','2026-10-20 00:06:28','Trần Minh Khoa','0912000001','2007-08-16','MALE','Quận Bình Thạnh, TP. Hồ Chí Minh','RECREATIONAL'),(4,'kh02@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Lê Thu Trang','0912000002','2005-01-04','FEMALE','Thủ Đức, TP. Hồ Chí Minh','RECREATIONAL'),(5,'kh03@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Phạm Quang Hải','0912000003','2003-09-04','MALE','Cầu Giấy, Hà Nội','COMPETITIVE'),(6,'kh04@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Hoàng Bảo Ngọc','0912000004','2000-02-07','FEMALE','Đống Đa, Hà Nội','BEGINNER'),(7,'kh05@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Huỳnh Tuấn Kiệt','0912000005','1998-01-26','MALE','Hải Châu, Đà Nẵng','RECREATIONAL'),(8,'kh06@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Phan Mỹ Linh','0912000006','1995-05-19','FEMALE','Ninh Kiều, Cần Thơ','RECREATIONAL'),(9,'kh07@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Vũ Thành Đạt','0912000007','1993-10-03','MALE','Biên Hòa, Đồng Nai','COMPETITIVE'),(10,'kh08@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Võ Hồng Nhung','0912000008','1990-01-05','FEMALE','Quận 1, TP. Hồ Chí Minh','BEGINNER'),(11,'kh09@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Đặng Công Danh','0912000009','1987-01-20','MALE','Quận Bình Thạnh, TP. Hồ Chí Minh','RECREATIONAL'),(12,'kh10@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Bùi Thị Bình','0912000010','1984-08-10','FEMALE','Thủ Đức, TP. Hồ Chí Minh','RECREATIONAL'),(13,'kh11@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Đỗ Minh Khoa','0912000011','1980-02-18','OTHER','Cầu Giấy, Hà Nội','COMPETITIVE'),(14,'kh12@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Hồ Thu Trang','0912000012','1977-02-24','FEMALE','Đống Đa, Hà Nội','BEGINNER'),(15,'kh13@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Ngô Quang Hải','0912000013',NULL,'MALE','Hải Châu, Đà Nẵng','RECREATIONAL'),(16,'kh14@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Nguyễn Bảo Ngọc','0912000014','1969-10-11','FEMALE','Ninh Kiều, Cần Thơ','RECREATIONAL'),(17,'kh15@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Trần Tuấn Kiệt','0912000015','1964-04-14','MALE','Biên Hòa, Đồng Nai','COMPETITIVE'),(18,'kh16@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Lê Mỹ Linh','0912000016','2010-03-07','FEMALE','Quận 1, TP. Hồ Chí Minh','BEGINNER'),(19,'kh17@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Phạm Thành Đạt','0912000017','2007-01-25','MALE','Quận Bình Thạnh, TP. Hồ Chí Minh',NULL),(20,'kh18@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Hoàng Hồng Nhung','0912000018','2005-09-13','FEMALE','Thủ Đức, TP. Hồ Chí Minh','RECREATIONAL'),(21,'kh19@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Huỳnh Công Danh','0912000019','2003-08-02','MALE','Cầu Giấy, Hà Nội','COMPETITIVE'),(22,'kh20@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Phan Thị Bình','0912000020','2000-01-10','FEMALE','Đống Đa, Hà Nội','BEGINNER'),(23,'kh21@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Vũ Minh Khoa','0912000021','1998-09-23','MALE','Hải Châu, Đà Nẵng','RECREATIONAL'),(24,'kh22@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Võ Đức Huy','0912000022','1994-12-21','OTHER','Ninh Kiều, Cần Thơ','RECREATIONAL'),(25,'kh23@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Đặng Quang Hải','0912000023','1993-01-30','MALE','Biên Hòa, Đồng Nai','COMPETITIVE'),(26,'kh24@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Bùi Bảo Ngọc','0912000024','1990-01-29','FEMALE','Quận 1, TP. Hồ Chí Minh','BEGINNER'),(27,'kh25@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Đỗ Tuấn Kiệt','0912000025','1987-08-22','MALE','Quận Bình Thạnh, TP. Hồ Chí Minh','RECREATIONAL'),(28,'kh26@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Hồ Mỹ Linh','0912000026',NULL,'FEMALE','Thủ Đức, TP. Hồ Chí Minh','RECREATIONAL'),(29,'kh27@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Ngô Thành Đạt','0912000027','1980-02-28','MALE','Cầu Giấy, Hà Nội','COMPETITIVE'),(30,'kh28@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Nguyễn Hồng Nhung','0912000028','1977-07-29','FEMALE','Đống Đa, Hà Nội','BEGINNER'),(31,'kh29@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Trần Công Danh','0912000029','1973-09-10','MALE','Hải Châu, Đà Nẵng','RECREATIONAL'),(32,'kh30@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Lê Thị Bình','0912000030','1969-02-26','FEMALE','Ninh Kiều, Cần Thơ','RECREATIONAL'),(33,'kh31@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Phạm Minh Khoa','0912000031','1964-01-18','MALE','Biên Hòa, Đồng Nai','COMPETITIVE'),(34,'kh32@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Hoàng Thu Trang','0912000032','2010-07-12','FEMALE','Quận 1, TP. Hồ Chí Minh','BEGINNER'),(35,'kh33@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Huỳnh Quang Hải','0912000033','2007-07-12','OTHER','Quận Bình Thạnh, TP. Hồ Chí Minh','RECREATIONAL'),(36,'kh34@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Phan Bảo Ngọc','0912000034','2005-02-18','FEMALE','Thủ Đức, TP. Hồ Chí Minh',NULL),(37,'kh35@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Vũ Tuấn Kiệt','0912000035','2003-01-20','MALE','Cầu Giấy, Hà Nội','COMPETITIVE'),(38,'kh36@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Võ Mỹ Linh','0912000036','2000-02-26','FEMALE','Đống Đa, Hà Nội','BEGINNER'),(39,'kh37@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Đặng Thành Đạt','0912000037','1998-04-18','MALE','Hải Châu, Đà Nẵng','RECREATIONAL'),(40,'kh38@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Bùi Hồng Nhung','0912000038','1995-06-28','FEMALE','Ninh Kiều, Cần Thơ','RECREATIONAL'),(41,'kh39@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Đỗ Công Danh','0912000039',NULL,'MALE','Biên Hòa, Đồng Nai','COMPETITIVE'),(42,'kh40@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','LOCKED',NULL,'2026-10-16 08:20:15','2026-10-20 00:06:28','Hồ Thị Bình','0912000040','1990-09-15','FEMALE','Quận 1, TP. Hồ Chí Minh','BEGINNER'),(43,'demo-admin2@example.test','pbkdf2_sha256$1000000$erQI2JiefbNHET6B9B2y6u$Sm8aQVT+AlNktOqm1NLKScZpiufFa8xKB9GbLWNidnw=','ADMIN','ACTIVE',NULL,'2026-10-19 08:00:00','2026-10-20 00:06:28','Trần Thị Hồng Phúc','0901000002','1988-10-20','FEMALE','456 Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh',NULL),(44,'demo-manager1@example.test','pbkdf2_sha256$1000000$erQI2JiefbNHET6B9B2y6u$Sm8aQVT+AlNktOqm1NLKScZpiufFa8xKB9GbLWNidnw=','MANAGER','ACTIVE',NULL,'2026-10-19 08:00:00','2026-10-20 00:06:28','Lê Hoàng Nam','0902000001','1992-03-12','MALE','789 Điện Biên Phủ, Bình Thạnh, TP. Hồ Chí Minh',NULL),(45,'demo-manager2@example.test','pbkdf2_sha256$1000000$erQI2JiefbNHET6B9B2y6u$Sm8aQVT+AlNktOqm1NLKScZpiufFa8xKB9GbLWNidnw=','MANAGER','ACTIVE',NULL,'2026-10-19 08:00:00','2026-10-20 00:06:28','Phạm Thu Hà','0902000002','1994-07-25','FEMALE','101 Võ Thị Sáu, Quận 3, TP. Hồ Chí Minh',NULL),(46,'demo-manager3@example.test','pbkdf2_sha256$1000000$erQI2JiefbNHET6B9B2y6u$Sm8aQVT+AlNktOqm1NLKScZpiufFa8xKB9GbLWNidnw=','MANAGER','ACTIVE',NULL,'2026-10-19 08:00:00','2026-10-20 00:06:28','Đặng Minh Tuấn','0902000003','1991-11-08','MALE','202 Cách Mạng Tháng 8, Quận 10, TP. Hồ Chí Minh',NULL),(47,'testlocked@t.com','pbkdf2_sha256$1000000$ZrEySpUIXtb1kdrvFYpIP2$d7xtSDce5hDCBkB4JIIvPD4zfcM3g+KMzbM279GdnLs=','CUSTOMER','LOCKED','2026-10-19 18:00:50','2026-10-19 18:00:49','2026-10-20 01:00:49','',NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `accounts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_groups`
--

DROP TABLE IF EXISTS `accounts_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_groups_account_id_group_id_f16ff131_uniq` (`account_id`,`group_id`),
  KEY `accounts_groups_group_id_8ed31270_fk_auth_group_id` (`group_id`),
  CONSTRAINT `accounts_groups_account_id_13c99fce_fk_accounts_account_id` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`),
  CONSTRAINT `accounts_groups_group_id_8ed31270_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_groups`
--

LOCK TABLES `accounts_groups` WRITE;
/*!40000 ALTER TABLE `accounts_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `accounts_user_permissions`
--

DROP TABLE IF EXISTS `accounts_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts_user_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `accounts_user_permissions_account_id_permission_id_6b5c0652_uniq` (`account_id`,`permission_id`),
  KEY `accounts_user_permis_permission_id_ef5446eb_fk_auth_perm` (`permission_id`),
  CONSTRAINT `accounts_user_permis_account_id_362b3798_fk_accounts_` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`),
  CONSTRAINT `accounts_user_permis_permission_id_ef5446eb_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts_user_permissions`
--

LOCK TABLES `accounts_user_permissions` WRITE;
/*!40000 ALTER TABLE `accounts_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `accounts_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=89 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add account',6,'add_account'),(22,'Can change account',6,'change_account'),(23,'Can delete account',6,'delete_account'),(24,'Can view account',6,'view_account'),(25,'Can add brand',7,'add_brand'),(26,'Can change brand',7,'change_brand'),(27,'Can delete brand',7,'delete_brand'),(28,'Can view brand',7,'view_brand'),(29,'Can add category',8,'add_category'),(30,'Can change category',8,'change_category'),(31,'Can delete category',8,'delete_category'),(32,'Can view category',8,'view_category'),(37,'Can add product',10,'add_product'),(38,'Can change product',10,'change_product'),(39,'Can delete product',10,'delete_product'),(40,'Can view product',10,'view_product'),(41,'Can add customer',11,'add_customer'),(42,'Can change customer',11,'change_customer'),(43,'Can delete customer',11,'delete_customer'),(44,'Can view customer',11,'view_customer'),(45,'Can add customer preference',12,'add_customerpreference'),(46,'Can change customer preference',12,'change_customerpreference'),(47,'Can delete customer preference',12,'delete_customerpreference'),(48,'Can view customer preference',12,'view_customerpreference'),(49,'Can add feedback',13,'add_feedback'),(50,'Can change feedback',13,'change_feedback'),(51,'Can delete feedback',13,'delete_feedback'),(52,'Can view feedback',13,'view_feedback'),(53,'Can add survey',14,'add_survey'),(54,'Can change survey',14,'change_survey'),(55,'Can delete survey',14,'delete_survey'),(56,'Can view survey',14,'view_survey'),(57,'Can add survey question',15,'add_surveyquestion'),(58,'Can change survey question',15,'change_surveyquestion'),(59,'Can delete survey question',15,'delete_surveyquestion'),(60,'Can view survey question',15,'view_surveyquestion'),(61,'Can add survey option',16,'add_surveyoption'),(62,'Can change survey option',16,'change_surveyoption'),(63,'Can delete survey option',16,'delete_surveyoption'),(64,'Can view survey option',16,'view_surveyoption'),(65,'Can add survey recipient',17,'add_surveyrecipient'),(66,'Can change survey recipient',17,'change_surveyrecipient'),(67,'Can delete survey recipient',17,'delete_surveyrecipient'),(68,'Can view survey recipient',17,'view_surveyrecipient'),(69,'Can add survey response',18,'add_surveyresponse'),(70,'Can change survey response',18,'change_surveyresponse'),(71,'Can delete survey response',18,'delete_surveyresponse'),(72,'Can view survey response',18,'view_surveyresponse'),(73,'Can add survey answer',19,'add_surveyanswer'),(74,'Can change survey answer',19,'change_surveyanswer'),(75,'Can delete survey answer',19,'delete_surveyanswer'),(76,'Can view survey answer',19,'view_surveyanswer'),(77,'Can add role',20,'add_role'),(78,'Can change role',20,'change_role'),(79,'Can delete role',20,'delete_role'),(80,'Can view role',20,'view_role'),(81,'Can add admin',21,'add_admin'),(82,'Can change admin',21,'change_admin'),(83,'Can delete admin',21,'delete_admin'),(84,'Can view admin',21,'view_admin'),(85,'Can add staff',22,'add_staff'),(86,'Can change staff',22,'change_staff'),(87,'Can delete staff',22,'delete_staff'),(88,'Can view staff',22,'view_staff');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `brands`
--

DROP TABLE IF EXISTS `brands`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `brands` (
  `brand_id` int NOT NULL AUTO_INCREMENT,
  `brand_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`brand_id`),
  KEY `idx_brands_name` (`brand_name`),
  KEY `idx_brands_status` (`status`),
  CONSTRAINT `chk_brands_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'INACTIVE')))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `brands`
--

LOCK TABLES `brands` WRITE;
/*!40000 ALTER TABLE `brands` DISABLE KEYS */;
INSERT INTO `brands` VALUES (3,'Yonex','Thương hiệu cầu lông Nhật Bản','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34'),(4,'Lining','Thương hiệu thể thao Trung Quốc','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34'),(5,'Victor','Thương hiệu cầu lông Đài Loan','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34'),(6,'Mizuno','Thương hiệu thể thao Nhật Bản','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34'),(7,'Apacs','Thương hiệu cầu lông Malaysia','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34');
/*!40000 ALTER TABLE `brands` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories`
--

DROP TABLE IF EXISTS `categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories` (
  `category_id` int NOT NULL AUTO_INCREMENT,
  `category_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`category_id`),
  KEY `idx_categories_name` (`category_name`),
  KEY `idx_categories_status` (`status`),
  CONSTRAINT `chk_categories_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'INACTIVE')))
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,'Badminton rackets','Vợt cầu lông các dòng thiên công, thủ và toàn diện','ACTIVE','2026-10-05 09:47:24','2026-10-14 15:03:34'),(5,'Shuttlecocks','Cầu lông thi đấu và tập luyện','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34'),(6,'Badminton shoes','Giày cầu lông','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34'),(7,'Badminton bags','Túi và balo đựng vợt','ACTIVE','2026-10-13 19:44:12','2026-10-14 09:55:10'),(8,'Accessories','Quấn cán, dây cước và phụ kiện','ACTIVE','2026-10-13 19:44:12','2026-10-14 09:55:10'),(9,'Badminton apparel','Quần áo cầu lông','ACTIVE','2026-10-14 10:04:21','2026-10-14 15:03:34');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customer_preferences`
--

DROP TABLE IF EXISTS `customer_preferences`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customer_preferences` (
  `preference_id` int NOT NULL AUTO_INCREMENT,
  `preference_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `preference_value` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `customer_id` int NOT NULL,
  PRIMARY KEY (`preference_id`),
  KEY `idx_customer_preferences_customer` (`customer_id`),
  KEY `idx_customer_preferences_type` (`preference_type`),
  CONSTRAINT `fk_customer_preferences_account` FOREIGN KEY (`customer_id`) REFERENCES `accounts` (`account_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=152 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer_preferences`
--

LOCK TABLES `customer_preferences` WRITE;
/*!40000 ALTER TABLE `customer_preferences` DISABLE KEYS */;
INSERT INTO `customer_preferences` VALUES (1,'CATEGORY','Badminton rackets','2026-10-16 08:20:14',2),(2,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',3),(3,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',3),(4,'BRAND','Kumpoo','2026-10-16 08:20:15',3),(5,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',4),(6,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',4),(7,'BRAND','Mizuno','2026-10-16 08:20:15',4),(8,'BRAND','Victor','2026-10-16 08:20:15',4),(9,'BRAND','Yonex','2026-10-16 08:20:15',4),(10,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',5),(11,'BRAND','Mizuno','2026-10-16 08:20:15',5),(12,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',6),(13,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',6),(14,'BRAND','Li-Ning','2026-10-16 08:20:15',6),(15,'BRAND','VNB','2026-10-16 08:20:15',6),(16,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',7),(17,'BRAND','Kumpoo','2026-10-16 08:20:15',7),(18,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',8),(19,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',8),(20,'BRAND','Apacs','2026-10-16 08:20:15',8),(21,'BRAND','VNB','2026-10-16 08:20:15',8),(22,'BRAND','Kumpoo','2026-10-16 08:20:15',8),(23,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',9),(24,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',9),(25,'BRAND','Yonex','2026-10-16 08:20:15',9),(26,'BRAND','Mizuno','2026-10-16 08:20:15',9),(27,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',10),(28,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',10),(29,'BRAND','VNB','2026-10-16 08:20:15',10),(30,'BRAND','Kumpoo','2026-10-16 08:20:15',10),(31,'BRAND','Mizuno','2026-10-16 08:20:15',10),(32,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',11),(33,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',11),(34,'BRAND','Kumpoo','2026-10-16 08:20:15',11),(35,'BRAND','Yonex','2026-10-16 08:20:15',11),(36,'BRAND','VNB','2026-10-16 08:20:15',11),(37,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',12),(38,'BRAND','Yonex','2026-10-16 08:20:15',12),(39,'BRAND','Apacs','2026-10-16 08:20:15',12),(40,'BRAND','Kumpoo','2026-10-16 08:20:15',12),(41,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',13),(42,'BRAND','VNB','2026-10-16 08:20:15',13),(43,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',14),(44,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',14),(45,'BRAND','Mizuno','2026-10-16 08:20:15',14),(46,'BRAND','Apacs','2026-10-16 08:20:15',14),(47,'BRAND','Li-Ning','2026-10-16 08:20:15',14),(48,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',15),(49,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',15),(50,'BRAND','Li-Ning','2026-10-16 08:20:15',15),(51,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',16),(52,'BRAND','Kumpoo','2026-10-16 08:20:15',16),(53,'BRAND','Mizuno','2026-10-16 08:20:15',16),(54,'BRAND','VNB','2026-10-16 08:20:15',16),(55,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',17),(56,'BRAND','Mizuno','2026-10-16 08:20:15',17),(57,'BRAND','VNB','2026-10-16 08:20:15',17),(58,'BRAND','Kumpoo','2026-10-16 08:20:15',17),(59,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',18),(60,'BRAND','Mizuno','2026-10-16 08:20:15',18),(61,'BRAND','Yonex','2026-10-16 08:20:15',18),(62,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',19),(63,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',19),(64,'BRAND','VNB','2026-10-16 08:20:15',19),(65,'BRAND','Apacs','2026-10-16 08:20:15',19),(66,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',20),(67,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',20),(68,'BRAND','Victor','2026-10-16 08:20:15',20),(69,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',21),(70,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',21),(71,'BRAND','Mizuno','2026-10-16 08:20:15',21),(72,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',22),(73,'BRAND','Victor','2026-10-16 08:20:15',22),(74,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',23),(75,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',23),(76,'BRAND','Li-Ning','2026-10-16 08:20:15',23),(77,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',24),(78,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',24),(79,'BRAND','Kumpoo','2026-10-16 08:20:15',24),(80,'BRAND','Victor','2026-10-16 08:20:15',24),(81,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',25),(82,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',25),(83,'BRAND','Victor','2026-10-16 08:20:15',25),(84,'BRAND','VNB','2026-10-16 08:20:15',25),(85,'BRAND','Kumpoo','2026-10-16 08:20:15',25),(86,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',26),(87,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',26),(88,'BRAND','VNB','2026-10-16 08:20:15',26),(89,'BRAND','Victor','2026-10-16 08:20:15',26),(90,'BRAND','Mizuno','2026-10-16 08:20:15',26),(91,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',27),(92,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',27),(93,'BRAND','Apacs','2026-10-16 08:20:15',27),(94,'BRAND','Li-Ning','2026-10-16 08:20:15',27),(95,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',28),(96,'BRAND','Li-Ning','2026-10-16 08:20:15',28),(97,'BRAND','Apacs','2026-10-16 08:20:15',28),(98,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',29),(99,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',29),(100,'BRAND','Kumpoo','2026-10-16 08:20:15',29),(101,'BRAND','VNB','2026-10-16 08:20:15',29),(102,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',30),(103,'BRAND','Li-Ning','2026-10-16 08:20:15',30),(104,'BRAND','Mizuno','2026-10-16 08:20:15',30),(105,'BRAND','Kumpoo','2026-10-16 08:20:15',30),(106,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',31),(107,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',31),(108,'BRAND','Victor','2026-10-16 08:20:15',31),(109,'BRAND','Yonex','2026-10-16 08:20:15',31),(110,'BRAND','Kumpoo','2026-10-16 08:20:15',31),(111,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',32),(112,'BRAND','Apacs','2026-10-16 08:20:15',32),(113,'BRAND','Yonex','2026-10-16 08:20:15',32),(114,'BRAND','Victor','2026-10-16 08:20:15',32),(115,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',33),(116,'BRAND','Victor','2026-10-16 08:20:15',33),(117,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',34),(118,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',34),(119,'BRAND','Mizuno','2026-10-16 08:20:15',34),(120,'BRAND','Yonex','2026-10-16 08:20:15',34),(121,'BRAND','VNB','2026-10-16 08:20:15',34),(122,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',35),(123,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',35),(124,'BRAND','Mizuno','2026-10-16 08:20:15',35),(125,'BRAND','VNB','2026-10-16 08:20:15',35),(126,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',36),(127,'BRAND','Mizuno','2026-10-16 08:20:15',36),(128,'BRAND','VNB','2026-10-16 08:20:15',36),(129,'BRAND','Yonex','2026-10-16 08:20:15',36),(130,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',37),(131,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',37),(132,'BRAND','Yonex','2026-10-16 08:20:15',37),(133,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',38),(134,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',38),(135,'BRAND','Li-Ning','2026-10-16 08:20:15',38),(136,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',39),(137,'BRAND','Apacs','2026-10-16 08:20:15',39),(138,'BRAND','Li-Ning','2026-10-16 08:20:15',39),(139,'BRAND','Kumpoo','2026-10-16 08:20:15',39),(140,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',40),(141,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',40),(142,'BRAND','Kumpoo','2026-10-16 08:20:15',40),(143,'BRAND','Victor','2026-10-16 08:20:15',40),(144,'BRAND','Yonex','2026-10-16 08:20:15',40),(145,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',41),(146,'BRAND','Yonex','2026-10-16 08:20:15',41),(147,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',42),(148,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',42),(149,'BRAND','Li-Ning','2026-10-16 08:20:15',42),(150,'BRAND','VNB','2026-10-16 08:20:15',42),(151,'BRAND','Kumpoo','2026-10-16 08:20:15',42);
/*!40000 ALTER TABLE `customer_preferences` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `object_repr` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_accounts_account_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_accounts_account_id` FOREIGN KEY (`user_id`) REFERENCES `accounts` (`account_id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (6,'accounts','account'),(21,'accounts','admin'),(20,'accounts','role'),(22,'accounts','staff'),(1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(7,'catalog','brand'),(8,'catalog','category'),(10,'catalog','product'),(4,'contenttypes','contenttype'),(11,'customers','customer'),(12,'customers','customerpreference'),(13,'feedback','feedback'),(5,'sessions','session'),(14,'surveys','survey'),(19,'surveys','surveyanswer'),(16,'surveys','surveyoption'),(15,'surveys','surveyquestion'),(17,'surveys','surveyrecipient'),(18,'surveys','surveyresponse');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-10-16 08:20:08.686117'),(2,'contenttypes','0002_remove_content_type_name','2026-10-16 08:20:08.749661'),(3,'auth','0001_initial','2026-10-16 08:20:08.967706'),(4,'auth','0002_alter_permission_name_max_length','2026-10-16 08:20:09.004704'),(5,'auth','0003_alter_user_email_max_length','2026-10-16 08:20:09.009707'),(6,'auth','0004_alter_user_username_opts','2026-10-16 08:20:09.012713'),(7,'auth','0005_alter_user_last_login_null','2026-10-16 08:20:09.015712'),(8,'auth','0006_require_contenttypes_0002','2026-10-16 08:20:09.016712'),(9,'auth','0007_alter_validators_add_error_messages','2026-10-16 08:20:09.020708'),(10,'auth','0008_alter_user_username_max_length','2026-10-16 08:20:09.024713'),(11,'auth','0009_alter_user_last_name_max_length','2026-10-16 08:20:09.027716'),(12,'auth','0010_alter_group_name_max_length','2026-10-16 08:20:09.033715'),(13,'auth','0011_update_proxy_permissions','2026-10-16 08:20:09.036708'),(14,'auth','0012_alter_user_first_name_max_length','2026-10-16 08:20:09.040708'),(15,'accounts','0001_initial','2026-10-16 08:20:09.220339'),(16,'accounts','0002_remove_account_chk_accounts_role_alter_account_role_and_more','2026-10-16 08:20:09.266874'),(17,'admin','0001_initial','2026-10-16 08:20:09.343261'),(18,'admin','0002_logentry_remove_auto_add','2026-10-16 08:20:09.347266'),(19,'admin','0003_logentry_add_action_flag_choices','2026-10-16 08:20:09.350265'),(20,'catalog','0001_initial','2026-10-16 08:20:09.511780'),(21,'catalog','0002_product_image_url','2026-10-16 08:20:09.543002'),(22,'customers','0001_initial','2026-10-16 08:20:09.636010'),(23,'feedback','0001_initial','2026-10-16 08:20:09.797085'),(24,'sessions','0001_initial','2026-10-16 08:20:09.817090'),(25,'surveys','0001_initial','2026-10-16 08:20:10.288699'),(26,'surveys','0002_schema_contract','2026-10-16 08:20:12.611366'),(27,'accounts','0003_role_admin_staff','2026-10-19 15:30:00.000000'),(29,'surveys','0003_questionnaire_configuration','2026-10-19 17:05:33.894630'),(30,'surveys','0004_survey_objective_audience','2026-10-19 17:05:33.909817'),(31,'accounts','0004_remove_staff_account_account_address_and_more','2026-10-19 17:14:43.700657'),(32,'surveys','0005_alter_surveyrecipient_customer','2026-10-19 17:14:43.718674'),(33,'feedback','0002_alter_feedback_customer_alter_feedback_handled_by','2026-10-19 17:14:43.728946'),(34,'customers','0002_alter_customerpreference_customer_delete_customer_and_more','2026-10-19 17:14:43.745640');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('46n3337sa5g9zb6kglfu78cbgshpg54z','.eJxVjEEOwiAQRe_C2pChpQN16d4zNAMzSNVAUtqV8e7apAvd_vfef6mJtjVPW5NlmlmdlXXq9DsGig8pO-E7lVvVsZZ1mYPeFX3Qpq-V5Xk53L-DTC1_6yA20MghGgeDTx76wK7rwCSUnrxgRCdxSMwERAYSeg-MaGwiMSOq9wcs9zjD:1xIrfF:OyjT97wK471NIul5sRvboknH7jB6-yCujdLlKFZAZI4','2026-11-02 18:00:49.938235');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feedbacks`
--

DROP TABLE IF EXISTS `feedbacks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feedbacks` (
  `feedback_id` int NOT NULL AUTO_INCREMENT,
  `rating` tinyint NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `manager_note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `resolved_at` datetime DEFAULT NULL,
  `customer_id` int NOT NULL,
  `handled_by` int DEFAULT NULL,
  `product_id` int NOT NULL,
  PRIMARY KEY (`feedback_id`),
  KEY `idx_feedbacks_customer` (`customer_id`),
  KEY `idx_feedbacks_product` (`product_id`),
  KEY `idx_feedbacks_status` (`status`),
  KEY `idx_feedbacks_handled_by` (`handled_by`),
  KEY `idx_feedbacks_created_at` (`created_at`),
  CONSTRAINT `fk_feedbacks_customer` FOREIGN KEY (`customer_id`) REFERENCES `accounts` (`account_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_feedbacks_handled_by` FOREIGN KEY (`handled_by`) REFERENCES `accounts` (`account_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_feedbacks_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_feedbacks_rating` CHECK (((`rating` >= 1) and (`rating` <= 5)))
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feedbacks`
--

LOCK TABLES `feedbacks` WRITE;
/*!40000 ALTER TABLE `feedbacks` DISABLE KEYS */;
INSERT INTO `feedbacks` VALUES (1,5,'Good racket','NEW',NULL,'2026-10-16 08:20:14',NULL,2,NULL,78),(2,5,'Khung vợt chắc, đập cầu uy lực, rất hài lòng.','NEW',NULL,'2026-08-11 16:20:15',NULL,3,NULL,78),(3,5,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-06-22 13:20:15','2026-06-25 13:20:15',4,1,79),(4,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','IN_PROGRESS',NULL,'2026-07-06 14:20:15',NULL,5,1,80),(5,2,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-09-15 08:20:15','2026-09-18 08:20:15',6,1,81),(6,5,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','NEW',NULL,'2026-09-09 05:20:15',NULL,7,NULL,82),(7,5,'Vợt nhẹ đầu, phòng thủ phản tạt nhanh, đáng tiền.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-08-13 11:20:15','2026-08-15 11:20:15',8,1,86),(8,4,'Khung vợt chắc, đập cầu uy lực, rất hài lòng.','NEW',NULL,'2026-09-12 21:20:15',NULL,9,NULL,87),(9,3,'Vợt ổn nhưng cước căng hơi chùng sau 2 tuần.','RESOLVED','Cảm ơn góp ý của bạn. Cửa hàng hỗ trợ căng lại cước/đổi size miễn phí, bạn mang sản phẩm qua shop nhé.','2026-07-14 22:20:15','2026-07-15 22:20:15',10,1,88),(10,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','IN_PROGRESS',NULL,'2026-09-08 18:20:15',NULL,11,1,78),(11,4,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-06-28 10:20:15','2026-06-30 10:20:15',12,1,79),(12,3,'Đánh được, tuy nhiên cán hơi to so với tay mình.','NEW',NULL,'2026-08-22 06:20:15',NULL,13,NULL,80),(13,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-06-26 05:20:15','2026-06-28 05:20:15',14,1,81),(14,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','NEW',NULL,'2026-08-25 16:20:15',NULL,15,NULL,82),(15,3,'Đánh được, tuy nhiên cán hơi to so với tay mình.','RESOLVED','Cảm ơn góp ý của bạn. Cửa hàng hỗ trợ căng lại cước/đổi size miễn phí, bạn mang sản phẩm qua shop nhé.','2026-08-10 16:20:15','2026-08-11 16:20:15',16,1,86),(16,4,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','IN_PROGRESS',NULL,'2026-07-03 07:20:15',NULL,17,1,87),(17,1,'Vợt bị nứt khung sau một tháng sử dụng.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-07-15 13:20:15','2026-07-17 13:20:15',18,1,88),(18,2,'Vợt bị nứt khung sau một tháng sử dụng.','NEW',NULL,'2026-08-15 01:20:15',NULL,19,NULL,78),(19,2,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-07-15 15:20:15','2026-07-17 15:20:15',20,1,79),(20,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','NEW',NULL,'2026-07-21 23:20:15',NULL,21,NULL,80),(21,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-07-03 20:20:15','2026-07-05 20:20:15',22,1,81),(22,4,'Khung vợt chắc, đập cầu uy lực, rất hài lòng.','IN_PROGRESS',NULL,'2026-07-01 00:20:15',NULL,23,1,82),(23,5,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-07-23 13:20:15','2026-07-25 13:20:15',24,1,86),(24,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','NEW',NULL,'2026-08-30 02:20:15',NULL,25,NULL,87),(25,2,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-08-10 17:20:15','2026-08-12 17:20:15',26,1,88),(26,1,'Vợt bị nứt khung sau một tháng sử dụng.','NEW',NULL,'2026-06-30 23:20:15',NULL,27,NULL,78),(27,2,'Vợt bị nứt khung sau một tháng sử dụng.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-08-19 10:20:15','2026-08-22 10:20:15',28,1,79),(28,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','IN_PROGRESS',NULL,'2026-08-19 03:20:15',NULL,29,1,80),(29,2,'Vợt bị nứt khung sau một tháng sử dụng.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-07-24 00:20:15','2026-07-26 00:20:15',30,1,81),(30,3,'Vợt ổn nhưng cước căng hơi chùng sau 2 tuần.','NEW',NULL,'2026-09-20 09:20:15',NULL,31,NULL,82),(31,4,'Khung vợt chắc, đập cầu uy lực, rất hài lòng.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-06-20 08:20:15','2026-06-21 08:20:15',32,1,86),(32,5,'Khung vợt chắc, đập cầu uy lực, rất hài lòng.','NEW',NULL,'2026-08-01 15:20:15',NULL,33,NULL,87),(33,4,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-09-29 13:20:15','2026-09-30 13:20:15',34,1,88),(34,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','IN_PROGRESS',NULL,'2026-07-21 12:20:15',NULL,35,1,78),(35,4,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-09-04 11:20:15','2026-09-07 11:20:15',36,1,79),(36,2,'Vợt bị nứt khung sau một tháng sử dụng.','NEW',NULL,'2026-08-07 01:20:15',NULL,37,NULL,80),(37,4,'Vợt nhẹ đầu, phòng thủ phản tạt nhanh, đáng tiền.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-06-24 10:20:15','2026-06-27 10:20:15',38,1,81);
/*!40000 ALTER TABLE `feedbacks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `product_id` int NOT NULL AUTO_INCREMENT,
  `product_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `price` decimal(12,2) NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `brand_id` int NOT NULL,
  `category_id` int NOT NULL,
  `image_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`product_id`),
  KEY `idx_products_category` (`category_id`),
  KEY `idx_products_brand` (`brand_id`),
  KEY `idx_products_name` (`product_name`),
  KEY `idx_products_status` (`status`),
  KEY `idx_products_price` (`price`),
  CONSTRAINT `fk_products_brand` FOREIGN KEY (`brand_id`) REFERENCES `brands` (`brand_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_products_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_products_price` CHECK ((`price` >= 0)),
  CONSTRAINT `chk_products_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'INACTIVE')))
) ENGINE=InnoDB AUTO_INCREMENT=118 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (78,'Yonex Astrox 88D Pro','Vợt thiên công, đầu nặng, hợp đánh đôi nam cuối sân',4200000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:03:34',3,1,'https://i.imgur.com/Xs2XCJ6.jpeg'),(79,'Yonex Astrox 99 Pro','Vợt thiên công, đầu nặng, lực đập mạnh',4300000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:10:38',3,1,'https://i.imgur.com/XFEFPT0.jpeg'),(80,'Yonex Arcsaber 11 Pro','Vợt cân bằng, kiểm soát cầu tốt',3800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:12:16',3,1,'https://i.imgur.com/9msX3aJ.jpeg'),(81,'Yonex Nanoflare 800 Pro','Vợt thiên tốc độ, đầu nhẹ, phản hồi nhanh',4000000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:13:50',3,1,'https://i.imgur.com/8mCquG1.jpeg'),(82,'Yonex Duora 10','Vợt hai đầu, linh hoạt công thủ',3500000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:13:40',3,1,'https://i.imgur.com/juLsHih.jpeg'),(83,'Yonex Power Cushion 65 Z3','Giày đệm êm, bám sân tốt',3200000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:15:11',3,6,'https://i.imgur.com/GFxsPzr.jpeg'),(84,'Yonex Aerosensa 50','Cầu lông vũ thi đấu, hộp 12 quả',950000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:15:49',3,5,'https://i.imgur.com/6KdFcrG.jpeg'),(85,'Yonex Áo thi đấu nam','Áo thun thoáng khí cho thi đấu',650000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:16:26',3,9,'https://i.imgur.com/d2wCZYO.jpeg'),(86,'Lining Axforce 80','Vợt thiên công, khung cứng',3300000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:17:23',4,1,'https://i.imgur.com/e0z4dBv.jpeg'),(87,'Lining Windstorm 72','Vợt nhẹ, linh hoạt, phù hợp người mới chơi',1900000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:18:07',4,1,'https://i.imgur.com/NjODJwE.jpeg'),(88,'Lining Aeronaut 9000','Vợt thiên công, đầu nặng',4000000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 16:17:31',4,1,'https://i.imgur.com/93F6k1G.jpeg'),(89,'Lining Turbocharging 75','Vợt thiên tốc độ, nhẹ',2400000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:20:18',4,1,'https://i.imgur.com/NqFuEKf.jpeg'),(90,'Lining Bladex 900','Vợt cân bằng, bền',2800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:20:47',4,1,'https://i.imgur.com/CPs0pT4.jpeg'),(91,'Lining Saga II','Giày nhẹ, hỗ trợ di chuyển nhanh',1800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:21:23',4,6,'https://i.imgur.com/d5oihyp.jpeg'),(92,'Lining A+60','Cầu lông vũ tập luyện, hộp 12 quả',700000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:22:28',4,5,'https://i.imgur.com/Wu1mNuH.jpeg'),(93,'Lining Áo thi đấu nam','Áo thun thoáng khí, co giãn',450000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:22:38',4,9,'https://i.imgur.com/NFacQwV.jpeg'),(94,'Victor Auraspeed 90S','Vợt tốc độ, đầu nhẹ',3300000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:23:33',5,1,'https://i.imgur.com/cjyx7bK.jpeg'),(95,'Victor Thruster Ryuga II','Vợt thiên công, đầu nặng',3600000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:24:16',5,1,'https://i.imgur.com/uFe7miv.jpeg'),(96,'Victor Jetspeed S 12','Vợt tốc độ, đầu nhẹ',3200000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:24:52',5,1,'https://i.imgur.com/LxQnsJ4.jpeg'),(97,'Victor Drive X 9X','Vợt cân bằng, đa dụng',3100000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:25:45',5,1,'https://i.imgur.com/AY9sy0U.jpeg'),(98,'Victor Brave Sword 12','Vợt thiên công, dễ kiểm soát',2800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 16:17:13',5,1,'https://i.imgur.com/wjB6oWu.jpeg'),(99,'Victor P9200','Giày ổn định, hỗ trợ cổ chân',2500000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:27:55',5,6,'https://i.imgur.com/hl6DGNB.jpeg'),(100,'Victor Gold No.1','Cầu lông vũ, hộp 12 quả',800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:27:43',5,5,'https://i.imgur.com/WUR6gNc.jpeg'),(101,'Victor Áo thi đấu nam','Áo thun thoáng khí cho thi đấu',500000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:27:31',5,9,'https://i.imgur.com/WrFioUJ.jpeg'),(102,'Mizuno Fortius 10 Quick','Vợt thiên tốc độ, đầu nhẹ',2800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:28:57',6,1,'https://i.imgur.com/HXpI9bt.jpeg'),(103,'Mizuno Fortius 30 Power','Vợt thiên công, đầu nặng',3000000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:30:04',6,1,'https://i.imgur.com/xu5HUQn.jpeg'),(104,'Mizuno Altius 01 Speed','Vợt nhẹ, linh hoạt',2500000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:30:35',6,1,'https://i.imgur.com/GsttcMO.jpeg'),(105,'Mizuno Altius 03 Feel','Vợt cân bằng, cảm giác cầu tốt',2600000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:31:53',6,1,'https://i.imgur.com/vaAtEUX.jpeg'),(106,'Mizuno Acrospeed 5.0','Vợt tầm trung cho người mới',1800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:32:22',6,1,'https://i.imgur.com/4c4orId.jpeg'),(107,'Mizuno Wave Claw 2','Giày nhẹ, linh hoạt',3200000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 16:17:49',6,6,'https://i.imgur.com/WSROf0I.jpeg'),(108,'Mizuno Cầu tập luyện','Cầu tập luyện, hộp 12 quả',600000.00,'INACTIVE','2026-10-14 10:04:21','2026-10-14 15:33:37',6,5,''),(109,'Mizuno Áo thi đấu nam','Áo thun thoáng khí, thấm hút tốt',450000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:59:09',6,9,'https://i.imgur.com/aOJdEMv.jpeg'),(110,'Apacs Nano Fusion Speed 722','Vợt tầm trung, thiên tốc độ',2200000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:35:59',7,1,'https://i.imgur.com/DtsE3lD.jpeg'),(111,'Apacs Feather Weight 55','Vợt siêu nhẹ cho người mới',1600000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:36:38',7,1,'https://i.imgur.com/t9Ovk0U.jpeg'),(112,'Apacs Z-Ziggler','Vợt thiên công, cứng',2400000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:37:15',7,1,'https://i.imgur.com/6yXd346.jpeg'),(113,'Apacs Edgesaber 10','Vợt cân bằng, đa dụng',2000000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:37:59',7,1,'https://i.imgur.com/jv3ufh2.jpeg'),(114,'Apacs Virtuoso Pro','Vợt thiên tốc độ, nhẹ',2300000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:38:36',7,1,'https://i.imgur.com/02l3P1e.jpeg'),(115,'Apacs Cushion Pro','Giày đệm êm cho tập luyện',1500000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:39:23',7,6,'https://i.imgur.com/eCAtV3F.jpeg'),(116,'Apacs Cầu lông vũ','Cầu lông vũ, hộp 12 quả',650000.00,'INACTIVE','2026-10-14 10:04:21','2026-10-14 15:40:09',7,5,''),(117,'Apacs Áo thi đấu nam','Áo thun thoáng khí cho tập luyện',350000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:41:18',7,9,'https://i.imgur.com/uES1S6c.jpeg');
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `role_id` int NOT NULL AUTO_INCREMENT,
  `role_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `role_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`role_id`),
  UNIQUE KEY `uq_roles_code` (`role_code`),
  CONSTRAINT `chk_roles_code` CHECK ((`role_code` in (_utf8mb4'ADMIN',_utf8mb4'MANAGER',_utf8mb4'CUSTOMER')))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'ADMIN','Quản trị viên','Quản trị hệ thống, tài khoản và cơ sở dữ liệu','2026-10-16 08:20:14','2026-10-16 08:20:14'),(2,'MANAGER','Nhân sự quản lý','Quản lý danh mục sản phẩm và vận hành CRM','2026-10-16 08:20:14','2026-10-16 08:20:14'),(3,'CUSTOMER','Khách hàng','Khách hàng mua sắm và tương tác CRM','2026-10-16 08:20:14','2026-10-16 08:20:14');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `survey_answers`
--

DROP TABLE IF EXISTS `survey_answers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `survey_answers` (
  `answer_id` int NOT NULL AUTO_INCREMENT,
  `answer_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `rating_value` tinyint DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `option_id` int DEFAULT NULL,
  `question_id` int NOT NULL,
  `response_id` int NOT NULL,
  PRIMARY KEY (`answer_id`),
  KEY `idx_survey_answers_response` (`response_id`),
  KEY `idx_survey_answers_question` (`question_id`),
  KEY `idx_survey_answers_option` (`option_id`),
  CONSTRAINT `fk_survey_answers_option` FOREIGN KEY (`option_id`) REFERENCES `survey_options` (`option_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_survey_answers_question` FOREIGN KEY (`question_id`) REFERENCES `survey_questions` (`question_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_survey_answers_response` FOREIGN KEY (`response_id`) REFERENCES `survey_responses` (`response_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_survey_answers_rating` CHECK (((`rating_value` is null) or (`rating_value` between 1 and 5)))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `survey_answers`
--

LOCK TABLES `survey_answers` WRITE;
/*!40000 ALTER TABLE `survey_answers` DISABLE KEYS */;
INSERT INTO `survey_answers` VALUES (1,NULL,NULL,'2026-10-16 08:20:14',1,1,1);
/*!40000 ALTER TABLE `survey_answers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `survey_options`
--

DROP TABLE IF EXISTS `survey_options`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `survey_options` (
  `option_id` int NOT NULL AUTO_INCREMENT,
  `option_text` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `sort_order` int NOT NULL,
  `question_id` int NOT NULL,
  PRIMARY KEY (`option_id`),
  KEY `idx_survey_options_question` (`question_id`),
  KEY `idx_survey_options_sort` (`question_id`,`sort_order`),
  CONSTRAINT `fk_survey_options_question` FOREIGN KEY (`question_id`) REFERENCES `survey_questions` (`question_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_survey_options_sort_order` CHECK ((`sort_order` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `survey_options`
--

LOCK TABLES `survey_options` WRITE;
/*!40000 ALTER TABLE `survey_options` DISABLE KEYS */;
INSERT INTO `survey_options` VALUES (1,'Good',0,1);
/*!40000 ALTER TABLE `survey_options` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `survey_questions`
--

DROP TABLE IF EXISTS `survey_questions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `survey_questions` (
  `question_id` int NOT NULL AUTO_INCREMENT,
  `question_text` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `question_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_required` tinyint(1) NOT NULL,
  `sort_order` int NOT NULL,
  `survey_id` int NOT NULL,
  `config` json DEFAULT NULL,
  PRIMARY KEY (`question_id`),
  KEY `idx_survey_questions_survey` (`survey_id`),
  KEY `idx_survey_questions_type` (`question_type`),
  KEY `idx_survey_questions_sort` (`survey_id`,`sort_order`),
  CONSTRAINT `fk_survey_questions_survey` FOREIGN KEY (`survey_id`) REFERENCES `surveys` (`survey_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_survey_questions_sort_order` CHECK ((`sort_order` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `survey_questions`
--

LOCK TABLES `survey_questions` WRITE;
/*!40000 ALTER TABLE `survey_questions` DISABLE KEYS */;
INSERT INTO `survey_questions` VALUES (1,'How was your shopping experience?','SINGLE_CHOICE',1,0,1,NULL);
/*!40000 ALTER TABLE `survey_questions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `survey_recipients`
--

DROP TABLE IF EXISTS `survey_recipients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `survey_recipients` (
  `recipient_id` int NOT NULL AUTO_INCREMENT,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `sent_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `opened_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `customer_id` int NOT NULL,
  `survey_id` int NOT NULL,
  PRIMARY KEY (`recipient_id`),
  UNIQUE KEY `uq_survey_recipients_survey_customer` (`survey_id`,`customer_id`),
  KEY `idx_survey_recipients_survey` (`survey_id`),
  KEY `idx_survey_recipients_customer` (`customer_id`),
  KEY `idx_survey_recipients_status` (`status`),
  CONSTRAINT `fk_survey_recipients_customer` FOREIGN KEY (`customer_id`) REFERENCES `accounts` (`account_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_survey_recipients_survey` FOREIGN KEY (`survey_id`) REFERENCES `surveys` (`survey_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `survey_recipients`
--

LOCK TABLES `survey_recipients` WRITE;
/*!40000 ALTER TABLE `survey_recipients` DISABLE KEYS */;
INSERT INTO `survey_recipients` VALUES (1,'COMPLETED','2026-10-16 08:20:14',NULL,'2026-10-16 08:20:14',2,1);
/*!40000 ALTER TABLE `survey_recipients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `survey_responses`
--

DROP TABLE IF EXISTS `survey_responses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `survey_responses` (
  `response_id` int NOT NULL AUTO_INCREMENT,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `started_at` datetime DEFAULT NULL,
  `submitted_at` datetime DEFAULT NULL,
  `recipient_id` int NOT NULL,
  PRIMARY KEY (`response_id`),
  UNIQUE KEY `uq_survey_responses_recipient` (`recipient_id`),
  KEY `idx_survey_responses_status` (`status`),
  CONSTRAINT `fk_survey_responses_recipient` FOREIGN KEY (`recipient_id`) REFERENCES `survey_recipients` (`recipient_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `survey_responses`
--

LOCK TABLES `survey_responses` WRITE;
/*!40000 ALTER TABLE `survey_responses` DISABLE KEYS */;
INSERT INTO `survey_responses` VALUES (1,'SUBMITTED','2026-10-16 08:20:14','2026-10-16 08:20:14',1);
/*!40000 ALTER TABLE `survey_responses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `surveys`
--

DROP TABLE IF EXISTS `surveys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `surveys` (
  `survey_id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `start_at` datetime DEFAULT NULL,
  `end_at` datetime DEFAULT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_by` int NOT NULL,
  `template_key` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `objective` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `audience` json DEFAULT NULL,
  PRIMARY KEY (`survey_id`),
  KEY `idx_surveys_status` (`status`),
  KEY `idx_surveys_created_by` (`created_by`),
  KEY `idx_surveys_start_at` (`start_at`),
  KEY `idx_surveys_end_at` (`end_at`),
  CONSTRAINT `fk_surveys_created_by` FOREIGN KEY (`created_by`) REFERENCES `accounts` (`account_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `surveys`
--

LOCK TABLES `surveys` WRITE;
/*!40000 ALTER TABLE `surveys` DISABLE KEYS */;
INSERT INTO `surveys` VALUES (1,'Demo badminton survey',NULL,NULL,NULL,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14',1,NULL,NULL,NULL);
/*!40000 ALTER TABLE `surveys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'crm_db'
--

--
-- Dumping routines for database 'crm_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-20 21:57:19

-- MySQL dump 10.13  Distrib 8.4.11, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: crm_db_review_export_20261016_8b99
-- ------------------------------------------------------
-- Server version	8.4.11

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
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `role_id` int NOT NULL AUTO_INCREMENT,
  `role_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
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
-- Table structure for table `accounts`
--

DROP TABLE IF EXISTS `accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `accounts` (
  `account_id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `last_login_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`account_id`),
  UNIQUE KEY `uq_accounts_email` (`email`),
  KEY `idx_accounts_role` (`role`),
  CONSTRAINT `fk_accounts_role` FOREIGN KEY (`role`) REFERENCES `roles` (`role_code`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_accounts_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'LOCKED')))
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts`
--

LOCK TABLES `accounts` WRITE;
/*!40000 ALTER TABLE `accounts` DISABLE KEYS */;
INSERT INTO `accounts` VALUES (1,'demo-admin@example.test','pbkdf2_sha256$1000000$erQI2JiefbNHET6B9B2y6u$Sm8aQVT+AlNktOqm1NLKScZpiufFa8xKB9GbLWNidnw=','ADMIN','ACTIVE',NULL,'2026-10-16 08:20:14','2026-10-16 08:20:14'),(2,'demo-customer@example.test','pbkdf2_sha256$1000000$RvXw0YBqj3Htzg8CMmIAdi$sN9oQIfreUpZ0qM9FBjbzz3/JI8ielnjoL9JRNz1WUc=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:14','2026-10-16 08:20:14'),(3,'kh01@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:14','2026-10-16 08:20:15'),(4,'kh02@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(5,'kh03@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(6,'kh04@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(7,'kh05@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(8,'kh06@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(9,'kh07@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(10,'kh08@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(11,'kh09@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(12,'kh10@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(13,'kh11@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(14,'kh12@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(15,'kh13@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(16,'kh14@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(17,'kh15@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(18,'kh16@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(19,'kh17@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(20,'kh18@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(21,'kh19@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(22,'kh20@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(23,'kh21@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(24,'kh22@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(25,'kh23@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(26,'kh24@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(27,'kh25@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(28,'kh26@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(29,'kh27@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(30,'kh28@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(31,'kh29@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(32,'kh30@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(33,'kh31@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(34,'kh32@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(35,'kh33@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(36,'kh34@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(37,'kh35@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(38,'kh36@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(39,'kh37@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(40,'kh38@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(41,'kh39@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','ACTIVE',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(42,'kh40@example.test','pbkdf2_sha256$1000000$qiw9ktMYZftQVqMvyhjwsP$4C6mdFe5zqAube060kvgYTj5LlnkFeiPKJnFaMRK8xU=','CUSTOMER','LOCKED',NULL,'2026-10-16 08:20:15','2026-10-16 08:20:15'),(43,'demo-admin2@example.test','pbkdf2_sha256$1000000$erQI2JiefbNHET6B9B2y6u$Sm8aQVT+AlNktOqm1NLKScZpiufFa8xKB9GbLWNidnw=','ADMIN','ACTIVE',NULL,'2026-10-19 08:00:00','2026-10-19 08:00:00'),(44,'demo-manager1@example.test','pbkdf2_sha256$1000000$erQI2JiefbNHET6B9B2y6u$Sm8aQVT+AlNktOqm1NLKScZpiufFa8xKB9GbLWNidnw=','MANAGER','ACTIVE',NULL,'2026-10-19 08:00:00','2026-10-19 08:00:00'),(45,'demo-manager2@example.test','pbkdf2_sha256$1000000$erQI2JiefbNHET6B9B2y6u$Sm8aQVT+AlNktOqm1NLKScZpiufFa8xKB9GbLWNidnw=','MANAGER','ACTIVE',NULL,'2026-10-19 08:00:00','2026-10-19 08:00:00'),(46,'demo-manager3@example.test','pbkdf2_sha256$1000000$erQI2JiefbNHET6B9B2y6u$Sm8aQVT+AlNktOqm1NLKScZpiufFa8xKB9GbLWNidnw=','MANAGER','ACTIVE',NULL,'2026-10-19 08:00:00','2026-10-19 08:00:00');
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
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
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
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
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
  `brand_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`brand_id`),
  KEY `idx_brands_name` (`brand_name`),
  KEY `idx_brands_status` (`status`),
  CONSTRAINT `chk_brands_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'INACTIVE')))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `brands`
--

LOCK TABLES `brands` WRITE;
/*!40000 ALTER TABLE `brands` DISABLE KEYS */;
INSERT INTO `brands` VALUES (1,'Demo brand',NULL,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14');
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
  `category_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`category_id`),
  KEY `idx_categories_name` (`category_name`),
  KEY `idx_categories_status` (`status`),
  CONSTRAINT `chk_categories_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'INACTIVE')))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,'Badminton rackets',NULL,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14');
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
  `preference_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `preference_value` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `customer_id` int NOT NULL,
  PRIMARY KEY (`preference_id`),
  KEY `idx_customer_preferences_customer` (`customer_id`),
  KEY `idx_customer_preferences_type` (`preference_type`),
  CONSTRAINT `fk_customer_preferences_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=152 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer_preferences`
--

LOCK TABLES `customer_preferences` WRITE;
/*!40000 ALTER TABLE `customer_preferences` DISABLE KEYS */;
INSERT INTO `customer_preferences` VALUES (1,'CATEGORY','Badminton rackets','2026-10-16 08:20:14',1),(2,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',2),(3,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',2),(4,'BRAND','Kumpoo','2026-10-16 08:20:15',2),(5,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',3),(6,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',3),(7,'BRAND','Mizuno','2026-10-16 08:20:15',3),(8,'BRAND','Victor','2026-10-16 08:20:15',3),(9,'BRAND','Yonex','2026-10-16 08:20:15',3),(10,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',4),(11,'BRAND','Mizuno','2026-10-16 08:20:15',4),(12,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',5),(13,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',5),(14,'BRAND','Li-Ning','2026-10-16 08:20:15',5),(15,'BRAND','VNB','2026-10-16 08:20:15',5),(16,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',6),(17,'BRAND','Kumpoo','2026-10-16 08:20:15',6),(18,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',7),(19,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',7),(20,'BRAND','Apacs','2026-10-16 08:20:15',7),(21,'BRAND','VNB','2026-10-16 08:20:15',7),(22,'BRAND','Kumpoo','2026-10-16 08:20:15',7),(23,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',8),(24,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',8),(25,'BRAND','Yonex','2026-10-16 08:20:15',8),(26,'BRAND','Mizuno','2026-10-16 08:20:15',8),(27,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',9),(28,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',9),(29,'BRAND','VNB','2026-10-16 08:20:15',9),(30,'BRAND','Kumpoo','2026-10-16 08:20:15',9),(31,'BRAND','Mizuno','2026-10-16 08:20:15',9),(32,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',10),(33,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',10),(34,'BRAND','Kumpoo','2026-10-16 08:20:15',10),(35,'BRAND','Yonex','2026-10-16 08:20:15',10),(36,'BRAND','VNB','2026-10-16 08:20:15',10),(37,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',11),(38,'BRAND','Yonex','2026-10-16 08:20:15',11),(39,'BRAND','Apacs','2026-10-16 08:20:15',11),(40,'BRAND','Kumpoo','2026-10-16 08:20:15',11),(41,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',12),(42,'BRAND','VNB','2026-10-16 08:20:15',12),(43,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',13),(44,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',13),(45,'BRAND','Mizuno','2026-10-16 08:20:15',13),(46,'BRAND','Apacs','2026-10-16 08:20:15',13),(47,'BRAND','Li-Ning','2026-10-16 08:20:15',13),(48,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',14),(49,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',14),(50,'BRAND','Li-Ning','2026-10-16 08:20:15',14),(51,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',15),(52,'BRAND','Kumpoo','2026-10-16 08:20:15',15),(53,'BRAND','Mizuno','2026-10-16 08:20:15',15),(54,'BRAND','VNB','2026-10-16 08:20:15',15),(55,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',16),(56,'BRAND','Mizuno','2026-10-16 08:20:15',16),(57,'BRAND','VNB','2026-10-16 08:20:15',16),(58,'BRAND','Kumpoo','2026-10-16 08:20:15',16),(59,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',17),(60,'BRAND','Mizuno','2026-10-16 08:20:15',17),(61,'BRAND','Yonex','2026-10-16 08:20:15',17),(62,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',18),(63,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',18),(64,'BRAND','VNB','2026-10-16 08:20:15',18),(65,'BRAND','Apacs','2026-10-16 08:20:15',18),(66,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',19),(67,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',19),(68,'BRAND','Victor','2026-10-16 08:20:15',19),(69,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',20),(70,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',20),(71,'BRAND','Mizuno','2026-10-16 08:20:15',20),(72,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',21),(73,'BRAND','Victor','2026-10-16 08:20:15',21),(74,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',22),(75,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',22),(76,'BRAND','Li-Ning','2026-10-16 08:20:15',22),(77,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',23),(78,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',23),(79,'BRAND','Kumpoo','2026-10-16 08:20:15',23),(80,'BRAND','Victor','2026-10-16 08:20:15',23),(81,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',24),(82,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',24),(83,'BRAND','Victor','2026-10-16 08:20:15',24),(84,'BRAND','VNB','2026-10-16 08:20:15',24),(85,'BRAND','Kumpoo','2026-10-16 08:20:15',24),(86,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',25),(87,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',25),(88,'BRAND','VNB','2026-10-16 08:20:15',25),(89,'BRAND','Victor','2026-10-16 08:20:15',25),(90,'BRAND','Mizuno','2026-10-16 08:20:15',25),(91,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',26),(92,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',26),(93,'BRAND','Apacs','2026-10-16 08:20:15',26),(94,'BRAND','Li-Ning','2026-10-16 08:20:15',26),(95,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',27),(96,'BRAND','Li-Ning','2026-10-16 08:20:15',27),(97,'BRAND','Apacs','2026-10-16 08:20:15',27),(98,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',28),(99,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',28),(100,'BRAND','Kumpoo','2026-10-16 08:20:15',28),(101,'BRAND','VNB','2026-10-16 08:20:15',28),(102,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',29),(103,'BRAND','Li-Ning','2026-10-16 08:20:15',29),(104,'BRAND','Mizuno','2026-10-16 08:20:15',29),(105,'BRAND','Kumpoo','2026-10-16 08:20:15',29),(106,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',30),(107,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',30),(108,'BRAND','Victor','2026-10-16 08:20:15',30),(109,'BRAND','Yonex','2026-10-16 08:20:15',30),(110,'BRAND','Kumpoo','2026-10-16 08:20:15',30),(111,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',31),(112,'BRAND','Apacs','2026-10-16 08:20:15',31),(113,'BRAND','Yonex','2026-10-16 08:20:15',31),(114,'BRAND','Victor','2026-10-16 08:20:15',31),(115,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',32),(116,'BRAND','Victor','2026-10-16 08:20:15',32),(117,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',33),(118,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',33),(119,'BRAND','Mizuno','2026-10-16 08:20:15',33),(120,'BRAND','Yonex','2026-10-16 08:20:15',33),(121,'BRAND','VNB','2026-10-16 08:20:15',33),(122,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',34),(123,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',34),(124,'BRAND','Mizuno','2026-10-16 08:20:15',34),(125,'BRAND','VNB','2026-10-16 08:20:15',34),(126,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',35),(127,'BRAND','Mizuno','2026-10-16 08:20:15',35),(128,'BRAND','VNB','2026-10-16 08:20:15',35),(129,'BRAND','Yonex','2026-10-16 08:20:15',35),(130,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',36),(131,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',36),(132,'BRAND','Yonex','2026-10-16 08:20:15',36),(133,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',37),(134,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',37),(135,'BRAND','Li-Ning','2026-10-16 08:20:15',37),(136,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',38),(137,'BRAND','Apacs','2026-10-16 08:20:15',38),(138,'BRAND','Li-Ning','2026-10-16 08:20:15',38),(139,'BRAND','Kumpoo','2026-10-16 08:20:15',38),(140,'PLAY_STYLE','Đánh đôi','2026-10-16 08:20:15',39),(141,'PLAY_STYLE','Toàn diện','2026-10-16 08:20:15',39),(142,'BRAND','Kumpoo','2026-10-16 08:20:15',39),(143,'BRAND','Victor','2026-10-16 08:20:15',39),(144,'BRAND','Yonex','2026-10-16 08:20:15',39),(145,'PLAY_STYLE','Đánh đơn','2026-10-16 08:20:15',40),(146,'BRAND','Yonex','2026-10-16 08:20:15',40),(147,'PLAY_STYLE','Phòng thủ','2026-10-16 08:20:15',41),(148,'PLAY_STYLE','Tấn công','2026-10-16 08:20:15',41),(149,'BRAND','Li-Ning','2026-10-16 08:20:15',41),(150,'BRAND','VNB','2026-10-16 08:20:15',41),(151,'BRAND','Kumpoo','2026-10-16 08:20:15',41);
/*!40000 ALTER TABLE `customer_preferences` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `customers`
--

DROP TABLE IF EXISTS `customers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `customers` (
  `customer_id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `playing_level` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted_at` datetime DEFAULT NULL,
  `account_id` int NOT NULL,
  PRIMARY KEY (`customer_id`),
  UNIQUE KEY `uq_customers_account_id` (`account_id`),
  KEY `idx_customers_full_name` (`full_name`),
  KEY `idx_customers_phone` (`phone`),
  KEY `idx_customers_status` (`status`),
  CONSTRAINT `fk_customers_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_customers_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'DELETED')))
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customers`
--

LOCK TABLES `customers` WRITE;
/*!40000 ALTER TABLE `customers` DISABLE KEYS */;
INSERT INTO `customers` VALUES (1,'Demo customer',NULL,NULL,NULL,NULL,NULL,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14',NULL,2),(2,'Trần Minh Khoa','0912000001','2007-08-16','MALE','Quận Bình Thạnh, TP. Hồ Chí Minh','RECREATIONAL','ACTIVE','2025-12-02 08:20:14','2026-10-16 15:20:14',NULL,3),(3,'Lê Thu Trang','0912000002','2005-01-04','FEMALE','Thủ Đức, TP. Hồ Chí Minh','RECREATIONAL','ACTIVE','2025-12-06 08:20:14','2026-10-16 15:20:14',NULL,4),(4,'Phạm Quang Hải','0912000003','2003-09-04','MALE','Cầu Giấy, Hà Nội','COMPETITIVE','ACTIVE','2026-10-11 08:20:14','2026-10-16 15:20:14',NULL,5),(5,'Hoàng Bảo Ngọc','0912000004','2000-02-07','FEMALE','Đống Đa, Hà Nội','BEGINNER','ACTIVE','2026-04-07 08:20:14','2026-10-16 15:20:14',NULL,6),(6,'Huỳnh Tuấn Kiệt','0912000005','1998-01-26','MALE','Hải Châu, Đà Nẵng','RECREATIONAL','ACTIVE','2026-01-14 08:20:14','2026-10-16 15:20:14',NULL,7),(7,'Phan Mỹ Linh','0912000006','1995-05-19','FEMALE','Ninh Kiều, Cần Thơ','RECREATIONAL','ACTIVE','2026-05-11 08:20:14','2026-10-16 15:20:14',NULL,8),(8,'Vũ Thành Đạt','0912000007','1993-10-03','MALE','Biên Hòa, Đồng Nai','COMPETITIVE','ACTIVE','2025-12-21 08:20:14','2026-10-16 15:20:14',NULL,9),(9,'Võ Hồng Nhung','0912000008','1990-01-05','FEMALE','Quận 1, TP. Hồ Chí Minh','BEGINNER','ACTIVE','2026-03-27 08:20:14','2026-10-16 15:20:14',NULL,10),(10,'Đặng Công Danh','0912000009','1987-01-20','MALE','Quận Bình Thạnh, TP. Hồ Chí Minh','RECREATIONAL','ACTIVE','2026-06-24 08:20:14','2026-10-16 15:20:14',NULL,11),(11,'Bùi Thị Bình','0912000010','1984-08-10','FEMALE','Thủ Đức, TP. Hồ Chí Minh','RECREATIONAL','ACTIVE','2026-03-11 08:20:14','2026-10-16 15:20:14',NULL,12),(12,'Đỗ Minh Khoa','0912000011','1980-02-18','OTHER','Cầu Giấy, Hà Nội','COMPETITIVE','ACTIVE','2026-08-15 08:20:14','2026-10-16 15:20:14',NULL,13),(13,'Hồ Thu Trang','0912000012','1977-02-24','FEMALE','Đống Đa, Hà Nội','BEGINNER','ACTIVE','2026-01-09 08:20:14','2026-10-16 15:20:14',NULL,14),(14,'Ngô Quang Hải','0912000013',NULL,'MALE','Hải Châu, Đà Nẵng','RECREATIONAL','ACTIVE','2026-06-01 08:20:14','2026-10-16 15:20:14',NULL,15),(15,'Nguyễn Bảo Ngọc','0912000014','1969-10-11','FEMALE','Ninh Kiều, Cần Thơ','RECREATIONAL','ACTIVE','2026-02-08 08:20:14','2026-10-16 15:20:14',NULL,16),(16,'Trần Tuấn Kiệt','0912000015','1964-04-14','MALE','Biên Hòa, Đồng Nai','COMPETITIVE','ACTIVE','2026-02-04 08:20:14','2026-10-16 15:20:14',NULL,17),(17,'Lê Mỹ Linh','0912000016','2010-03-07','FEMALE','Quận 1, TP. Hồ Chí Minh','BEGINNER','ACTIVE','2026-03-06 08:20:14','2026-10-16 15:20:14',NULL,18),(18,'Phạm Thành Đạt','0912000017','2007-01-25','MALE','Quận Bình Thạnh, TP. Hồ Chí Minh',NULL,'ACTIVE','2026-02-13 08:20:14','2026-10-16 15:20:14',NULL,19),(19,'Hoàng Hồng Nhung','0912000018','2005-09-13','FEMALE','Thủ Đức, TP. Hồ Chí Minh','RECREATIONAL','ACTIVE','2026-03-20 08:20:14','2026-10-16 15:20:14',NULL,20),(20,'Huỳnh Công Danh','0912000019','2003-08-02','MALE','Cầu Giấy, Hà Nội','COMPETITIVE','ACTIVE','2025-12-23 08:20:14','2026-10-16 15:20:14',NULL,21),(21,'Phan Thị Bình','0912000020','2000-01-10','FEMALE','Đống Đa, Hà Nội','BEGINNER','ACTIVE','2026-08-16 08:20:14','2026-10-16 15:20:14',NULL,22),(22,'Vũ Minh Khoa','0912000021','1998-09-23','MALE','Hải Châu, Đà Nẵng','RECREATIONAL','ACTIVE','2025-11-10 08:20:14','2026-10-16 15:20:14',NULL,23),(23,'Võ Đức Huy','0912000022','1994-12-21','OTHER','Ninh Kiều, Cần Thơ','RECREATIONAL','ACTIVE','2025-12-14 08:20:14','2026-10-16 15:20:14',NULL,24),(24,'Đặng Quang Hải','0912000023','1993-01-30','MALE','Biên Hòa, Đồng Nai','COMPETITIVE','ACTIVE','2026-05-13 08:20:14','2026-10-16 15:20:14',NULL,25),(25,'Bùi Bảo Ngọc','0912000024','1990-01-29','FEMALE','Quận 1, TP. Hồ Chí Minh','BEGINNER','ACTIVE','2026-10-09 08:20:14','2026-10-16 15:20:14',NULL,26),(26,'Đỗ Tuấn Kiệt','0912000025','1987-08-22','MALE','Quận Bình Thạnh, TP. Hồ Chí Minh','RECREATIONAL','ACTIVE','2026-10-03 08:20:14','2026-10-16 15:20:14',NULL,27),(27,'Hồ Mỹ Linh','0912000026',NULL,'FEMALE','Thủ Đức, TP. Hồ Chí Minh','RECREATIONAL','ACTIVE','2026-05-14 08:20:14','2026-10-16 15:20:14',NULL,28),(28,'Ngô Thành Đạt','0912000027','1980-02-28','MALE','Cầu Giấy, Hà Nội','COMPETITIVE','ACTIVE','2026-07-21 08:20:14','2026-10-16 15:20:14',NULL,29),(29,'Nguyễn Hồng Nhung','0912000028','1977-07-29','FEMALE','Đống Đa, Hà Nội','BEGINNER','ACTIVE','2026-06-19 08:20:14','2026-10-16 15:20:14',NULL,30),(30,'Trần Công Danh','0912000029','1973-09-10','MALE','Hải Châu, Đà Nẵng','RECREATIONAL','ACTIVE','2026-09-22 08:20:14','2026-10-16 15:20:14',NULL,31),(31,'Lê Thị Bình','0912000030','1969-02-26','FEMALE','Ninh Kiều, Cần Thơ','RECREATIONAL','ACTIVE','2025-11-20 08:20:14','2026-10-16 15:20:14',NULL,32),(32,'Phạm Minh Khoa','0912000031','1964-01-18','MALE','Biên Hòa, Đồng Nai','COMPETITIVE','ACTIVE','2025-11-12 08:20:14','2026-10-16 15:20:14',NULL,33),(33,'Hoàng Thu Trang','0912000032','2010-07-12','FEMALE','Quận 1, TP. Hồ Chí Minh','BEGINNER','ACTIVE','2026-05-13 08:20:14','2026-10-16 15:20:14',NULL,34),(34,'Huỳnh Quang Hải','0912000033','2007-07-12','OTHER','Quận Bình Thạnh, TP. Hồ Chí Minh','RECREATIONAL','ACTIVE','2026-05-22 08:20:14','2026-10-16 15:20:14',NULL,35),(35,'Phan Bảo Ngọc','0912000034','2005-02-18','FEMALE','Thủ Đức, TP. Hồ Chí Minh',NULL,'ACTIVE','2026-01-20 08:20:14','2026-10-16 15:20:14',NULL,36),(36,'Vũ Tuấn Kiệt','0912000035','2003-01-20','MALE','Cầu Giấy, Hà Nội','COMPETITIVE','ACTIVE','2026-08-30 08:20:14','2026-10-16 15:20:14',NULL,37),(37,'Võ Mỹ Linh','0912000036','2000-02-26','FEMALE','Đống Đa, Hà Nội','BEGINNER','ACTIVE','2026-07-28 08:20:14','2026-10-16 15:20:14',NULL,38),(38,'Đặng Thành Đạt','0912000037','1998-04-18','MALE','Hải Châu, Đà Nẵng','RECREATIONAL','ACTIVE','2025-12-30 08:20:14','2026-10-16 15:20:14',NULL,39),(39,'Bùi Hồng Nhung','0912000038','1995-06-28','FEMALE','Ninh Kiều, Cần Thơ','RECREATIONAL','ACTIVE','2026-06-03 08:20:14','2026-10-16 15:20:14',NULL,40),(40,'Đỗ Công Danh','0912000039',NULL,'MALE','Biên Hòa, Đồng Nai','COMPETITIVE','ACTIVE','2025-10-31 08:20:14','2026-10-16 15:20:14',NULL,41),(41,'Hồ Thị Bình','0912000040','1990-09-15','FEMALE','Quận 1, TP. Hồ Chí Minh','BEGINNER','ACTIVE','2026-09-14 08:20:14','2026-10-16 15:20:14',NULL,42);
/*!40000 ALTER TABLE `customers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `admins`
--

DROP TABLE IF EXISTS `admins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admins` (
  `admin_id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `admin_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `full_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`admin_id`),
  UNIQUE KEY `uq_admins_account_id` (`account_id`),
  UNIQUE KEY `uq_admins_code` (`admin_code`),
  KEY `idx_admins_full_name` (`full_name`),
  KEY `idx_admins_phone` (`phone`),
  KEY `idx_admins_status` (`status`),
  CONSTRAINT `fk_admins_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_admins_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'INACTIVE')))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admins`
--

LOCK TABLES `admins` WRITE;
/*!40000 ALTER TABLE `admins` DISABLE KEYS */;
INSERT INTO `admins` VALUES (1,1,'AD0001','Nguyễn Văn Quản Trị','0901000001','1985-05-15','MALE','123 Lê Lợi, Quận 1, TP. Hồ Chí Minh','ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14'),(2,43,'AD0002','Trần Thị Hồng Phúc','0901000002','1988-10-20','FEMALE','456 Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh','ACTIVE','2026-10-19 08:00:00','2026-10-19 08:00:00');
/*!40000 ALTER TABLE `admins` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staffs`
--

DROP TABLE IF EXISTS `staffs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staffs` (
  `staff_id` int NOT NULL AUTO_INCREMENT,
  `account_id` int NOT NULL,
  `staff_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `full_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `position` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT 'MANAGER',
  `hire_date` date DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`staff_id`),
  UNIQUE KEY `uq_staffs_account_id` (`account_id`),
  UNIQUE KEY `uq_staffs_code` (`staff_code`),
  KEY `idx_staffs_full_name` (`full_name`),
  KEY `idx_staffs_phone` (`phone`),
  KEY `idx_staffs_status` (`status`),
  CONSTRAINT `fk_staffs_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`account_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_staffs_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'INACTIVE')))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staffs`
--

LOCK TABLES `staffs` WRITE;
/*!40000 ALTER TABLE `staffs` DISABLE KEYS */;
INSERT INTO `staffs` VALUES (1,44,'ST0001','Lê Hoàng Nam','0902000001','1992-03-12','MALE','789 Điện Biên Phủ, Bình Thạnh, TP. Hồ Chí Minh','MANAGER','2023-01-15','ACTIVE','2026-10-19 08:00:00','2026-10-19 08:00:00'),(2,45,'ST0002','Phạm Thu Hà','0902000002','1994-07-25','FEMALE','101 Võ Thị Sáu, Quận 3, TP. Hồ Chí Minh','MANAGER','2023-06-01','ACTIVE','2026-10-19 08:00:00','2026-10-19 08:00:00'),(3,46,'ST0003','Đặng Minh Tuấn','0902000003','1991-11-08','MALE','202 Cách Mạng Tháng 8, Quận 10, TP. Hồ Chí Minh','MANAGER','2024-02-10','ACTIVE','2026-10-19 08:00:00','2026-10-19 08:00:00');
/*!40000 ALTER TABLE `staffs` ENABLE KEYS */;
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
  `object_id` longtext COLLATE utf8mb4_unicode_ci,
  `object_repr` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
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
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
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
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-10-16 08:20:08.686117'),(2,'contenttypes','0002_remove_content_type_name','2026-10-16 08:20:08.749661'),(3,'auth','0001_initial','2026-10-16 08:20:08.967706'),(4,'auth','0002_alter_permission_name_max_length','2026-10-16 08:20:09.004704'),(5,'auth','0003_alter_user_email_max_length','2026-10-16 08:20:09.009707'),(6,'auth','0004_alter_user_username_opts','2026-10-16 08:20:09.012713'),(7,'auth','0005_alter_user_last_login_null','2026-10-16 08:20:09.015712'),(8,'auth','0006_require_contenttypes_0002','2026-10-16 08:20:09.016712'),(9,'auth','0007_alter_validators_add_error_messages','2026-10-16 08:20:09.020708'),(10,'auth','0008_alter_user_username_max_length','2026-10-16 08:20:09.024713'),(11,'auth','0009_alter_user_last_name_max_length','2026-10-16 08:20:09.027716'),(12,'auth','0010_alter_group_name_max_length','2026-10-16 08:20:09.033715'),(13,'auth','0011_update_proxy_permissions','2026-10-16 08:20:09.036708'),(14,'auth','0012_alter_user_first_name_max_length','2026-10-16 08:20:09.040708'),(15,'accounts','0001_initial','2026-10-16 08:20:09.220339'),(16,'accounts','0002_remove_account_chk_accounts_role_alter_account_role_and_more','2026-10-16 08:20:09.266874'),(17,'admin','0001_initial','2026-10-16 08:20:09.343261'),(18,'admin','0002_logentry_remove_auto_add','2026-10-16 08:20:09.347266'),(19,'admin','0003_logentry_add_action_flag_choices','2026-10-16 08:20:09.350265'),(20,'catalog','0001_initial','2026-10-16 08:20:09.511780'),(21,'catalog','0002_product_image_url','2026-10-16 08:20:09.543002'),(22,'customers','0001_initial','2026-10-16 08:20:09.636010'),(23,'feedback','0001_initial','2026-10-16 08:20:09.797085'),(24,'sessions','0001_initial','2026-10-16 08:20:09.817090'),(25,'surveys','0001_initial','2026-10-16 08:20:10.288699'),(26,'surveys','0002_schema_contract','2026-10-16 08:20:12.611366'),(27,'accounts','0003_role_admin_staff','2026-10-19 15:30:00.000000'),(28,'catalog','0003_remove_product_supplier_delete_supplier','2026-10-19 15:30:00.000000');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
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
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `manager_note` text COLLATE utf8mb4_unicode_ci,
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
  CONSTRAINT `fk_feedbacks_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_feedbacks_handled_by` FOREIGN KEY (`handled_by`) REFERENCES `accounts` (`account_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_feedbacks_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_feedbacks_rating` CHECK (((`rating` >= 1) and (`rating` <= 5))),
  CONSTRAINT `feedbacks_chk_1` CHECK ((`rating` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feedbacks`
--

LOCK TABLES `feedbacks` WRITE;
/*!40000 ALTER TABLE `feedbacks` DISABLE KEYS */;
INSERT INTO `feedbacks` VALUES (1,5,'Good racket','NEW',NULL,'2026-10-16 08:20:14',NULL,1,NULL,1),(2,5,'Khung vợt chắc, đập cầu uy lực, rất hài lòng.','NEW',NULL,'2026-08-11 16:20:15',NULL,2,NULL,1),(3,5,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-06-22 13:20:15','2026-06-25 13:20:15',3,1,2),(4,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','IN_PROGRESS',NULL,'2026-07-06 14:20:15',NULL,4,1,3),(5,2,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-09-15 08:20:15','2026-09-18 08:20:15',5,1,4),(6,5,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','NEW',NULL,'2026-09-09 05:20:15',NULL,6,NULL,5),(7,5,'Vợt nhẹ đầu, phòng thủ phản tạt nhanh, đáng tiền.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-08-13 11:20:15','2026-08-15 11:20:15',7,1,6),(8,4,'Khung vợt chắc, đập cầu uy lực, rất hài lòng.','NEW',NULL,'2026-09-12 21:20:15',NULL,8,NULL,7),(9,3,'Vợt ổn nhưng cước căng hơi chùng sau 2 tuần.','RESOLVED','Cảm ơn góp ý của bạn. Cửa hàng hỗ trợ căng lại cước/đổi size miễn phí, bạn mang sản phẩm qua shop nhé.','2026-07-14 22:20:15','2026-07-15 22:20:15',9,1,8),(10,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','IN_PROGRESS',NULL,'2026-09-08 18:20:15',NULL,10,1,1),(11,4,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-06-28 10:20:15','2026-06-30 10:20:15',11,1,2),(12,3,'Đánh được, tuy nhiên cán hơi to so với tay mình.','NEW',NULL,'2026-08-22 06:20:15',NULL,12,NULL,3),(13,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-06-26 05:20:15','2026-06-28 05:20:15',13,1,4),(14,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','NEW',NULL,'2026-08-25 16:20:15',NULL,14,NULL,5),(15,3,'Đánh được, tuy nhiên cán hơi to so với tay mình.','RESOLVED','Cảm ơn góp ý của bạn. Cửa hàng hỗ trợ căng lại cước/đổi size miễn phí, bạn mang sản phẩm qua shop nhé.','2026-08-10 16:20:15','2026-08-11 16:20:15',15,1,6),(16,4,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','IN_PROGRESS',NULL,'2026-07-03 07:20:15',NULL,16,1,7),(17,1,'Vợt bị nứt khung sau một tháng sử dụng.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-07-15 13:20:15','2026-07-17 13:20:15',17,1,8),(18,2,'Vợt bị nứt khung sau một tháng sử dụng.','NEW',NULL,'2026-08-15 01:20:15',NULL,18,NULL,1),(19,2,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-07-15 15:20:15','2026-07-17 15:20:15',19,1,2),(20,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','NEW',NULL,'2026-07-21 23:20:15',NULL,20,NULL,3),(21,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-07-03 20:20:15','2026-07-05 20:20:15',21,1,4),(22,4,'Khung vợt chắc, đập cầu uy lực, rất hài lòng.','IN_PROGRESS',NULL,'2026-07-01 00:20:15',NULL,22,1,5),(23,5,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-07-23 13:20:15','2026-07-25 13:20:15',23,1,6),(24,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','NEW',NULL,'2026-08-30 02:20:15',NULL,24,NULL,7),(25,2,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-08-10 17:20:15','2026-08-12 17:20:15',25,1,8),(26,1,'Vợt bị nứt khung sau một tháng sử dụng.','NEW',NULL,'2026-06-30 23:20:15',NULL,26,NULL,1),(27,2,'Vợt bị nứt khung sau một tháng sử dụng.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-08-19 10:20:15','2026-08-22 10:20:15',27,1,2),(28,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','IN_PROGRESS',NULL,'2026-08-19 03:20:15',NULL,28,1,3),(29,2,'Vợt bị nứt khung sau một tháng sử dụng.','RESOLVED','Cửa hàng xin lỗi vì trải nghiệm chưa tốt. Nhân viên đã liên hệ để đổi sản phẩm mới cho bạn.','2026-07-24 00:20:15','2026-07-26 00:20:15',29,1,4),(30,3,'Vợt ổn nhưng cước căng hơi chùng sau 2 tuần.','NEW',NULL,'2026-09-20 09:20:15',NULL,30,NULL,5),(31,4,'Khung vợt chắc, đập cầu uy lực, rất hài lòng.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-06-20 08:20:15','2026-06-21 08:20:15',31,1,6),(32,5,'Khung vợt chắc, đập cầu uy lực, rất hài lòng.','NEW',NULL,'2026-08-01 15:20:15',NULL,32,NULL,7),(33,4,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-09-29 13:20:15','2026-09-30 13:20:15',33,1,8),(34,1,'Giao sai màu so với đơn đặt hàng, mong shop đổi lại.','IN_PROGRESS',NULL,'2026-07-21 12:20:15',NULL,34,1,1),(35,4,'Vợt đầm tay, đánh cầu cao sâu rất dễ.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-09-04 11:20:15','2026-09-07 11:20:15',35,1,2),(36,2,'Vợt bị nứt khung sau một tháng sử dụng.','NEW',NULL,'2026-08-07 01:20:15',NULL,36,NULL,3),(37,4,'Vợt nhẹ đầu, phòng thủ phản tạt nhanh, đáng tiền.','RESOLVED','Cảm ơn bạn đã tin dùng sản phẩm của cửa hàng! Hẹn gặp lại bạn.','2026-06-24 10:20:15','2026-06-27 10:20:15',37,1,4);
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
  `product_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `price` decimal(12,2) NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `brand_id` int NOT NULL,
  `category_id` int NOT NULL,
  `image_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (1,'Demo racket 1',NULL,100000.00,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14',1,1,''),(2,'Demo racket 2',NULL,100000.00,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14',1,1,''),(3,'Demo racket 3',NULL,100000.00,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14',1,1,''),(4,'Demo racket 4',NULL,100000.00,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14',1,1,''),(5,'Demo racket 5',NULL,100000.00,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14',1,1,''),(6,'Demo racket 6',NULL,100000.00,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14',1,1,''),(7,'Demo racket 7',NULL,100000.00,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14',1,1,''),(8,'Demo racket 8',NULL,100000.00,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14',1,1,'');
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `survey_answers`
--

DROP TABLE IF EXISTS `survey_answers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `survey_answers` (
  `answer_id` int NOT NULL AUTO_INCREMENT,
  `answer_text` text COLLATE utf8mb4_unicode_ci,
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
  CONSTRAINT `chk_survey_answers_rating` CHECK (((`rating_value` is null) or (`rating_value` between 1 and 5))),
  CONSTRAINT `survey_answers_chk_1` CHECK ((`rating_value` >= 0))
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
  `option_text` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
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
  `question_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `question_type` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_required` tinyint(1) NOT NULL,
  `sort_order` int NOT NULL,
  `survey_id` int NOT NULL,
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
INSERT INTO `survey_questions` VALUES (1,'How was your shopping experience?','SINGLE_CHOICE',1,0,1);
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
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
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
  CONSTRAINT `fk_survey_recipients_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_survey_recipients_survey` FOREIGN KEY (`survey_id`) REFERENCES `surveys` (`survey_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `survey_recipients`
--

LOCK TABLES `survey_recipients` WRITE;
/*!40000 ALTER TABLE `survey_recipients` DISABLE KEYS */;
INSERT INTO `survey_recipients` VALUES (1,'COMPLETED','2026-10-16 08:20:14',NULL,'2026-10-16 08:20:14',1,1);
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
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `started_at` datetime DEFAULT NULL,
  `submitted_at` datetime DEFAULT NULL,
  `recipient_id` int NOT NULL,
  PRIMARY KEY (`response_id`),
  UNIQUE KEY `recipient_id` (`recipient_id`),
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
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `start_at` datetime DEFAULT NULL,
  `end_at` datetime DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_by` int NOT NULL,
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
INSERT INTO `surveys` VALUES (1,'Demo badminton survey',NULL,NULL,NULL,'ACTIVE','2026-10-16 08:20:14','2026-10-16 08:20:14',1);
/*!40000 ALTER TABLE `surveys` ENABLE KEYS */;
UNLOCK TABLES;
-- ===== BAT DAU: DU LIEU THAT (thay du lieu demo) =====
-- Dan khoi nay ngay TRUOC dong: /*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
SET FOREIGN_KEY_CHECKS=0;
DELETE FROM `products`;
DELETE FROM `categories`;
DELETE FROM `brands`;

LOCK TABLES `brands` WRITE;
/*!40000 ALTER TABLE `brands` DISABLE KEYS */;
REPLACE INTO `brands` VALUES (3,'Yonex','Thương hiệu cầu lông Nhật Bản','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34');
REPLACE INTO `brands` VALUES (4,'Lining','Thương hiệu thể thao Trung Quốc','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34');
REPLACE INTO `brands` VALUES (5,'Victor','Thương hiệu cầu lông Đài Loan','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34');
REPLACE INTO `brands` VALUES (6,'Mizuno','Thương hiệu thể thao Nhật Bản','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34');
REPLACE INTO `brands` VALUES (7,'Apacs','Thương hiệu cầu lông Malaysia','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34');
/*!40000 ALTER TABLE `brands` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
REPLACE INTO `categories` VALUES (1,'Badminton rackets','Vợt cầu lông các dòng thiên công, thủ và toàn diện','ACTIVE','2026-10-05 09:47:24','2026-10-14 15:03:34');
REPLACE INTO `categories` VALUES (5,'Shuttlecocks','Cầu lông thi đấu và tập luyện','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34');
REPLACE INTO `categories` VALUES (6,'Badminton shoes','Giày cầu lông','ACTIVE','2026-10-13 19:44:12','2026-10-14 15:03:34');
REPLACE INTO `categories` VALUES (7,'Badminton bags','Túi và balo đựng vợt','ACTIVE','2026-10-13 19:44:12','2026-10-14 09:55:10');
REPLACE INTO `categories` VALUES (8,'Accessories','Quấn cán, dây cước và phụ kiện','ACTIVE','2026-10-13 19:44:12','2026-10-14 09:55:10');
REPLACE INTO `categories` VALUES (9,'Badminton apparel','Quần áo cầu lông','ACTIVE','2026-10-14 10:04:21','2026-10-14 15:03:34');
/*!40000 ALTER TABLE `categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
REPLACE INTO `products` VALUES (78,'Yonex Astrox 88D Pro','Vợt thiên công, đầu nặng, hợp đánh đôi nam cuối sân',4200000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:03:34',3,1,'https://i.imgur.com/Xs2XCJ6.jpeg');
REPLACE INTO `products` VALUES (79,'Yonex Astrox 99 Pro','Vợt thiên công, đầu nặng, lực đập mạnh',4300000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:10:38',3,1,'https://i.imgur.com/XFEFPT0.jpeg');
REPLACE INTO `products` VALUES (80,'Yonex Arcsaber 11 Pro','Vợt cân bằng, kiểm soát cầu tốt',3800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:12:16',3,1,'https://i.imgur.com/9msX3aJ.jpeg');
REPLACE INTO `products` VALUES (81,'Yonex Nanoflare 800 Pro','Vợt thiên tốc độ, đầu nhẹ, phản hồi nhanh',4000000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:13:50',3,1,'https://i.imgur.com/8mCquG1.jpeg');
REPLACE INTO `products` VALUES (82,'Yonex Duora 10','Vợt hai đầu, linh hoạt công thủ',3500000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:13:40',3,1,'https://i.imgur.com/juLsHih.jpeg');
REPLACE INTO `products` VALUES (83,'Yonex Power Cushion 65 Z3','Giày đệm êm, bám sân tốt',3200000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:15:11',3,6,'https://i.imgur.com/GFxsPzr.jpeg');
REPLACE INTO `products` VALUES (84,'Yonex Aerosensa 50','Cầu lông vũ thi đấu, hộp 12 quả',950000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:15:49',3,5,'https://i.imgur.com/6KdFcrG.jpeg');
REPLACE INTO `products` VALUES (85,'Yonex Áo thi đấu nam','Áo thun thoáng khí cho thi đấu',650000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:16:26',3,9,'https://i.imgur.com/d2wCZYO.jpeg');
REPLACE INTO `products` VALUES (86,'Lining Axforce 80','Vợt thiên công, khung cứng',3300000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:17:23',4,1,'https://i.imgur.com/e0z4dBv.jpeg');
REPLACE INTO `products` VALUES (87,'Lining Windstorm 72','Vợt nhẹ, linh hoạt, phù hợp người mới chơi',1900000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:18:07',4,1,'https://i.imgur.com/NjODJwE.jpeg');
REPLACE INTO `products` VALUES (88,'Lining Aeronaut 9000','Vợt thiên công, đầu nặng',4000000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 16:17:31',4,1,'https://i.imgur.com/93F6k1G.jpeg');
REPLACE INTO `products` VALUES (89,'Lining Turbocharging 75','Vợt thiên tốc độ, nhẹ',2400000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:20:18',4,1,'https://i.imgur.com/NqFuEKf.jpeg');
REPLACE INTO `products` VALUES (90,'Lining Bladex 900','Vợt cân bằng, bền',2800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:20:47',4,1,'https://i.imgur.com/CPs0pT4.jpeg');
REPLACE INTO `products` VALUES (91,'Lining Saga II','Giày nhẹ, hỗ trợ di chuyển nhanh',1800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:21:23',4,6,'https://i.imgur.com/d5oihyp.jpeg');
REPLACE INTO `products` VALUES (92,'Lining A+60','Cầu lông vũ tập luyện, hộp 12 quả',700000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:22:28',4,5,'https://i.imgur.com/Wu1mNuH.jpeg');
REPLACE INTO `products` VALUES (93,'Lining Áo thi đấu nam','Áo thun thoáng khí, co giãn',450000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:22:38',4,9,'https://i.imgur.com/NFacQwV.jpeg');
REPLACE INTO `products` VALUES (94,'Victor Auraspeed 90S','Vợt tốc độ, đầu nhẹ',3300000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:23:33',5,1,'https://i.imgur.com/cjyx7bK.jpeg');
REPLACE INTO `products` VALUES (95,'Victor Thruster Ryuga II','Vợt thiên công, đầu nặng',3600000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:24:16',5,1,'https://i.imgur.com/uFe7miv.jpeg');
REPLACE INTO `products` VALUES (96,'Victor Jetspeed S 12','Vợt tốc độ, đầu nhẹ',3200000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:24:52',5,1,'https://i.imgur.com/LxQnsJ4.jpeg');
REPLACE INTO `products` VALUES (97,'Victor Drive X 9X','Vợt cân bằng, đa dụng',3100000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:25:45',5,1,'https://i.imgur.com/AY9sy0U.jpeg');
REPLACE INTO `products` VALUES (98,'Victor Brave Sword 12','Vợt thiên công, dễ kiểm soát',2800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 16:17:13',5,1,'https://i.imgur.com/wjB6oWu.jpeg');
REPLACE INTO `products` VALUES (99,'Victor P9200','Giày ổn định, hỗ trợ cổ chân',2500000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:27:55',5,6,'https://i.imgur.com/hl6DGNB.jpeg');
REPLACE INTO `products` VALUES (100,'Victor Gold No.1','Cầu lông vũ, hộp 12 quả',800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:27:43',5,5,'https://i.imgur.com/WUR6gNc.jpeg');
REPLACE INTO `products` VALUES (101,'Victor Áo thi đấu nam','Áo thun thoáng khí cho thi đấu',500000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:27:31',5,9,'https://i.imgur.com/WrFioUJ.jpeg');
REPLACE INTO `products` VALUES (102,'Mizuno Fortius 10 Quick','Vợt thiên tốc độ, đầu nhẹ',2800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:28:57',6,1,'https://i.imgur.com/HXpI9bt.jpeg');
REPLACE INTO `products` VALUES (103,'Mizuno Fortius 30 Power','Vợt thiên công, đầu nặng',3000000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:30:04',6,1,'https://i.imgur.com/xu5HUQn.jpeg');
REPLACE INTO `products` VALUES (104,'Mizuno Altius 01 Speed','Vợt nhẹ, linh hoạt',2500000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:30:35',6,1,'https://i.imgur.com/GsttcMO.jpeg');
REPLACE INTO `products` VALUES (105,'Mizuno Altius 03 Feel','Vợt cân bằng, cảm giác cầu tốt',2600000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:31:53',6,1,'https://i.imgur.com/vaAtEUX.jpeg');
REPLACE INTO `products` VALUES (106,'Mizuno Acrospeed 5.0','Vợt tầm trung cho người mới',1800000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:32:22',6,1,'https://i.imgur.com/4c4orId.jpeg');
REPLACE INTO `products` VALUES (107,'Mizuno Wave Claw 2','Giày nhẹ, linh hoạt',3200000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 16:17:49',6,6,'https://i.imgur.com/WSROf0I.jpeg');
REPLACE INTO `products` VALUES (108,'Mizuno Cầu tập luyện','Cầu tập luyện, hộp 12 quả',600000.00,'INACTIVE','2026-10-14 10:04:21','2026-10-14 15:33:37',6,5,'');
REPLACE INTO `products` VALUES (109,'Mizuno Áo thi đấu nam','Áo thun thoáng khí, thấm hút tốt',450000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:59:09',6,9,'https://i.imgur.com/aOJdEMv.jpeg');
REPLACE INTO `products` VALUES (110,'Apacs Nano Fusion Speed 722','Vợt tầm trung, thiên tốc độ',2200000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:35:59',7,1,'https://i.imgur.com/DtsE3lD.jpeg');
REPLACE INTO `products` VALUES (111,'Apacs Feather Weight 55','Vợt siêu nhẹ cho người mới',1600000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:36:38',7,1,'https://i.imgur.com/t9Ovk0U.jpeg');
REPLACE INTO `products` VALUES (112,'Apacs Z-Ziggler','Vợt thiên công, cứng',2400000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:37:15',7,1,'https://i.imgur.com/6yXd346.jpeg');
REPLACE INTO `products` VALUES (113,'Apacs Edgesaber 10','Vợt cân bằng, đa dụng',2000000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:37:59',7,1,'https://i.imgur.com/jv3ufh2.jpeg');
REPLACE INTO `products` VALUES (114,'Apacs Virtuoso Pro','Vợt thiên tốc độ, nhẹ',2300000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:38:36',7,1,'https://i.imgur.com/02l3P1e.jpeg');
REPLACE INTO `products` VALUES (115,'Apacs Cushion Pro','Giày đệm êm cho tập luyện',1500000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:39:23',7,6,'https://i.imgur.com/eCAtV3F.jpeg');
REPLACE INTO `products` VALUES (116,'Apacs Cầu lông vũ','Cầu lông vũ, hộp 12 quả',650000.00,'INACTIVE','2026-10-14 10:04:21','2026-10-14 15:40:09',7,5,'');
REPLACE INTO `products` VALUES (117,'Apacs Áo thi đấu nam','Áo thun thoáng khí cho tập luyện',350000.00,'ACTIVE','2026-10-14 10:04:21','2026-10-14 15:41:18',7,9,'https://i.imgur.com/uES1S6c.jpeg');
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

-- ===== KET THUC =====
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-16 15:20:23



-- MySQL dump 10.13  Distrib 8.4.11, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: crm_db_v2
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
  `address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `full_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `gender` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `playing_level` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`account_id`),
  UNIQUE KEY `uq_accounts_email` (`email`),
  CONSTRAINT `chk_accounts_role` CHECK ((`role` in (_utf8mb4'ADMIN',_utf8mb4'MANAGER',_utf8mb4'CUSTOMER'))),
  CONSTRAINT `chk_accounts_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'LOCKED')))
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `accounts`
--

LOCK TABLES `accounts` WRITE;
/*!40000 ALTER TABLE `accounts` DISABLE KEYS */;
INSERT INTO `accounts` VALUES (1,'admin1@gmail.com','pbkdf2_sha256$1000000$vznUfaTzOEf5tUQFbvZtHW$utChDolwvHxBNTY4X5U+/5fwO+eitq92jBehvUBoeDc=','ADMIN','ACTIVE','2026-11-02 14:04:01','2026-10-15 01:54:06','2026-11-02 21:04:00',NULL,NULL,'',NULL,NULL,NULL),(2,'ttdkhiem3@gmail.com','pbkdf2_sha256$1000000$Qk2sXBaLKcJZSKSgm83kS7$efUZj3AOvIweHipiEvnuxed2YGpFsckpEuTMtNBOXfg=','CUSTOMER','ACTIVE','2026-10-29 02:03:52','2026-10-15 02:06:05','2026-10-29 02:05:30','854 Tạ Quang Bửu P5 Q8','2003-11-18','Trần Trọng Duy Khiêm',NULL,'+84909786029','BEGINNER'),(3,'manager@gmail.com','pbkdf2_sha256$1000000$NYoAJsq6hIG4RCUzFQOEz2$ykUisr2rhlA6+WZXJ+y80PPM0vEuZt9QTXb0EKhp9vs=','MANAGER','ACTIVE','2026-10-17 14:06:47','2026-10-17 14:06:40','2026-10-17 21:06:46',NULL,NULL,'',NULL,NULL,NULL),(5,'manger1@gmail.com','pbkdf2_sha256$1000000$i1wJWbpd6m3uopKGOyJtqc$ckKLvIeK0clYi+b78rlbYMJYa91zG+BTb1upTlQH3tM=','MANAGER','ACTIVE','2026-10-29 02:00:41','2026-10-17 14:33:41','2026-10-29 02:16:50',NULL,NULL,'',NULL,NULL,NULL),(8,'1234@gmail.com','pbkdf2_sha256$1000000$Gok9El4xgZwQmj25BGsouj$hmwXG9CWyqlhi2J/4VxwuwlQKLevf/qonkTecTNXX9k=','CUSTOMER','ACTIVE','2026-10-17 15:17:49','2026-10-17 15:17:38','2026-10-29 08:59:16','Address','2026-10-08','abc','MALE','0901234567','BEGINNER'),(12,'cus4@gmail.com','pbkdf2_sha256$1000000$bqQR1f9vwy28wejl6QMzrT$wb+wLaM7FM82HD1g5sF1w4VV1MKNBMUIQOSRZb6nF5c=','CUSTOMER','ACTIVE','2026-10-17 15:58:13','2026-10-17 15:31:17','2026-10-17 22:58:13','123','2026-10-08','khim','OTHER','0912345671','COMPETITIVE'),(13,'admin2@gmail.com','pbkdf2_sha256$1000000$WX1ZbzzSyX9PsydPHJ4bt4$uU0EIx7qU26iVpdI/hXl3UhDT8pipg+A0HeAl+tD5qY=','ADMIN','ACTIVE','2026-10-29 02:11:16','2026-10-29 01:58:20','2026-10-29 09:11:15',NULL,NULL,'',NULL,NULL,NULL),(14,'cus1@gmail.com','pbkdf2_sha256$1000000$g5bwtZUQwSoJpO6S5ihhTn$Tu313x4hAXD43u9OcXaOxh8Wo4mVJfOYOb9aFYqXuAM=','CUSTOMER','ACTIVE','2026-11-02 16:38:17','2026-10-29 02:07:07','2026-11-02 23:38:16','123 Tung Tung','1995-10-17','Customer One','MALE','0901234561','RECREATIONAL'),(15,'manager1@gmail.com','pbkdf2_sha256$1000000$CTPSONqp7ufewpdeYcCPEO$HoEiqCa1VDH4+TgU01OQCMdmU7lvOWCs9T9FB3EnEfc=','MANAGER','ACTIVE','2026-11-02 16:44:00','2026-10-29 02:31:38','2026-11-02 23:43:59',NULL,NULL,'',NULL,NULL,NULL),(16,'1232@gmail.com','pbkdf2_sha256$1000000$PYs3BAyTlACELnZnFPzD92$FK+aJFpinZ7mi2qWlhL8ZeKWZc8RhgG/aBb3VSvbcwY=','CUSTOMER','ACTIVE','2026-11-02 16:44:28','2026-11-02 16:43:07','2026-11-02 23:44:28','123','2014-06-18','custo','MALE','0901234512',NULL);
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
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add account',6,'add_account'),(22,'Can change account',6,'change_account'),(23,'Can delete account',6,'delete_account'),(24,'Can view account',6,'view_account'),(25,'Can add brand',7,'add_brand'),(26,'Can change brand',7,'change_brand'),(27,'Can delete brand',7,'delete_brand'),(28,'Can view brand',7,'view_brand'),(29,'Can add category',8,'add_category'),(30,'Can change category',8,'change_category'),(31,'Can delete category',8,'delete_category'),(32,'Can view category',8,'view_category'),(33,'Can add supplier',9,'add_supplier'),(34,'Can change supplier',9,'change_supplier'),(35,'Can delete supplier',9,'delete_supplier'),(36,'Can view supplier',9,'view_supplier'),(37,'Can add product',10,'add_product'),(38,'Can change product',10,'change_product'),(39,'Can delete product',10,'delete_product'),(40,'Can view product',10,'view_product'),(41,'Can add customer',11,'add_customer'),(42,'Can change customer',11,'change_customer'),(43,'Can delete customer',11,'delete_customer'),(44,'Can view customer',11,'view_customer'),(45,'Can add customer preference',12,'add_customerpreference'),(46,'Can change customer preference',12,'change_customerpreference'),(47,'Can delete customer preference',12,'delete_customerpreference'),(48,'Can view customer preference',12,'view_customerpreference'),(49,'Can add feedback',13,'add_feedback'),(50,'Can change feedback',13,'change_feedback'),(51,'Can delete feedback',13,'delete_feedback'),(52,'Can view feedback',13,'view_feedback'),(53,'Can add survey',14,'add_survey'),(54,'Can change survey',14,'change_survey'),(55,'Can delete survey',14,'delete_survey'),(56,'Can view survey',14,'view_survey'),(57,'Can add survey question',15,'add_surveyquestion'),(58,'Can change survey question',15,'change_surveyquestion'),(59,'Can delete survey question',15,'delete_surveyquestion'),(60,'Can view survey question',15,'view_surveyquestion'),(61,'Can add survey option',16,'add_surveyoption'),(62,'Can change survey option',16,'change_surveyoption'),(63,'Can delete survey option',16,'delete_surveyoption'),(64,'Can view survey option',16,'view_surveyoption'),(65,'Can add survey recipient',17,'add_surveyrecipient'),(66,'Can change survey recipient',17,'change_surveyrecipient'),(67,'Can delete survey recipient',17,'delete_surveyrecipient'),(68,'Can view survey recipient',17,'view_surveyrecipient'),(69,'Can add survey response',18,'add_surveyresponse'),(70,'Can change survey response',18,'change_surveyresponse'),(71,'Can delete survey response',18,'delete_surveyresponse'),(72,'Can view survey response',18,'view_surveyresponse'),(73,'Can add survey answer',19,'add_surveyanswer'),(74,'Can change survey answer',19,'change_surveyanswer'),(75,'Can delete survey answer',19,'delete_surveyanswer'),(76,'Can view survey answer',19,'view_surveyanswer'),(77,'Can add role',20,'add_role'),(78,'Can change role',20,'change_role'),(79,'Can delete role',20,'delete_role'),(80,'Can view role',20,'view_role'),(81,'Can add admin',21,'add_admin'),(82,'Can change admin',21,'change_admin'),(83,'Can delete admin',21,'delete_admin'),(84,'Can view admin',21,'view_admin'),(85,'Can add staff',22,'add_staff'),(86,'Can change staff',22,'change_staff'),(87,'Can delete staff',22,'delete_staff'),(88,'Can view staff',22,'view_staff');
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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `brands`
--

LOCK TABLES `brands` WRITE;
/*!40000 ALTER TABLE `brands` DISABLE KEYS */;
INSERT INTO `brands` VALUES (1,'Yonex','Thương hiệu cầu lông Nhật Bản','ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37'),(2,'Lining','Thương hiệu thể thao Trung Quốc','ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37'),(3,'Victor','Thương hiệu cầu lông Đài Loan','ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37'),(4,'Mizuno','Thương hiệu thể thao Nhật Bản','ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37'),(5,'Apacs','Thương hiệu cầu lông Malaysia','ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37'),(6,'BRAINROT','TUNG TUNG TUNG SIGMA BOI','ACTIVE','2026-10-17 15:02:05','2026-10-17 15:02:05');
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
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories`
--

LOCK TABLES `categories` WRITE;
/*!40000 ALTER TABLE `categories` DISABLE KEYS */;
INSERT INTO `categories` VALUES (1,'Vợt cầu lông','Vợt cầu lông các dòng thiên công, thủ và toàn diện','ACTIVE','2026-10-15 01:53:37','2026-10-22 01:16:26'),(2,'Giày','Giày cầu lông','ACTIVE','2026-10-15 01:53:37','2026-10-22 01:16:39'),(3,'Ống cầu','Cầu lông thi đấu và tập luyện','ACTIVE','2026-10-15 01:53:37','2026-10-22 01:16:33'),(4,'Quần áo','Quần áo cầu lông','ACTIVE','2026-10-15 01:53:37','2026-10-22 01:15:27');
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
  CONSTRAINT `fk_customer_preferences_customer` FOREIGN KEY (`customer_id`) REFERENCES `accounts` (`account_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_customer_preferences_type` CHECK ((`preference_type` in (_utf8mb4'BRAND',_utf8mb4'CATEGORY',_utf8mb4'FAVORITE_BRAND',_utf8mb4'FAVORITE_BRAND_OTHER')))
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `customer_preferences`
--

LOCK TABLES `customer_preferences` WRITE;
/*!40000 ALTER TABLE `customer_preferences` DISABLE KEYS */;
INSERT INTO `customer_preferences` VALUES (8,'CATEGORY','Giày','2026-10-29 02:08:39',14),(9,'FAVORITE_BRAND','Yonex','2026-10-29 02:08:39',14);
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
INSERT INTO `django_content_type` VALUES (6,'accounts','account'),(21,'accounts','admin'),(20,'accounts','role'),(22,'accounts','staff'),(1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(7,'catalog','brand'),(8,'catalog','category'),(10,'catalog','product'),(9,'catalog','supplier'),(4,'contenttypes','contenttype'),(11,'customers','customer'),(12,'customers','customerpreference'),(13,'feedback','feedback'),(5,'sessions','session'),(14,'surveys','survey'),(19,'surveys','surveyanswer'),(16,'surveys','surveyoption'),(15,'surveys','surveyquestion'),(17,'surveys','surveyrecipient'),(18,'surveys','surveyresponse');
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
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-10-15 01:53:24.091189'),(2,'contenttypes','0002_remove_content_type_name','2026-10-15 01:53:24.191779'),(3,'auth','0001_initial','2026-10-15 01:53:24.581047'),(4,'auth','0002_alter_permission_name_max_length','2026-10-15 01:53:24.685720'),(5,'auth','0003_alter_user_email_max_length','2026-10-15 01:53:24.691720'),(6,'auth','0004_alter_user_username_opts','2026-10-15 01:53:24.696719'),(7,'auth','0005_alter_user_last_login_null','2026-10-15 01:53:24.701719'),(8,'auth','0006_require_contenttypes_0002','2026-10-15 01:53:24.704719'),(9,'auth','0007_alter_validators_add_error_messages','2026-10-15 01:53:24.709721'),(10,'auth','0008_alter_user_username_max_length','2026-10-15 01:53:24.713719'),(11,'auth','0009_alter_user_last_name_max_length','2026-10-15 01:53:24.718719'),(12,'auth','0010_alter_group_name_max_length','2026-10-15 01:53:24.730719'),(13,'auth','0011_update_proxy_permissions','2026-10-15 01:53:24.739844'),(14,'auth','0012_alter_user_first_name_max_length','2026-10-15 01:53:24.764360'),(15,'accounts','0001_initial','2026-10-15 01:53:25.201721'),(16,'admin','0001_initial','2026-10-15 01:53:25.418874'),(17,'admin','0002_logentry_remove_auto_add','2026-10-15 01:53:25.430867'),(18,'admin','0003_logentry_add_action_flag_choices','2026-10-15 01:53:25.447884'),(19,'catalog','0001_initial','2026-10-15 01:53:26.668111'),(20,'catalog','0002_product_image_url','2026-10-15 01:53:26.957199'),(21,'customers','0001_initial','2026-10-15 01:53:27.243790'),(22,'feedback','0001_initial','2026-10-15 01:53:27.719267'),(23,'sessions','0001_initial','2026-10-15 01:53:27.806050'),(24,'surveys','0001_initial','2026-10-15 01:53:29.088921'),(25,'surveys','0002_schema_contract','2026-10-15 01:53:36.221888'),(26,'accounts','0002_remove_account_chk_accounts_role_alter_account_role_and_more','2026-10-17 13:43:54.592416'),(27,'surveys','0003_questionnaire_configuration','2026-10-21 07:38:53.050430'),(28,'surveys','0004_survey_objective_audience','2026-10-21 07:38:53.163416'),(29,'accounts','0003_role_admin_staff','2026-10-22 02:00:58.044129'),(30,'accounts','0004_remove_staff_account_account_address_and_more','2026-10-22 02:00:59.213087'),(31,'surveys','0005_alter_surveyrecipient_customer','2026-10-22 02:00:59.234104'),(32,'feedback','0002_alter_feedback_customer_alter_feedback_handled_by','2026-10-22 02:00:59.265634'),(33,'customers','0002_alter_customerpreference_customer_delete_customer_and_more','2026-10-22 02:00:59.308629'),(34,'customers','0003_remove_play_style','2026-11-02 14:03:41.789237'),(35,'customers','0004_supported_preference_types','2026-11-02 14:03:41.930424'),(36,'feedback','0003_two_status_feedback','2026-11-02 14:03:42.052656'),(37,'surveys','0006_reconcile_rating_constraint','2026-11-02 14:03:42.067708');
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
INSERT INTO `django_session` VALUES ('5h4k1ohs9jrrqg8ep5nf4dvlie1yvw3l','.eJxVjMsOwiAURP-FtSFQKA-X7vsN5D6orRpISrsy_rtt0oWuJplzZt4iwbZOaWt5STOLq9BWXH5LBHrmchB-QLlXSbWsy4zyUORJmxwq59ftdP8OJmjTvs4-OEDmPvQMqrOjdmQ6HLOOQSsg9BSZnKOoSHe5V24PDN4aYGNHLz5fHnI4XQ:1xMFYY:avYfU7D_-cjR1shB6Si7uXTPYcfwELgYhLtWQJoism8','2026-11-12 02:07:54.034878'),('9prx2cxmh9t2y6vfrheum6pzkouu5ar2','.eJxVjMsOwiAQRf-FtSGUNy7d-w1kmAGpGkhKuzL-uzbpQrf3nHNfLMK21riNvMSZ2JlNkp1-xwT4yG0ndId26xx7W5c58V3hBx382ik_L4f7d1Bh1G_ts9WTLyIUbSV6giTAOGupqEQYpClEUgqtjYTgHWmHIJRSXhERBGTvDwf9ODs:1xI6nV:Tx38UucHI4heWjX3DBVveN-UEgGuIZR57EhfNi3Fa7c','2026-10-31 15:58:13.199930'),('a9vthr77zkur5x2z10qsopkskm9x46d4','.eJxVjMsOwiAQRf-FtSE8hsK4dO83kBkgUjWQlHZl_Hdt0oVu7znnvkSkba1xG2WJcxZnoZ04_Y5M6VHaTvKd2q3L1Nu6zCx3RR50yGvP5Xk53L-DSqN-aw-TSeCddb54xQFdBszBkA8hoLKoQTvDBVATsTKT4-wNKiZLCQnE-wPNhTby:1xNv8Z:0_t5QIH7BiUXUH2UO8w1zZW9JoiBkcVaYIbyJQZR8I0','2026-11-16 16:43:59.793786'),('fp78rf2seccaayao9rprgadze7x81qww','.eJxVjMsOwiAQRf-FtSEBOjxcuvcbyAwDUjWQlHZl_Hdt0oVu7znnvkTEba1xG3mJM4uzUFacfkfC9MhtJ3zHdusy9bYuM8ldkQcd8to5Py-H-3dQcdRv7YvyQYNl1ASayLgpK63AEjhvPAHjNJUMJhVrLIUQVHba6sCQGEwR7w_w_zeR:1xNv92:m_aogTbD_S9Ww5nthHflNEZ9GFvIsLh6uIME2ICi_zA','2026-11-16 16:44:28.308609'),('fqr26yam8wn19xmrcwpcx10evtux57r1','.eJxVjMsOwiAURP-FtSFQKA-X7vsN5D6orRpISrsy_rtt0oWuJplzZt4iwbZOaWt5STOLq9BWXH5LBHrmchB-QLlXSbWsy4zyUORJmxwq59ftdP8OJmjTvs4-OEDmPvQMqrOjdmQ6HLOOQSsg9BSZnKOoSHe5V24PDN4aYGNHLz5fHnI4XQ:1xMG8G:VCGqH7iPt4aiC6Ei8oLfw4Y_1-RSjej6tx1r6T5Y8TQ','2026-11-12 02:44:48.963273'),('pnonm2ukwfpr8scio0d9sny53equ1lsh','.eJxVjDsOwjAQRO_iGlnrxJ-Ekj5nsOxdLw4gW8qnQtwdR0oB0lTz3sxb-LBv2e9rWvxM4ioGcfntYsBnKgegRyj3KrGWbZmjPBR50lVOldLrdrp_Bzmsua1t74ZoHWPQ2kJLHA0rStQDQ4-Ous40gRnQKBxRjRqCYrBoGQyR-HwB2c030A:1xI6AO:Cg6Fg84K37e04QpzjIM2villm_M2TUh2_XVwCfzk_7Q','2026-10-31 15:17:48.743777'),('y1a6u2qwh1rcdv2eepdx275u0e5nubdj','.eJxVjDsOwjAQBe_iGllmE_8o6XMGa7324gCypTipEHeHSCmgfTPzXiLgtpaw9byEOYmLAHH63SLSI9cdpDvWW5PU6rrMUe6KPGiXU0v5eT3cv4OCvXzr0Y-EjNEmSpmsdQOCB0OZR2NIg6IzRs9asYXBM1nHyqDyBEzO6CTeHwpyOKQ:1xJhl5:ggrF8eixg5w3HavUURz4Jyb8Vu-KXXNkocfP09WsMSQ','2026-11-05 01:38:19.265892');
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
  CONSTRAINT `fk_feedbacks_customer` FOREIGN KEY (`customer_id`) REFERENCES `accounts` (`account_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_feedbacks_handled_by` FOREIGN KEY (`handled_by`) REFERENCES `accounts` (`account_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_feedbacks_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_feedbacks_rating` CHECK (((`rating` >= 1) and (`rating` <= 5))),
  CONSTRAINT `chk_feedbacks_status` CHECK ((`status` in (_utf8mb4'NEW',_utf8mb4'RESOLVED'))),
  CONSTRAINT `feedbacks_chk_1` CHECK ((`rating` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feedbacks`
--

LOCK TABLES `feedbacks` WRITE;
/*!40000 ALTER TABLE `feedbacks` DISABLE KEYS */;
INSERT INTO `feedbacks` VALUES (1,5,'Sản phẩm ok nha shop','RESOLVED','ok','2026-10-17 15:55:50','2026-10-17 15:58:27',12,5,3);
/*!40000 ALTER TABLE `feedbacks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `migration_profile_archive`
--

DROP TABLE IF EXISTS `migration_profile_archive`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `migration_profile_archive` (
  `source_table` varchar(32) NOT NULL,
  `source_id` int NOT NULL,
  `account_id` int NOT NULL,
  `payload` json NOT NULL,
  PRIMARY KEY (`source_table`,`source_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `migration_profile_archive`
--

LOCK TABLES `migration_profile_archive` WRITE;
/*!40000 ALTER TABLE `migration_profile_archive` DISABLE KEYS */;
INSERT INTO `migration_profile_archive` VALUES ('customers',1,2,'{\"phone\": \"+84909786029\", \"gender\": null, \"status\": \"ACTIVE\", \"address\": \"854 Tạ Quang Bửu P5 Q8\", \"full_name\": \"Trần Trọng Duy Khiêm\", \"account_id\": 2, \"created_at\": \"2026-10-15 02:06:06+00:00\", \"deleted_at\": null, \"updated_at\": \"2026-10-15 02:06:06+00:00\", \"customer_id\": 1, \"date_of_birth\": \"2003-11-18\", \"playing_level\": \"BEGINNER\"}'),('customers',2,6,'{\"phone\": \"0909111111\", \"gender\": \"MALE\", \"status\": \"DELETED\", \"address\": \"123\", \"full_name\": \"Khiêm Trần\", \"account_id\": 6, \"created_at\": \"2026-10-17 15:05:42+00:00\", \"deleted_at\": \"2026-10-17 15:11:54+00:00\", \"updated_at\": \"2026-10-17 15:11:54+00:00\", \"customer_id\": 2, \"date_of_birth\": \"2026-10-15\", \"playing_level\": \"BEGINNER\"}'),('customers',3,8,'{\"phone\": \"0901234567\", \"gender\": \"MALE\", \"status\": \"ACTIVE\", \"address\": \"Address\", \"full_name\": \"abc\", \"account_id\": 8, \"created_at\": \"2026-10-17 15:17:39+00:00\", \"deleted_at\": null, \"updated_at\": \"2026-10-17 15:17:39+00:00\", \"customer_id\": 3, \"date_of_birth\": \"2026-10-08\", \"playing_level\": \"BEGINNER\"}'),('customers',4,10,'{\"phone\": \"0909111112\", \"gender\": \"MALE\", \"status\": \"ACTIVE\", \"address\": \"123\", \"full_name\": \"cus2\", \"account_id\": 10, \"created_at\": \"2026-10-17 15:23:17+00:00\", \"deleted_at\": null, \"updated_at\": \"2026-10-17 15:23:17+00:00\", \"customer_id\": 4, \"date_of_birth\": \"2026-10-15\", \"playing_level\": \"BEGINNER\"}'),('customers',5,12,'{\"phone\": \"0912345671\", \"gender\": \"OTHER\", \"status\": \"ACTIVE\", \"address\": \"123\", \"full_name\": \"khim\", \"account_id\": 12, \"created_at\": \"2026-10-17 15:31:17+00:00\", \"deleted_at\": null, \"updated_at\": \"2026-10-17 16:07:22+00:00\", \"customer_id\": 5, \"date_of_birth\": \"2026-10-08\", \"playing_level\": \"COMPETITIVE\"}');
/*!40000 ALTER TABLE `migration_profile_archive` ENABLE KEYS */;
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
  `supplier_id` int NOT NULL,
  `image_url` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`product_id`),
  KEY `idx_products_category` (`category_id`),
  KEY `idx_products_brand` (`brand_id`),
  KEY `idx_products_supplier` (`supplier_id`),
  KEY `idx_products_name` (`product_name`),
  KEY `idx_products_status` (`status`),
  KEY `idx_products_price` (`price`),
  CONSTRAINT `fk_products_brand` FOREIGN KEY (`brand_id`) REFERENCES `brands` (`brand_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_products_category` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_products_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`supplier_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_products_price` CHECK ((`price` >= 0)),
  CONSTRAINT `chk_products_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'INACTIVE')))
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (2,'Yonex Astrox 99 Pro','Vợt thiên công, đầu nặng, lực đập mạnh',4300000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-29 02:02:23',3,1,6,'https://i.imgur.com/XFEFPT0.jpeg'),(3,'Yonex Arcsaber 11 Pro','Vợt cân bằng, kiểm soát cầu tốt',3800000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',1,1,1,'https://i.imgur.com/9msX3aJ.jpeg'),(4,'Yonex Nanoflare 800 Pro','Vợt thiên tốc độ, đầu nhẹ, phản hồi nhanh',4000000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',1,1,1,'https://i.imgur.com/8mCquG1.jpeg'),(5,'Yonex Duora 10','Vợt hai đầu, linh hoạt công thủ',3500000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',1,1,1,'https://i.imgur.com/juLsHih.jpeg'),(6,'Yonex Power Cushion 65 Z3','Giày đệm êm, bám sân tốt',3200000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',1,2,1,'https://i.imgur.com/GFxsPzr.jpeg'),(7,'Yonex Aerosensa 50','Cầu lông vũ thi đấu, hộp 12 quả',950000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',1,3,1,'https://i.imgur.com/6KdFcrG.jpeg'),(8,'Yonex Áo thi đấu nam','Áo thun thoáng khí cho thi đấu',650000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',1,4,1,'https://i.imgur.com/d2wCZYO.jpeg'),(9,'Lining Axforce 80','Vợt thiên công, khung cứng',3300000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',2,1,2,'https://i.imgur.com/e0z4dBv.jpeg'),(10,'Lining Windstorm 72','Vợt nhẹ, linh hoạt, phù hợp người mới chơi',1900000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',2,1,2,'https://i.imgur.com/NjODJwE.jpeg'),(11,'Lining Aeronaut 9000','Vợt thiên công, đầu nặng',3000000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',2,1,2,'https://i.imgur.com/93F6k1G.jpeg'),(12,'Lining Turbocharging 75','Vợt thiên tốc độ, nhẹ',2400000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',2,1,2,'https://i.imgur.com/NqFuEKf.jpeg'),(13,'Lining Bladex 900','Vợt cân bằng, bền',2800000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',2,1,2,'https://i.imgur.com/CPs0pT4.jpeg'),(14,'Lining Saga II','Giày nhẹ, hỗ trợ di chuyển nhanh',1800000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',2,2,2,'https://i.imgur.com/d5oihyp.jpeg'),(15,'Lining A+60','Cầu lông vũ tập luyện, hộp 12 quả',700000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',2,3,2,'https://i.imgur.com/Wu1mNuH.jpeg'),(16,'Lining Áo thi đấu nam','Áo thun thoáng khí, co giãn',450000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',2,4,2,'https://i.imgur.com/NFacQwV.jpeg'),(17,'Victor Auraspeed 90S','Vợt tốc độ, đầu nhẹ',3300000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',3,1,3,'https://i.imgur.com/cjyx7bK.jpeg'),(18,'Victor Thruster Ryuga II','Vợt thiên công, đầu nặng',3600000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',3,1,3,'https://i.imgur.com/uFe7miv.jpeg'),(19,'Victor Jetspeed S 12','Vợt tốc độ, đầu nhẹ',3200000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',3,1,3,'https://i.imgur.com/LxQnsJ4.jpeg'),(20,'Victor Drive X 9X','Vợt cân bằng, đa dụng',3100000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',3,1,3,'https://i.imgur.com/AY9sy0U.jpeg'),(21,'Victor Brave Sword 12','Vợt thiên công, dễ kiểm soát',2800000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',3,1,3,'https://i.imgur.com/wjB6oWu.jpeg'),(22,'Victor P9200','Giày ổn định, hỗ trợ cổ chân',2500000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',3,2,3,'https://i.imgur.com/hl6DGNB.jpeg'),(23,'Victor Gold No.1','Cầu lông vũ, hộp 12 quả',800000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',3,3,3,'https://i.imgur.com/WUR6gNc.jpeg'),(24,'Victor Áo thi đấu nam','Áo thun thoáng khí cho thi đấu',500000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',3,4,3,'https://i.imgur.com/WrFioUJ.jpeg'),(25,'Mizuno Fortius 10 Quick','Vợt thiên tốc độ, đầu nhẹ',2800000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',4,1,4,'https://i.imgur.com/HXpI9bt.jpeg'),(26,'Mizuno Fortius 30 Power','Vợt thiên công, đầu nặng',3000000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',4,1,4,'https://i.imgur.com/xu5HUQn.jpeg'),(27,'Mizuno Altius 01 Speed','Vợt nhẹ, linh hoạt',2500000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',4,1,4,'https://i.imgur.com/GsttcMO.jpeg'),(28,'Mizuno Altius 03 Feel','Vợt cân bằng, cảm giác cầu tốt',2600000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',4,1,4,'https://i.imgur.com/vaAtEUX.jpeg'),(29,'Mizuno Acrospeed 5.0','Vợt tầm trung cho người mới',1800000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',4,1,4,'https://i.imgur.com/4c4orId.jpeg'),(30,'Mizuno Wave Claw 2','Giày nhẹ, linh hoạt',2200000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',4,2,4,'https://i.imgur.com/WSROf0I.jpeg'),(31,'Mizuno Cầu tập luyện','Cầu tập luyện, hộp 12 quả',600000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',4,3,4,''),(32,'Mizuno Áo thi đấu nam','Áo thun thoáng khí, thấm hút tốt',550000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',4,4,4,'https://i.imgur.com/aOJdEMv.jpeg'),(33,'Apacs Nano Fusion Speed 722','Vợt tầm trung, thiên tốc độ',2200000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',5,1,6,'https://i.imgur.com/DtsE3lD.jpeg'),(34,'Apacs Feather Weight 55','Vợt siêu nhẹ cho người mới',1600000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',5,1,6,'https://i.imgur.com/t9Ovk0U.jpeg'),(35,'Apacs Z-Ziggler','Vợt thiên công, cứng',2400000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',5,1,6,'https://i.imgur.com/6yXd346.jpeg'),(36,'Apacs Edgesaber 10','Vợt cân bằng, đa dụng',2000000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',5,1,6,'https://i.imgur.com/jv3ufh2.jpeg'),(37,'Apacs Virtuoso Pro','Vợt thiên tốc độ, nhẹ',2300000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',5,1,6,'https://i.imgur.com/02l3P1e.jpeg'),(38,'Apacs Cushion Pro','Giày đệm êm cho tập luyện',1500000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',5,2,6,'https://i.imgur.com/eCAtV3F.jpeg'),(39,'Apacs Cầu lông vũ','Cầu lông vũ, hộp 12 quả',650000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',5,3,6,''),(40,'Apacs Áo thi đấu nam','Áo thun thoáng khí cho tập luyện',350000.00,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37',5,4,6,'https://i.imgur.com/uES1S6c.jpeg'),(42,'67','123',67000.00,'ACTIVE','2026-10-17 15:02:33','2026-10-17 15:02:33',6,1,6,'');
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
  `role_code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role_name` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`role_id`),
  UNIQUE KEY `role_code` (`role_code`),
  UNIQUE KEY `uq_roles_code` (`role_code`),
  CONSTRAINT `chk_roles_code` CHECK ((`role_code` in (_utf8mb4'ADMIN',_utf8mb4'MANAGER',_utf8mb4'CUSTOMER')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `suppliers`
--

DROP TABLE IF EXISTS `suppliers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `suppliers` (
  `supplier_id` int NOT NULL AUTO_INCREMENT,
  `supplier_code` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `supplier_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ACTIVE',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`supplier_id`),
  UNIQUE KEY `uq_suppliers_code` (`supplier_code`),
  KEY `idx_suppliers_name` (`supplier_name`),
  KEY `idx_suppliers_status` (`status`),
  CONSTRAINT `chk_suppliers_status` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'INACTIVE')))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `suppliers`
--

LOCK TABLES `suppliers` WRITE;
/*!40000 ALTER TABLE `suppliers` DISABLE KEYS */;
INSERT INTO `suppliers` VALUES (1,'SUP001','Yonex Vietnam',NULL,NULL,NULL,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37'),(2,'SUP002','Lining Sports',NULL,NULL,NULL,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37'),(3,'SUP003','Victor Distribution',NULL,NULL,NULL,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37'),(4,'SUP004','Mizuno Sports',NULL,NULL,NULL,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37'),(5,'SUP005','Kawasaki Badminton',NULL,NULL,NULL,'ACTIVE','2026-10-15 01:53:37','2026-10-15 01:53:37'),(6,'SUP006','Apacs Vietnam','123','123123123123','123@gmail.com','ACTIVE','2026-10-15 01:53:37','2026-10-17 14:52:48'),(7,'sup67','Yolex','123','123123123123','123@gmail.com','ACTIVE','2026-10-17 14:53:30','2026-10-17 14:53:30');
/*!40000 ALTER TABLE `suppliers` ENABLE KEYS */;
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
  CONSTRAINT `chk_survey_answers_rating_1_10` CHECK (((`rating_value` is null) or (`rating_value` between 1 and 10))),
  CONSTRAINT `survey_answers_chk_1` CHECK ((`rating_value` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `survey_answers`
--

LOCK TABLES `survey_answers` WRITE;
/*!40000 ALTER TABLE `survey_answers` DISABLE KEYS */;
INSERT INTO `survey_answers` VALUES (1,NULL,NULL,'2026-10-15 02:11:03',4,2,1),(2,NULL,NULL,'2026-10-17 15:38:53',8,3,2),(3,NULL,NULL,'2026-10-17 16:15:47',13,7,6),(4,NULL,NULL,'2026-10-17 16:15:47',16,8,6),(5,'Sản phẩm ok',NULL,'2026-10-17 16:16:50',NULL,5,4);
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
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `survey_options`
--

LOCK TABLES `survey_options` WRITE;
/*!40000 ALTER TABLE `survey_options` DISABLE KEYS */;
INSERT INTO `survey_options` VALUES (1,'1 tiếng',1,1),(2,'2 tiếng',2,1),(3,'3 tiếng',3,1),(4,'Mới chơi',1,2),(5,'1 năm',2,2),(6,'2 năm',3,2),(7,'3 năm',4,2),(8,'yes',1,3),(9,'no',2,3),(10,'mizuno',1,6),(11,'apacs',2,6),(12,'yonex',3,6),(13,'a',1,7),(14,'b',2,7),(15,'c',3,7),(16,'1',1,8),(17,'2',2,8),(18,'3',3,8),(22,'12',1,10),(23,'123',2,10),(24,'1234',3,10),(25,'123',1,11),(26,'12344',2,11),(27,'1234',3,11);
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
  `config` json NOT NULL DEFAULT (_utf8mb4'{}'),
  PRIMARY KEY (`question_id`),
  KEY `idx_survey_questions_survey` (`survey_id`),
  KEY `idx_survey_questions_type` (`question_type`),
  KEY `idx_survey_questions_sort` (`survey_id`,`sort_order`),
  CONSTRAINT `fk_survey_questions_survey` FOREIGN KEY (`survey_id`) REFERENCES `surveys` (`survey_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `chk_survey_questions_sort_order` CHECK ((`sort_order` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `survey_questions`
--

LOCK TABLES `survey_questions` WRITE;
/*!40000 ALTER TABLE `survey_questions` DISABLE KEYS */;
INSERT INTO `survey_questions` VALUES (1,'Bạn chơi cầu lông trong bao lâu','MULTI_CHOICE',0,1,1,'{}'),(2,'Bạn chơi trình độ nào','MULTI_CHOICE',0,1,2,'{}'),(3,'Gay or not','SINGLE_CHOICE',1,1,3,'{}'),(4,'abc','RATING',1,1,4,'{}'),(5,'Nêu cảm nghĩ về sản phẩm','TEXT',0,1,5,'{}'),(6,'Thích hãng nào','MULTI_CHOICE',1,1,6,'{}'),(7,'Thích giày gì','MULTI_CHOICE',0,1,7,'{}'),(8,'Thích vợt gì','SINGLE_CHOICE',0,2,7,'{}'),(10,'test','MULTI_CHOICE',1,1,8,'{\"key\": \"\", \"section\": \"\"}'),(11,'test1','MULTI_CHOICE',1,1,9,'{\"key\": \"\", \"section\": \"\"}');
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
  CONSTRAINT `fk_survey_recipients_customer` FOREIGN KEY (`customer_id`) REFERENCES `accounts` (`account_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_survey_recipients_survey` FOREIGN KEY (`survey_id`) REFERENCES `surveys` (`survey_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `survey_recipients`
--

LOCK TABLES `survey_recipients` WRITE;
/*!40000 ALTER TABLE `survey_recipients` DISABLE KEYS */;
INSERT INTO `survey_recipients` VALUES (1,'COMPLETED','2026-10-15 02:10:45','2026-10-15 02:10:56','2026-10-15 02:11:03',2,2),(2,'SENT','2026-10-17 15:38:47',NULL,NULL,2,3),(3,'SENT','2026-10-17 15:38:47',NULL,NULL,8,3),(5,'COMPLETED','2026-10-17 15:38:47','2026-10-17 15:38:50','2026-10-17 15:38:54',12,3),(6,'SENT','2026-10-17 15:43:39',NULL,NULL,2,4),(7,'SENT','2026-10-17 15:43:39',NULL,NULL,8,4),(9,'OPENED','2026-10-17 15:43:39','2026-10-17 15:43:48',NULL,12,4),(10,'SENT','2026-10-17 15:45:24',NULL,NULL,2,5),(11,'SENT','2026-10-17 15:45:24',NULL,NULL,8,5),(13,'COMPLETED','2026-10-17 15:45:24','2026-10-17 15:45:31','2026-10-17 16:16:50',12,5),(14,'SENT','2026-10-17 16:14:18',NULL,NULL,2,6),(15,'SENT','2026-10-17 16:14:18',NULL,NULL,8,6),(17,'OPENED','2026-10-17 16:14:18','2026-10-17 16:14:25',NULL,12,6),(18,'SENT','2026-10-17 16:15:31',NULL,NULL,2,7),(19,'SENT','2026-10-17 16:15:31',NULL,NULL,8,7),(21,'COMPLETED','2026-10-17 16:15:31','2026-10-17 16:15:38','2026-10-17 16:15:47',12,7),(22,'SENT','2026-11-02 14:09:40',NULL,NULL,2,8),(23,'SENT','2026-11-02 16:38:02',NULL,NULL,2,9),(24,'SENT','2026-11-02 16:38:02',NULL,NULL,8,9),(25,'SENT','2026-11-02 16:38:02',NULL,NULL,12,9),(26,'OPENED','2026-11-02 16:38:02','2026-11-02 16:38:25',NULL,14,9),(27,'SENT','2026-11-02 16:45:09',NULL,NULL,16,9);
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
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `survey_responses`
--

LOCK TABLES `survey_responses` WRITE;
/*!40000 ALTER TABLE `survey_responses` DISABLE KEYS */;
INSERT INTO `survey_responses` VALUES (1,'SUBMITTED','2026-10-15 02:10:56','2026-10-15 02:11:03',1),(2,'SUBMITTED','2026-10-17 15:38:50','2026-10-17 15:38:54',5),(3,'IN_PROGRESS','2026-10-17 15:43:48',NULL,9),(4,'SUBMITTED','2026-10-17 15:45:31','2026-10-17 16:16:50',13),(5,'IN_PROGRESS','2026-10-17 16:14:25',NULL,17),(6,'SUBMITTED','2026-10-17 16:15:38','2026-10-17 16:15:47',21),(7,'IN_PROGRESS','2026-11-02 16:38:25',NULL,26);
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
  `template_key` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `objective` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `audience` json NOT NULL DEFAULT (_utf8mb4'{}'),
  PRIMARY KEY (`survey_id`),
  KEY `idx_surveys_status` (`status`),
  KEY `idx_surveys_created_by` (`created_by`),
  KEY `idx_surveys_start_at` (`start_at`),
  KEY `idx_surveys_end_at` (`end_at`),
  CONSTRAINT `fk_surveys_created_by` FOREIGN KEY (`created_by`) REFERENCES `accounts` (`account_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `surveys`
--

LOCK TABLES `surveys` WRITE;
/*!40000 ALTER TABLE `surveys` DISABLE KEYS */;
INSERT INTO `surveys` VALUES (1,'Thời  gian chơi cầu lông','','2026-10-15 02:01:00','2026-10-16 02:01:00','CLOSED','2026-10-15 02:01:21','2026-10-17 22:35:43',1,NULL,NULL,'{}'),(2,'bạn chơi cầu lông được lâu chưa','','2026-10-15 02:09:00','2026-10-16 02:09:00','CLOSED','2026-10-15 02:09:48','2026-10-17 22:35:43',1,NULL,NULL,'{}'),(3,'bạn có gay ko','gay','2026-10-17 15:36:00','2026-10-18 15:36:00','CLOSED','2026-10-17 15:36:15','2026-10-20 16:41:38',5,NULL,NULL,'{}'),(4,'trình độ chơi','','2026-10-17 15:40:00','2026-10-18 15:40:00','CLOSED','2026-10-17 15:40:21','2026-10-20 16:41:38',5,NULL,NULL,'{}'),(5,'123','123','2026-10-17 15:44:00','2026-10-18 15:44:00','CLOSED','2026-10-17 15:44:52','2026-10-20 16:41:38',5,NULL,NULL,'{}'),(6,'Thích hãng nào?','','2026-10-17 16:11:00','2026-10-18 16:11:00','CLOSED','2026-10-17 16:11:28','2026-10-20 16:41:38',5,NULL,NULL,'{}'),(7,'Thích giày gì','123','2026-10-17 16:14:00','2026-10-18 16:15:00','CLOSED','2026-10-17 16:15:05','2026-10-20 16:41:38',5,NULL,NULL,'{}'),(8,'test','test','2026-11-01 17:00:00','2026-11-03 16:59:59','ACTIVE','2026-11-02 14:05:33','2026-11-02 14:09:40',15,NULL,'SATISFACTION','{\"audience\": \"filter\", \"age_groups\": [\"18_24\"], \"preferences\": [], \"customer_ids\": [], \"playing_levels\": []}'),(9,'test','123','2026-11-01 17:00:00','2026-11-03 16:59:59','ACTIVE','2026-11-02 16:38:01','2026-11-02 16:38:02',15,NULL,'SATISFACTION','{\"audience\": \"all\", \"age_groups\": [], \"preferences\": [], \"customer_ids\": [], \"playing_levels\": []}');
/*!40000 ALTER TABLE `surveys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'crm_db_v2'
--

--
-- Dumping routines for database 'crm_db_v2'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-02 23:53:41

--
-- Raw Python operation
--
-- THIS OPERATION CANNOT BE WRITTEN AS SQL
--
-- Add field address to account
--
ALTER TABLE `accounts` ADD COLUMN `address` varchar(255) NULL;
--
-- Add field date_of_birth to account
--
ALTER TABLE `accounts` ADD COLUMN `date_of_birth` date NULL;
--
-- Add field full_name to account
--
ALTER TABLE `accounts` ADD COLUMN `full_name` varchar(150) DEFAULT '' NOT NULL;
ALTER TABLE `accounts` ALTER COLUMN `full_name` DROP DEFAULT;
--
-- Add field gender to account
--
ALTER TABLE `accounts` ADD COLUMN `gender` varchar(20) NULL;
--
-- Add field phone to account
--
ALTER TABLE `accounts` ADD COLUMN `phone` varchar(20) NULL;
--
-- Add field playing_level to account
--
ALTER TABLE `accounts` ADD COLUMN `playing_level` varchar(30) NULL;
--
-- Raw Python operation
--
-- THIS OPERATION CANNOT BE WRITTEN AS SQL
--
-- Raw Python operation
--
-- THIS OPERATION CANNOT BE WRITTEN AS SQL
--
-- Remove field account from staff
--
ALTER TABLE `staffs` DROP FOREIGN KEY `staffs_account_id_a35f0431_fk_accounts_account_id`;
ALTER TABLE `staffs` DROP COLUMN `account_id`;
--
-- Delete model Admin
--
DROP TABLE `admins` CASCADE;
--
-- Delete model Staff
--
DROP TABLE `staffs` CASCADE;
--
-- Create proxy model Admin
--
-- (no-op)
--
-- Create proxy model Staff
--
-- (no-op)

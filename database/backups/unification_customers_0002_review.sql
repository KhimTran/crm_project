--
-- Alter field customer on customerpreference
--
ALTER TABLE `customer_preferences` DROP FOREIGN KEY `fk_customer_preferences_customer`;
ALTER TABLE `customer_preferences` ADD CONSTRAINT `customer_preferences_customer_id_0996f1ef_fk_accounts_account_id` FOREIGN KEY (`customer_id`) REFERENCES `accounts` (`account_id`);
--
-- Delete model Customer
--
DROP TABLE `customers` CASCADE;
--
-- Create proxy model Customer
--
-- (no-op)

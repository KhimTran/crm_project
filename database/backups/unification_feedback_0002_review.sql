--
-- Alter field customer on feedback
--
ALTER TABLE `feedbacks` DROP FOREIGN KEY `fk_feedbacks_customer`;
ALTER TABLE `feedbacks` ADD CONSTRAINT `feedbacks_customer_id_a064ac85_fk_accounts_account_id` FOREIGN KEY (`customer_id`) REFERENCES `accounts` (`account_id`);
--
-- Alter field handled_by on feedback
--
-- (no-op)

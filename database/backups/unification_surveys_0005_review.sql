--
-- Alter field customer on surveyrecipient
--
ALTER TABLE `survey_recipients` DROP FOREIGN KEY `fk_survey_recipients_customer`;
ALTER TABLE `survey_recipients` ADD CONSTRAINT `survey_recipients_customer_id_ce7961b2_fk_accounts_account_id` FOREIGN KEY (`customer_id`) REFERENCES `accounts` (`account_id`);

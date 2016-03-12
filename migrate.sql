USE `mcpdev`;

RENAME TABLE `members` TO `__members_old`;
RENAME TABLE `doors` TO `__doors_old`;
RENAME TABLE `door_logs` TO `__door_logs_old`;
RENAME TABLE `certifications` TO `__certifications_old`;
RENAME TABLE `merchants` TO `__merchants_old`;
RENAME TABLE `transactions` TO `__transactions_old`;
RENAME TABLE `wallets` TO `__wallets_old`;

CREATE TABLE `members` (
  `id` INT NOT NULL PRIMARY KEY,
  `first_name` VARCHAR(255) NOT NULL,
  `last_name` VARCHAR(255) NOT NULL,
  `nickname` VARCHAR(255) NULL,
  `fob_number` VARCHAR(255) NOT NULL,
  `last_unlock` DATETIME NOT NULL,
  `announce` BIT NOT NULL DEFAULT 0,
  `director` BIT NOT NULL DEFAULT 0
);

CREATE TABLE `member_subscriptions` (
  `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `member_id` INT NOT NULL REFERENCES `members`(`id`),
  `date_from` DATETIME NOT NULL,
  `date_to` DATETIME NOT NULL
);

CREATE TABLE `fallback_fobs` (
  `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `first_name` VARCHAR(255) NOT NULL,
  `last_name` VARCHAR(255) NOT NULL,
  `nickname` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `fob_number` VARCHAR(255) NOT NULL
);

CREATE TABLE `door_cache` (
  `id` INT NOT NULL PRIMARY KEY,
  `name` VARCHAR(255) NOT NULL
);

CREATE TABLE `access_log` (
  `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `member_id` INT NULL REFERENCES `members`(`id`),
  `door_id` INT NOT NULL REFERENCES `door_cache`(`id`),
  `fob_number` VARCHAR(255) NOT NULL,
  `timestamp` DATETIME NOT NULL,
  `access_permitted` BIT NOT NULL DEFAULT 0,
  `uploaded` BIT NOT NULL DEFAULT 0
);

INSERT INTO `fallback_fobs` (`first_name`, `last_name`, `email`, `nickname`, `fob_number`) SELECT `first_name`, `last_name`, `email`, `nickname`, `fob_field` FROM `__members_old`;

DROP TABLE IF EXISTS `learning_queue`;
DROP TABLE IF EXISTS `picture`;
DROP TABLE IF EXISTS `learning_subset`;
DROP TABLE IF EXISTS `learning_set`;
DROP TABLE IF EXISTS `picture_set`;
DROP TABLE IF EXISTS `neural_network`;

CREATE TABLE `neural_network` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` varchar(255) NOT NULL,
  `pretrained_iteration` INT NOT NULL,
  `auto_init` TINYINT(1) NOT NULL DEFAULT '0',
  `keep_saved` TINYINT(1) NOT NULL DEFAULT '0',
  `gpu` TINYINT(1) NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Neural networks';

CREATE TABLE `picture_set` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Picture set';

CREATE TABLE `learning_set` (
  `id` CHAR(16) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Learning set';
INSERT INTO `learning_set` (`id`)
VALUES ("training"), ("validation"), ("testing");

CREATE TABLE `learning_subset` (
  `picture_set_id` INT NOT NULL,
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`picture_set_id`, `id`),
  FOREIGN KEY (`picture_set_id`) REFERENCES `picture_set` (`id`) ON DELETE CASCADE,
  UNIQUE KEY unique_learning_subset_in_picture_set (`picture_set_id`, `name`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Learning subset';

CREATE TABLE `picture` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `picture_set_id` INT NOT NULL,
  `learning_set` CHAR(16) NOT NULL,
  `learning_subset_id` INT NOT NULL,
  `hash` CHAR(32) NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`learning_set`) REFERENCES `learning_set` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`picture_set_id`, `learning_subset_id`) REFERENCES `learning_subset` (`picture_set_id`, `id`) ON DELETE CASCADE,
  UNIQUE KEY unique_picture_in_learning_subset (`picture_set_id`, `learning_set`, `learning_subset_id`, `hash`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Picture';

CREATE TABLE `learning_queue` (
  `neural_network_id` INT NOT NULL,
  `picture_set_id` INT NOT NULL,
  `start_iteration` INT NOT NULL,
  `status` ENUM('waiting','learning') NOT NULL,
  PRIMARY KEY (`neural_network_id`),
  FOREIGN KEY (`picture_set_id`) REFERENCES `picture_set` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Learning queue. Each neural network can have only one record.';

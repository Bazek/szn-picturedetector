DROP TABLE IF EXISTS `model`;
DROP TABLE IF EXISTS `picture`;
DROP TABLE IF EXISTS `picture_set`;
DROP TABLE IF EXISTS `neural_network`;
DROP TABLE IF EXISTS `learning_queue`;

CREATE TABLE `model` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` varchar(127) NOT NULL,
  `description` varchar(255) NOT NULL,
  `model_config_path` varchar(255) NOT NULL,
  `solver_config_path` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Models for neural networks';

CREATE TABLE `neural_network` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `model_id` INT NOT NULL,
  `description` varchar(255) NOT NULL,
  `pretrained_model_path` varchar(255) NOT NULL,
  `mean_file_path` varchar(255) NOT NULL,
  `train_db_path` varchar(255) NOT NULL,
  `validate_db_path` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`model_id`) REFERENCES `model` (`id`) ON DELETE CASCADE,
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Neural networks with configuration';

CREATE TABLE `picture_set` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Picture set';

CREATE TABLE `picture` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `picture_set_id` INT NOT NULL,
  `learning_set` ENUM('training','validation','testing') NOT NULL,
  `learning_subset` INT(3) NOT NULL,
  `hash` CHAR(32) NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`picture_set_id`) REFERENCES `picture_set` (`id`) ON DELETE CASCADE,
  UNIQUE KEY unique_picture_in_learning_subset (`picture_set_id`, `learning_set`, `learning_subset`, `hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Picture';

CREATE TABLE `learning_queue` (
  `neural_network_id` INT NOT NULL,
  `picture_set_id` INT NOT NULL,
  `start_iteration` INT NOT NULL,
  `status` ENUM('waiting','learning') NOT NULL,
  PRIMARY KEY (`neural_network_id`),
  FOREIGN KEY (`picture_set_id`) REFERENCES `picture_set` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Learning queue. Each neural network can have only one record.';
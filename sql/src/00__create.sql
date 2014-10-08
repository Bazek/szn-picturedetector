
DROP TABLE IF EXISTS `solver_config`;
DROP TABLE IF EXISTS `learning_queue`;
DROP TABLE IF EXISTS `picture`;
DROP TABLE IF EXISTS `learning_subset`;
DROP TABLE IF EXISTS `learning_set`;
DROP TABLE IF EXISTS `picture_set`;
DROP TABLE IF EXISTS `neural_network`;
DROP TABLE IF EXISTS `model`;


CREATE TABLE `model` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` varchar(127) NOT NULL,
  `description` varchar(255) NOT NULL,
  `model_config_path` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Models for neural networks';

CREATE TABLE `neural_network` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `model_id` INT NOT NULL,
  `description` varchar(255) NOT NULL,
  `pretrained_model_path` varchar(255) NOT NULL,
  `mean_file` varchar(255) NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`model_id`) REFERENCES `model` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Neural networks with configuration';

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

CREATE TABLE `solver_config` (
  `neural_network_id` INT NOT NULL,
  `net` varchar(255) NOT NULL,
  `stepsize` INT NULL DEFAULT NULL,
  `display` INT NULL DEFAULT NULL,
  `max_iter` INT NULL DEFAULT NULL,
  `test_iter` INT NULL DEFAULT NULL,
  `test_interval` INT NULL DEFAULT NULL,
  `test_compute_loss` tinyint(1) NULL DEFAULT NULL,
  `base_lr` float NULL DEFAULT NULL,
  `lr_policy` varchar(255) NULL DEFAULT NULL,
  `gamma` float NULL DEFAULT NULL,
  `momentum` float NULL DEFAULT NULL,
  `weight_decay` float NULL DEFAULT NULL,
  `power` float NULL DEFAULT NULL,
  `snapshot` INT NULL DEFAULT NULL,
  `snapshot_prefix` varchar(255) NULL DEFAULT NULL,
  `snapshot_diff` tinyint(1) NULL DEFAULT NULL,
  `snapshot_after_train` tinyint(1) NULL DEFAULT NULL,
  `solver_mode` enum('CPU','GPU') NULL DEFAULT NULL,
  `device_id` INT NULL DEFAULT NULL,
  `random_seed` bigint(20) NULL DEFAULT NULL,
  `debug_info` tinyint(1) NULL DEFAULT NULL,
  PRIMARY KEY (`neural_network_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Saved solver settings. From these settings the learning solver file will be generated.';

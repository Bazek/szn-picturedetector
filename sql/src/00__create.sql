
DROP TABLE IF EXISTS `picture`;
DROP TABLE IF EXISTS `picture_set`;
DROP TABLE IF EXISTS `neural_network`;


CREATE TABLE `neural_network` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(256) NOT NULL,
  `configuration` BLOB NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Neural network with configuration';


CREATE TABLE `picture_set` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(256) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Picture set';

CREATE TABLE `picture` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `picture_set_id` INT NOT NULL,
  `learning_set` ENUM('training','validation','testing') NOT NULL,
  `learning_subset` ENUM('true','false') NOT NULL,
  `hash` CHAR(32) NOT NULL,
  PRIMARY KEY (`id`),
  FOREIGN KEY (`picture_set_id`) REFERENCES `picture_set` (`id`) ON DELETE CASCADE,
  UNIQUE KEY unique_picture_in_learning_subset (`picture_set_id`, `learning_set`, `learning_subset`, `hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Picture';


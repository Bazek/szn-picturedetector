CREATE TABLE `neural_network` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(255) NOT NULL,
  `configuration` BLOB NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_czech_ci COMMENT='Neural network with configuration';


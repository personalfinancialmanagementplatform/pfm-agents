/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

DROP TABLE IF EXISTS `alert`;
CREATE TABLE `alert` (
  `alertId` int NOT NULL AUTO_INCREMENT,
  `patientId` int NOT NULL,
  `signId` int NOT NULL,
  `alertType` varchar(50) NOT NULL,
  `alertMessage` varchar(255) NOT NULL,
  `alertTime` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `alertTrigged` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`alertId`),
  KEY `patientId` (`patientId`),
  KEY `signId` (`signId`),
  CONSTRAINT `alert_ibfk_1` FOREIGN KEY (`patientId`) REFERENCES `patient` (`patientId`),
  CONSTRAINT `alert_ibfk_2` FOREIGN KEY (`signId`) REFERENCES `vitalsigns` (`signId`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `patient`;
CREATE TABLE `patient` (
  `patientId` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `age` int NOT NULL,
  `gender` varchar(10) NOT NULL,
  `addr` varchar(255) NOT NULL,
  `idNum` varchar(20) NOT NULL,
  `nhCardNum` varchar(20) NOT NULL,
  `emerName` varchar(100) DEFAULT NULL,
  `emerPhone` varchar(20) DEFAULT NULL,
  `info` varchar(255) DEFAULT NULL,
  `lastUpd` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `lastUpdId` int DEFAULT NULL,
  `isArchived` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`patientId`),
  UNIQUE KEY `idNum` (`idNum`),
  KEY `lastUpdId` (`lastUpdId`),
  CONSTRAINT `patient_ibfk_1` FOREIGN KEY (`lastUpdId`) REFERENCES `user` (`userId`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `tracking`;
CREATE TABLE `tracking` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userId` int NOT NULL,
  `patientId` int NOT NULL,
  `roleId` int DEFAULT NULL,
  `permissionLevel` int DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `userId` (`userId`,`patientId`),
  KEY `patientId` (`patientId`),
  CONSTRAINT `tracking_ibfk_1` FOREIGN KEY (`userId`) REFERENCES `user` (`userId`),
  CONSTRAINT `tracking_ibfk_2` FOREIGN KEY (`patientId`) REFERENCES `patient` (`patientId`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `userId` int NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(100) NOT NULL,
  `role` int NOT NULL COMMENT '0:caregiver, 1:family',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`userId`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `vitalsigns`;
CREATE TABLE `vitalsigns` (
  `signId` int NOT NULL AUTO_INCREMENT,
  `userId` int NOT NULL,
  `patientId` int NOT NULL,
  `vitalTypeId` int NOT NULL COMMENT '對應 VitalType 表中的類型，例如血糖、血壓',
  `value` decimal(10,2) NOT NULL COMMENT '測量值，例如血糖值或收縮壓值',
  `recordDateTime` timestamp NOT NULL COMMENT '測量的完整日期與時間',
  `comment` varchar(255) DEFAULT NULL COMMENT '備註',
  `alertTrigged` tinyint(1) DEFAULT '0' COMMENT '是否觸發警報',
  PRIMARY KEY (`signId`),
  KEY `userId` (`userId`),
  KEY `patientId` (`patientId`),
  KEY `vitalTypeId` (`vitalTypeId`),
  CONSTRAINT `vitalsigns_ibfk_1` FOREIGN KEY (`userId`) REFERENCES `user` (`userId`),
  CONSTRAINT `vitalsigns_ibfk_2` FOREIGN KEY (`patientId`) REFERENCES `patient` (`patientId`),
  CONSTRAINT `vitalsigns_ibfk_3` FOREIGN KEY (`vitalTypeId`) REFERENCES `vitaltype` (`vitalTypeId`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `vitaltype`;
CREATE TABLE `vitaltype` (
  `vitalTypeId` int NOT NULL AUTO_INCREMENT,
  `typeName` varchar(50) NOT NULL,
  `unit` varchar(20) NOT NULL,
  `upperBound` decimal(10,2) NOT NULL,
  `lowerBound` decimal(10,2) NOT NULL,
  PRIMARY KEY (`vitalTypeId`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP VIEW IF EXISTS `healthtrendsview`;
select `vs`.`signId` AS `signId`,`vs`.`patientId` AS `patientId`,`p`.`name` AS `patientName`,`vt`.`typeName` AS `typeName`,`vt`.`unit` AS `unit`,`vs`.`value` AS `value`,`vs`.`recordDateTime` AS `recordDateTime`,`vs`.`alertTrigged` AS `alertTrigged` from ((`health_db`.`vitalsigns` `vs` join `health_db`.`vitaltype` `vt` on((`vs`.`vitalTypeId` = `vt`.`vitalTypeId`))) join `health_db`.`patient` `p` on((`vs`.`patientId` = `p`.`patientId`)));

INSERT INTO `alert` (`alertId`, `patientId`, `signId`, `alertType`, `alertMessage`, `alertTime`, `alertTrigged`) VALUES
(1, 1, 1, 'Blood Sugar High', 'Blood sugar exceeds upper bound', '2025-04-22 17:42:55', 1);
INSERT INTO `alert` (`alertId`, `patientId`, `signId`, `alertType`, `alertMessage`, `alertTime`, `alertTrigged`) VALUES
(2, 2, 4, 'Heart Rate High', 'Heart rate exceeds upper bound', '2025-04-22 17:42:55', 1);


INSERT INTO `patient` (`patientId`, `name`, `age`, `gender`, `addr`, `idNum`, `nhCardNum`, `emerName`, `emerPhone`, `info`, `lastUpd`, `lastUpdId`, `isArchived`) VALUES
(1, '王小明', 82, 'male', '台北市信義區A路1號', 'A123456789', 'NH00001', '王大明', '0911222333', '糖尿病患者', '2025-04-22 17:42:55', 1, 0);
INSERT INTO `patient` (`patientId`, `name`, `age`, `gender`, `addr`, `idNum`, `nhCardNum`, `emerName`, `emerPhone`, `info`, `lastUpd`, `lastUpdId`, `isArchived`) VALUES
(2, '陳美麗', 76, 'female', '新北市板橋區B路2號', 'B234567890', 'NH00002', '陳玉珍', '0922333444', '高血壓控制中', '2025-04-22 17:42:55', 1, 0);


INSERT INTO `tracking` (`id`, `userId`, `patientId`, `roleId`, `permissionLevel`, `created_at`) VALUES
(1, 1, 1, NULL, 3, '2025-04-22 17:42:55');
INSERT INTO `tracking` (`id`, `userId`, `patientId`, `roleId`, `permissionLevel`, `created_at`) VALUES
(2, 1, 2, NULL, 3, '2025-04-22 17:42:55');


INSERT INTO `user` (`userId`, `username`, `password`, `email`, `role`, `created_at`) VALUES
(1, 'caregiver_amy', 'hashed_password_1', 'amy@example.com', 0, '2025-04-22 17:42:55');
INSERT INTO `user` (`userId`, `username`, `password`, `email`, `role`, `created_at`) VALUES
(2, 'family_bob', 'hashed_password_2', 'bob@example.com', 1, '2025-04-22 17:42:55');


INSERT INTO `vitalsigns` (`signId`, `userId`, `patientId`, `vitalTypeId`, `value`, `recordDateTime`, `comment`, `alertTrigged`) VALUES
(1, 1, 1, 1, '160.00', '2025-04-21 09:00:00', '早餐後測量', 1);
INSERT INTO `vitalsigns` (`signId`, `userId`, `patientId`, `vitalTypeId`, `value`, `recordDateTime`, `comment`, `alertTrigged`) VALUES
(2, 1, 1, 2, '140.00', '2025-04-21 09:00:00', '早餐後測量', 1);
INSERT INTO `vitalsigns` (`signId`, `userId`, `patientId`, `vitalTypeId`, `value`, `recordDateTime`, `comment`, `alertTrigged`) VALUES
(3, 1, 2, 1, '120.00', '2025-04-22 18:00:00', '晚餐後測量', 0);
INSERT INTO `vitalsigns` (`signId`, `userId`, `patientId`, `vitalTypeId`, `value`, `recordDateTime`, `comment`, `alertTrigged`) VALUES
(4, 1, 2, 4, '100.00', '2025-04-22 18:00:00', '運動後測量', 1);

INSERT INTO `vitaltype` (`vitalTypeId`, `typeName`, `unit`, `upperBound`, `lowerBound`) VALUES
(1, 'bloodSugar', 'mg/dL', '140.00', '70.00');
INSERT INTO `vitaltype` (`vitalTypeId`, `typeName`, `unit`, `upperBound`, `lowerBound`) VALUES
(2, 'systolic', 'mmHg', '130.00', '90.00');
INSERT INTO `vitaltype` (`vitalTypeId`, `typeName`, `unit`, `upperBound`, `lowerBound`) VALUES
(3, 'diastolic', 'mmHg', '80.00', '60.00');
INSERT INTO `vitaltype` (`vitalTypeId`, `typeName`, `unit`, `upperBound`, `lowerBound`) VALUES
(4, 'heartRate', 'bpm', '100.00', '60.00'),
(5, 'bloodO2', '%', '100.00', '95.00'),
(6, 'weight', 'kg', '100.00', '40.00');



/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
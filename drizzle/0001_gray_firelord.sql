CREATE TABLE `api_keys` (
	`id` varchar(36) NOT NULL,
	`userId` int NOT NULL,
	`name` varchar(255) NOT NULL,
	`keyHash` varchar(255) NOT NULL,
	`isActive` int NOT NULL DEFAULT 1,
	`rateLimit` int DEFAULT 100,
	`rateLimitWindow` int DEFAULT 60,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	`lastUsedAt` timestamp,
	CONSTRAINT `api_keys_id` PRIMARY KEY(`id`),
	CONSTRAINT `api_keys_keyHash_unique` UNIQUE(`keyHash`)
);
--> statement-breakpoint
CREATE TABLE `email_logs` (
	`id` varchar(36) NOT NULL,
	`emailId` varchar(36) NOT NULL,
	`providerId` varchar(36),
	`status` varchar(50) NOT NULL,
	`statusCode` int,
	`message` text,
	`errorDetails` text,
	`processingTime` int,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `email_logs_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `email_templates` (
	`id` varchar(36) NOT NULL,
	`userId` int NOT NULL,
	`name` varchar(255) NOT NULL,
	`subject` varchar(500) NOT NULL,
	`htmlContent` text,
	`textContent` text,
	`variables` text,
	`isActive` int NOT NULL DEFAULT 1,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `email_templates_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `emails` (
	`id` varchar(36) NOT NULL,
	`apiKeyId` varchar(36),
	`templateId` varchar(36),
	`providerId` varchar(36),
	`to` varchar(320) NOT NULL,
	`cc` text,
	`bcc` text,
	`subject` varchar(500) NOT NULL,
	`htmlContent` text,
	`textContent` text,
	`variables` text,
	`status` varchar(50) NOT NULL DEFAULT 'pending',
	`priority` varchar(20) DEFAULT 'normal',
	`attempts` int DEFAULT 0,
	`maxAttempts` int DEFAULT 5,
	`nextRetryAt` timestamp,
	`sentAt` timestamp,
	`failureReason` text,
	`webhookUrl` varchar(2048),
	`externalId` varchar(255),
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `emails_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `metrics` (
	`id` varchar(36) NOT NULL,
	`userId` int,
	`date` varchar(10) NOT NULL,
	`hour` int,
	`totalSent` int DEFAULT 0,
	`totalSuccessful` int DEFAULT 0,
	`totalFailed` int DEFAULT 0,
	`averageLatency` int DEFAULT 0,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `metrics_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `smtp_providers` (
	`id` varchar(36) NOT NULL,
	`userId` int NOT NULL,
	`name` varchar(255) NOT NULL,
	`type` varchar(50) NOT NULL,
	`isActive` int NOT NULL DEFAULT 1,
	`priority` int DEFAULT 0,
	`config` text NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `smtp_providers_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `webhooks` (
	`id` varchar(36) NOT NULL,
	`userId` int NOT NULL,
	`url` varchar(2048) NOT NULL,
	`events` text,
	`isActive` int NOT NULL DEFAULT 1,
	`secret` varchar(255) NOT NULL,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `webhooks_id` PRIMARY KEY(`id`)
);

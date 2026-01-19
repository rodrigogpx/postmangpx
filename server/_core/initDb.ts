import { drizzle } from "drizzle-orm/mysql2";
import { sql } from "drizzle-orm";

export async function initializeDatabase() {
  if (!process.env.DATABASE_URL) {
    console.warn("[Database] DATABASE_URL not set, skipping initialization");
    return;
  }

  try {
    console.log("[Database] Initializing database...");
    const db = drizzle(process.env.DATABASE_URL);

    // Criar tabelas se não existirem
    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        openId VARCHAR(64) NOT NULL UNIQUE,
        name TEXT,
        email VARCHAR(320),
        loginMethod VARCHAR(64),
        role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
        createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        lastSignedIn TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS api_keys (
        id VARCHAR(36) PRIMARY KEY,
        userId INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        keyHash VARCHAR(255) NOT NULL UNIQUE,
        isActive INT NOT NULL DEFAULT 1,
        rateLimit INT DEFAULT 100,
        rateLimitWindow INT DEFAULT 60,
        createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        lastUsedAt TIMESTAMP NULL
      )
    `);

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS smtp_providers (
        id VARCHAR(36) PRIMARY KEY,
        userId INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        type VARCHAR(50) NOT NULL,
        isActive INT NOT NULL DEFAULT 1,
        priority INT DEFAULT 0,
        config TEXT NOT NULL,
        createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      )
    `);

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS email_templates (
        id VARCHAR(36) PRIMARY KEY,
        userId INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        subject VARCHAR(500) NOT NULL,
        htmlContent TEXT,
        textContent TEXT,
        variables TEXT,
        isActive INT NOT NULL DEFAULT 1,
        createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      )
    `);

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS emails (
        id VARCHAR(36) PRIMARY KEY,
        apiKeyId VARCHAR(36),
        templateId VARCHAR(36),
        providerId VARCHAR(36),
        \`to\` VARCHAR(320) NOT NULL,
        cc TEXT,
        bcc TEXT,
        subject VARCHAR(500) NOT NULL,
        htmlContent TEXT,
        textContent TEXT,
        variables TEXT,
        status VARCHAR(50) NOT NULL DEFAULT 'pending',
        priority VARCHAR(20) DEFAULT 'normal',
        attempts INT DEFAULT 0,
        maxAttempts INT DEFAULT 5,
        nextRetryAt TIMESTAMP NULL,
        sentAt TIMESTAMP NULL,
        failureReason TEXT,
        webhookUrl VARCHAR(2048),
        externalId VARCHAR(255),
        createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      )
    `);

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS email_logs (
        id VARCHAR(36) PRIMARY KEY,
        emailId VARCHAR(36) NOT NULL,
        providerId VARCHAR(36),
        status VARCHAR(50) NOT NULL,
        statusCode INT,
        message TEXT,
        errorDetails TEXT,
        processingTime INT,
        createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS webhooks (
        id VARCHAR(36) PRIMARY KEY,
        userId INT NOT NULL,
        url VARCHAR(2048) NOT NULL,
        events TEXT,
        isActive INT NOT NULL DEFAULT 1,
        secret VARCHAR(255) NOT NULL,
        createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
      )
    `);

    await db.execute(sql`
      CREATE TABLE IF NOT EXISTS metrics (
        id VARCHAR(36) PRIMARY KEY,
        userId INT,
        date VARCHAR(10) NOT NULL,
        hour INT,
        totalSent INT DEFAULT 0,
        totalSuccessful INT DEFAULT 0,
        totalFailed INT DEFAULT 0,
        averageLatency INT DEFAULT 0,
        createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);

    console.log("[Database] Database initialized successfully");
  } catch (error) {
    console.error("[Database] Failed to initialize database:", error);
    throw error;
  }
}

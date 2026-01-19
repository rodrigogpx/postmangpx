-- ============================================
-- PostmanGPX - Database Initialization Script
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- Users Table (for dashboard authentication)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    "openId" VARCHAR(64) NOT NULL UNIQUE,
    name TEXT,
    email VARCHAR(320),
    "loginMethod" VARCHAR(64),
    role VARCHAR(20) DEFAULT 'user' NOT NULL,
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "lastSignedIn" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ============================================
-- API Keys Table
-- ============================================
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "userId" INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    "isActive" BOOLEAN DEFAULT true NOT NULL,
    "rateLimit" INTEGER DEFAULT 100,
    "rateLimitWindow" INTEGER DEFAULT 60,
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "lastUsedAt" TIMESTAMP,
    INDEX idx_user_id ("userId"),
    INDEX idx_active ("isActive")
);

-- ============================================
-- SMTP Providers Table
-- ============================================
CREATE TABLE IF NOT EXISTS smtp_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "userId" INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    "isActive" BOOLEAN DEFAULT true NOT NULL,
    priority INTEGER DEFAULT 0,
    config JSONB NOT NULL,
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_user_id ("userId"),
    INDEX idx_active ("isActive"),
    INDEX idx_priority (priority DESC)
);

-- ============================================
-- Email Templates Table
-- ============================================
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "userId" INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    "htmlContent" TEXT,
    "textContent" TEXT,
    variables JSONB DEFAULT '[]'::jsonb,
    "isActive" BOOLEAN DEFAULT true NOT NULL,
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_user_id ("userId"),
    INDEX idx_active ("isActive")
);

-- ============================================
-- Emails Table
-- ============================================
CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "apiKeyId" UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    "templateId" UUID REFERENCES email_templates(id) ON DELETE SET NULL,
    "providerId" UUID REFERENCES smtp_providers(id) ON DELETE SET NULL,
    "to" VARCHAR(320) NOT NULL,
    "cc" TEXT,
    "bcc" TEXT,
    subject VARCHAR(500) NOT NULL,
    "htmlContent" TEXT,
    "textContent" TEXT,
    variables JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    "attempts" INTEGER DEFAULT 0,
    "maxAttempts" INTEGER DEFAULT 5,
    "nextRetryAt" TIMESTAMP,
    "sentAt" TIMESTAMP,
    "failureReason" TEXT,
    "webhookUrl" VARCHAR(2048),
    "webhookSignature" VARCHAR(255),
    "externalId" VARCHAR(255),
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_status (status),
    INDEX idx_to ("to"),
    INDEX idx_created ("createdAt" DESC),
    INDEX idx_api_key ("apiKeyId"),
    INDEX idx_template ("templateId"),
    INDEX idx_provider ("providerId"),
    INDEX idx_retry ("nextRetryAt")
);

-- ============================================
-- Email Logs Table
-- ============================================
CREATE TABLE IF NOT EXISTS email_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "emailId" UUID NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
    "providerId" UUID REFERENCES smtp_providers(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL,
    "statusCode" INTEGER,
    message TEXT,
    "errorDetails" JSONB,
    "processingTime" INTEGER,
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_email_id ("emailId"),
    INDEX idx_status (status),
    INDEX idx_created ("createdAt" DESC)
);

-- ============================================
-- Webhooks Table
-- ============================================
CREATE TABLE IF NOT EXISTS webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "userId" INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(2048) NOT NULL,
    events TEXT[] DEFAULT ARRAY['email.sent', 'email.failed', 'email.opened', 'email.clicked'],
    "isActive" BOOLEAN DEFAULT true NOT NULL,
    secret VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    "updatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_user_id ("userId"),
    INDEX idx_active ("isActive")
);

-- ============================================
-- Webhook Logs Table
-- ============================================
CREATE TABLE IF NOT EXISTS webhook_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "webhookId" UUID NOT NULL REFERENCES webhooks(id) ON DELETE CASCADE,
    event VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    "statusCode" INTEGER,
    response TEXT,
    "attempts" INTEGER DEFAULT 1,
    "nextRetryAt" TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_webhook_id ("webhookId"),
    INDEX idx_status (status),
    INDEX idx_created ("createdAt" DESC)
);

-- ============================================
-- Metrics Table (for aggregated statistics)
-- ============================================
CREATE TABLE IF NOT EXISTS metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    "userId" INTEGER REFERENCES users(id) ON DELETE CASCADE,
    "providerId" UUID REFERENCES smtp_providers(id) ON DELETE SET NULL,
    date DATE NOT NULL,
    hour INTEGER,
    "totalSent" INTEGER DEFAULT 0,
    "totalSuccessful" INTEGER DEFAULT 0,
    "totalFailed" INTEGER DEFAULT 0,
    "totalBounced" INTEGER DEFAULT 0,
    "averageLatency" FLOAT DEFAULT 0,
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_user_date ("userId", date),
    INDEX idx_provider_date ("providerId", date),
    INDEX idx_date (date)
);

-- ============================================
-- Create Indexes for Performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_emails_status_created ON emails(status, "createdAt" DESC);
CREATE INDEX IF NOT EXISTS idx_emails_api_key_created ON emails("apiKeyId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS idx_email_logs_email_created ON email_logs("emailId", "createdAt" DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_logs_webhook_created ON webhook_logs("webhookId", "createdAt" DESC);

-- ============================================
-- Create default admin user (optional)
-- ============================================
-- Uncomment and modify as needed
-- INSERT INTO users ("openId", name, email, "loginMethod", role)
-- VALUES ('admin-001', 'Admin User', 'admin@postmangpx.local', 'local', 'admin')
-- ON CONFLICT ("openId") DO NOTHING;

-- ============================================
-- Grant permissions
-- ============================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postmangpx;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postmangpx;

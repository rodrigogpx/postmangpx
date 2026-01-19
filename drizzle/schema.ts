import { int, mysqlEnum, mysqlTable, text, timestamp, varchar } from "drizzle-orm/mysql-core";

/**
 * Users table - Autenticação do dashboard
 */
export const users = mysqlTable("users", {
  id: int("id").autoincrement().primaryKey(),
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * API Keys - Autenticação para clientes externos
 */
export const apiKeys = mysqlTable("api_keys", {
  id: varchar("id", { length: 36 }).primaryKey(),
  userId: int("userId").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
  keyHash: varchar("keyHash", { length: 255 }).notNull().unique(),
  isActive: int("isActive").default(1).notNull(),
  rateLimit: int("rateLimit").default(100),
  rateLimitWindow: int("rateLimitWindow").default(60),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastUsedAt: timestamp("lastUsedAt"),
});

export type ApiKey = typeof apiKeys.$inferSelect;
export type InsertApiKey = typeof apiKeys.$inferInsert;

/**
 * SMTP Providers - Configurações de provedores de e-mail
 */
export const smtpProviders = mysqlTable("smtp_providers", {
  id: varchar("id", { length: 36 }).primaryKey(),
  userId: int("userId").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
  type: varchar("type", { length: 50 }).notNull(),
  isActive: int("isActive").default(1).notNull(),
  priority: int("priority").default(0),
  config: text("config").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type SmtpProvider = typeof smtpProviders.$inferSelect;
export type InsertSmtpProvider = typeof smtpProviders.$inferInsert;

/**
 * Email Templates - Templates de e-mail
 */
export const emailTemplates = mysqlTable("email_templates", {
  id: varchar("id", { length: 36 }).primaryKey(),
  userId: int("userId").notNull(),
  name: varchar("name", { length: 255 }).notNull(),
  subject: varchar("subject", { length: 500 }).notNull(),
  htmlContent: text("htmlContent"),
  textContent: text("textContent"),
  variables: text("variables"),
  isActive: int("isActive").default(1).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type EmailTemplate = typeof emailTemplates.$inferSelect;
export type InsertEmailTemplate = typeof emailTemplates.$inferInsert;

/**
 * Emails - Histórico de e-mails enviados
 */
export const emails = mysqlTable("emails", {
  id: varchar("id", { length: 36 }).primaryKey(),
  apiKeyId: varchar("apiKeyId", { length: 36 }),
  templateId: varchar("templateId", { length: 36 }),
  providerId: varchar("providerId", { length: 36 }),
  to: varchar("to", { length: 320 }).notNull(),
  cc: text("cc"),
  bcc: text("bcc"),
  subject: varchar("subject", { length: 500 }).notNull(),
  htmlContent: text("htmlContent"),
  textContent: text("textContent"),
  variables: text("variables"),
  status: varchar("status", { length: 50 }).default("pending").notNull(),
  priority: varchar("priority", { length: 20 }).default("normal"),
  attempts: int("attempts").default(0),
  maxAttempts: int("maxAttempts").default(5),
  nextRetryAt: timestamp("nextRetryAt"),
  sentAt: timestamp("sentAt"),
  failureReason: text("failureReason"),
  webhookUrl: varchar("webhookUrl", { length: 2048 }),
  externalId: varchar("externalId", { length: 255 }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Email = typeof emails.$inferSelect;
export type InsertEmail = typeof emails.$inferInsert;

/**
 * Email Logs - Logs detalhados de cada tentativa
 */
export const emailLogs = mysqlTable("email_logs", {
  id: varchar("id", { length: 36 }).primaryKey(),
  emailId: varchar("emailId", { length: 36 }).notNull(),
  providerId: varchar("providerId", { length: 36 }),
  status: varchar("status", { length: 50 }).notNull(),
  statusCode: int("statusCode"),
  message: text("message"),
  errorDetails: text("errorDetails"),
  processingTime: int("processingTime"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type EmailLog = typeof emailLogs.$inferSelect;
export type InsertEmailLog = typeof emailLogs.$inferInsert;

/**
 * Webhooks - Configurações de webhooks
 */
export const webhooks = mysqlTable("webhooks", {
  id: varchar("id", { length: 36 }).primaryKey(),
  userId: int("userId").notNull(),
  url: varchar("url", { length: 2048 }).notNull(),
  events: text("events"),
  isActive: int("isActive").default(1).notNull(),
  secret: varchar("secret", { length: 255 }).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Webhook = typeof webhooks.$inferSelect;
export type InsertWebhook = typeof webhooks.$inferInsert;

/**
 * Metrics - Agregações de métricas para dashboard
 */
export const metrics = mysqlTable("metrics", {
  id: varchar("id", { length: 36 }).primaryKey(),
  userId: int("userId"),
  date: varchar("date", { length: 10 }).notNull(),
  hour: int("hour"),
  totalSent: int("totalSent").default(0),
  totalSuccessful: int("totalSuccessful").default(0),
  totalFailed: int("totalFailed").default(0),
  averageLatency: int("averageLatency").default(0),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type Metric = typeof metrics.$inferSelect;
export type InsertMetric = typeof metrics.$inferInsert;

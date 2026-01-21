import { integer, sqliteTable, text } from "drizzle-orm/sqlite-core";

/**
 * Users table - Autenticação do dashboard
 */
export const users = sqliteTable("users", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  openId: text("openId").notNull().unique(),
  name: text("name"),
  email: text("email"),
  loginMethod: text("loginMethod"),
  role: text("role").$type<"user" | "admin">().default("user").notNull(),
  createdAt: integer("createdAt", { mode: "timestamp" }).defaultNow().notNull(),
  updatedAt: integer("updatedAt", { mode: "timestamp" }).defaultNow().notNull(),
  lastSignedIn: integer("lastSignedIn", { mode: "timestamp" }).defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * API Keys - Autenticação para clientes externos
 */
export const apiKeys = sqliteTable("api_keys", {
  id: text("id").primaryKey(),
  userId: integer("userId").notNull(),
  name: text("name").notNull(),
  keyHash: text("keyHash").notNull().unique(),
  isActive: integer("isActive").default(1).notNull(),
  rateLimit: integer("rateLimit").default(100),
  rateLimitWindow: integer("rateLimitWindow").default(60),
  createdAt: integer("createdAt", { mode: "timestamp" }).defaultNow().notNull(),
  updatedAt: integer("updatedAt", { mode: "timestamp" }).defaultNow().notNull(),
  lastUsedAt: integer("lastUsedAt", { mode: "timestamp" }),
});

export type ApiKey = typeof apiKeys.$inferSelect;
export type InsertApiKey = typeof apiKeys.$inferInsert;

/**
 * SMTP Providers - Configurações de provedores de e-mail
 */
export const smtpProviders = sqliteTable("smtp_providers", {
  id: text("id").primaryKey(),
  userId: integer("userId").notNull(),
  name: text("name").notNull(),
  type: text("type").notNull(),
  isActive: integer("isActive").default(1).notNull(),
  priority: integer("priority").default(0),
  config: text("config").notNull(),
  createdAt: integer("createdAt", { mode: "timestamp" }).defaultNow().notNull(),
  updatedAt: integer("updatedAt", { mode: "timestamp" }).defaultNow().notNull(),
});

export type SmtpProvider = typeof smtpProviders.$inferSelect;
export type InsertSmtpProvider = typeof smtpProviders.$inferInsert;

/**
 * Email Templates - Templates de e-mail
 */
export const emailTemplates = sqliteTable("email_templates", {
  id: text("id").primaryKey(),
  userId: integer("userId").notNull(),
  name: text("name").notNull(),
  subject: text("subject").notNull(),
  htmlContent: text("htmlContent"),
  textContent: text("textContent"),
  variables: text("variables"),
  isActive: integer("isActive").default(1).notNull(),
  createdAt: integer("createdAt", { mode: "timestamp" }).defaultNow().notNull(),
  updatedAt: integer("updatedAt", { mode: "timestamp" }).defaultNow().notNull(),
});

export type EmailTemplate = typeof emailTemplates.$inferSelect;
export type InsertEmailTemplate = typeof emailTemplates.$inferInsert;

/**
 * Emails - Histórico de e-mails enviados
 */
export const emails = sqliteTable("emails", {
  id: text("id").primaryKey(),
  apiKeyId: text("apiKeyId"),
  templateId: text("templateId"),
  providerId: text("providerId"),
  to: text("to").notNull(),
  cc: text("cc"),
  bcc: text("bcc"),
  subject: text("subject").notNull(),
  htmlContent: text("htmlContent"),
  textContent: text("textContent"),
  variables: text("variables"),
  status: text("status").default("pending").notNull(),
  priority: text("priority").default("normal"),
  attempts: integer("attempts").default(0),
  maxAttempts: integer("maxAttempts").default(5),
  nextRetryAt: integer("nextRetryAt", { mode: "timestamp" }),
  sentAt: integer("sentAt", { mode: "timestamp" }),
  failureReason: text("failureReason"),
  webhookUrl: text("webhookUrl"),
  externalId: text("externalId"),
  createdAt: integer("createdAt", { mode: "timestamp" }).defaultNow().notNull(),
  updatedAt: integer("updatedAt", { mode: "timestamp" }).defaultNow().notNull(),
});

export type Email = typeof emails.$inferSelect;
export type InsertEmail = typeof emails.$inferInsert;

/**
 * Email Logs - Logs detalhados de cada tentativa
 */
export const emailLogs = sqliteTable("email_logs", {
  id: text("id").primaryKey(),
  emailId: text("emailId").notNull(),
  providerId: text("providerId"),
  status: text("status").notNull(),
  statusCode: integer("statusCode"),
  message: text("message"),
  errorDetails: text("errorDetails"),
  processingTime: integer("processingTime"),
  createdAt: integer("createdAt", { mode: "timestamp" }).defaultNow().notNull(),
});

export type EmailLog = typeof emailLogs.$inferSelect;
export type InsertEmailLog = typeof emailLogs.$inferInsert;

/**
 * Webhooks - Configurações de webhooks
 */
export const webhooks = sqliteTable("webhooks", {
  id: text("id").primaryKey(),
  userId: integer("userId").notNull(),
  url: text("url").notNull(),
  events: text("events"),
  isActive: integer("isActive").default(1).notNull(),
  secret: text("secret").notNull(),
  createdAt: integer("createdAt", { mode: "timestamp" }).defaultNow().notNull(),
  updatedAt: integer("updatedAt", { mode: "timestamp" }).defaultNow().notNull(),
});

export type Webhook = typeof webhooks.$inferSelect;
export type InsertWebhook = typeof webhooks.$inferInsert;

/**
 * Metrics - Agregações de métricas para dashboard
 */
export const metrics = sqliteTable("metrics", {
  id: text("id").primaryKey(),
  userId: integer("userId"),
  date: text("date").notNull(),
  hour: integer("hour"),
  totalSent: integer("totalSent").default(0),
  totalSuccessful: integer("totalSuccessful").default(0),
  totalFailed: integer("totalFailed").default(0),
  averageLatency: integer("averageLatency").default(0),
  createdAt: integer("createdAt", { mode: "timestamp" }).defaultNow().notNull(),
});

export type Metric = typeof metrics.$inferSelect;
export type InsertMetric = typeof metrics.$inferInsert;


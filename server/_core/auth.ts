import { TRPCError } from "@trpc/server";
import { eq } from "drizzle-orm";
import { nanoid } from "nanoid";
import { z } from "zod";
import { apiKeys } from "../../drizzle/schema";
import { getDb } from "../db";

// Schema para validação de API Key
// Formato: pmgpx_[live|test]_[32 caracteres alfanuméricos]
export const apiKeySchema = z.string().regex(/^pmgpx_(live|test)_[a-zA-Z0-9]{32}$/, {
  message: "Invalid API key format. Expected: pmgpx_live_xxx or pmgpx_test_xxx",
});

// Schema para validação de input de e-mail
export const sendEmailSchema = z.object({
  to: z.string().email("Invalid email address"),
  cc: z.array(z.string().email()).optional(),
  bcc: z.array(z.string().email()).optional(),
  subject: z.string().min(1, "Subject is required").max(500),
  template: z.string().uuid().optional(),
  html: z.string().optional(),
  text: z.string().optional(),
  variables: z.record(z.any()).optional(),
  webhookUrl: z.string().url().optional(),
  externalId: z.string().max(255).optional(),
  priority: z.enum(["low", "normal", "high"]).default("normal"),
}).refine(
  (data) => data.template || data.html || data.text,
  {
    message: "Either template, html, or text content is required",
    path: ["content"],
  }
);

export const getEmailStatusSchema = z.object({
  id: z.string().uuid("Invalid email ID"),
});

export const listEmailsSchema = z.object({
  status: z.enum(["pending", "sent", "failed"]).optional(),
  to: z.string().email().optional(),
  limit: z.number().min(1).max(100).default(20),
  offset: z.number().min(0).default(0),
});

// Função para verificar API Key
export async function verifyApiKey(apiKey: string) {
  if (!apiKey) {
    throw new TRPCError({
      code: "UNAUTHORIZED",
      message: "API key is required",
    });
  }

  // Validar formato
  try {
    apiKeySchema.parse(apiKey);
  } catch (error) {
    throw new TRPCError({
      code: "UNAUTHORIZED",
      message: "Invalid API key format",
    });
  }

  const db = await getDb();
  if (!db) {
    throw new TRPCError({
      code: "INTERNAL_SERVER_ERROR",
      message: "Database unavailable",
    });
  }

  // Hash da API key (simulação - em produção usar bcrypt)
  const keyHash = `hash_${apiKey}`;

  const keyRecord = await db
    .select()
    .from(apiKeys)
    .where(eq(apiKeys.keyHash, keyHash))
    .limit(1);

  if (!keyRecord.length) {
    throw new TRPCError({
      code: "UNAUTHORIZED",
      message: "Invalid API key",
    });
  }

  const apiKeyData = keyRecord[0];

  if (!apiKeyData.isActive) {
    throw new TRPCError({
      code: "UNAUTHORIZED",
      message: "API key is disabled",
    });
  }

  // Atualizar lastUsedAt
  await db
    .update(apiKeys)
    .set({ lastUsedAt: new Date() })
    .where(eq(apiKeys.id, apiKeyData.id));

  return apiKeyData;
}

// Função para gerar API Key
export function generateApiKey(environment: 'live' | 'test' = 'live'): string {
  return `pmgpx_${environment}_${nanoid(32)}`;
}

// Middleware para rate limiting (simples)
export async function checkRateLimit(apiKeyId: string, limit: number, window: number): Promise<void> {
  // Em produção, usar Redis para rate limiting
  // Por enquanto, apenas log para demonstração
  console.log(`[RateLimit] Checking API key ${apiKeyId} with limit ${limit}/${window}s`);
  
  // TODO: Implementar rate limiting real com Redis
  // const key = `rate_limit:${apiKeyId}`;
  // const current = await redis.incr(key);
  // if (current === 1) {
  //   await redis.expire(key, window);
  // }
  // if (current > limit) {
  //   throw new TRPCError({
  //     code: "TOO_MANY_REQUESTS",
  //     message: "Rate limit exceeded",
  //   });
  // }
}

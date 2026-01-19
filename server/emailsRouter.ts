import { TRPCError } from "@trpc/server";
import { eq, desc, and, like } from "drizzle-orm";
import { nanoid } from "nanoid";
import { z } from "zod";
import { emails, emailTemplates } from "../drizzle/schema";
import { getDb } from "./db";
import { publicProcedure, router } from "./_core/trpc";
import { 
  verifyApiKey, 
  sendEmailSchema, 
  getEmailStatusSchema, 
  listEmailsSchema,
  checkRateLimit 
} from "./_core/auth";

export const emailsRouter = router({
  send: publicProcedure
    .input(sendEmailSchema)
    .mutation(async ({ input, ctx }) => {
      // Verificar API Key
      const apiKey = ctx.req.headers.authorization?.replace('Bearer ', '');
      const apiKeyData = await verifyApiKey(apiKey);

      // Rate limiting
      await checkRateLimit(apiKeyData.id, apiKeyData.rateLimit, apiKeyData.rateLimitWindow);

      const db = await getDb();
      if (!db) {
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message: "Database unavailable",
        });
      }

      // Se template fornecido, buscar conteúdo
      let htmlContent = input.html;
      let textContent = input.text;
      let subject = input.subject;

      if (input.template) {
        const template = await db
          .select()
          .from(emailTemplates)
          .where(eq(emailTemplates.id, input.template))
          .limit(1);

        if (!template.length) {
          throw new TRPCError({
            code: "NOT_FOUND",
            message: "Template not found",
          });
        }

        const templateData = template[0];
        
        // Substituir variáveis (simples)
        const variables = input.variables || {};
        
        subject = templateData.subject.replace(/\{\{(\w+)\}\}/g, (match, key) => 
          variables[key] || match
        );
        
        if (templateData.htmlContent) {
          htmlContent = templateData.htmlContent.replace(/\{\{(\w+)\}\}/g, (match, key) => 
            variables[key] || match
          );
        }
        
        if (templateData.textContent) {
          textContent = templateData.textContent.replace(/\{\{(\w+)\}\}/g, (match, key) => 
            variables[key] || match
          );
        }
      }

      // Criar registro de e-mail
      const emailId = nanoid();
      const emailData = {
        id: emailId,
        apiKeyId: apiKeyData.id,
        templateId: input.template || null,
        providerId: null, // Será definido pelo worker
        to: input.to,
        cc: input.cc?.join(',') || null,
        bcc: input.bcc?.join(',') || null,
        subject,
        htmlContent: htmlContent || null,
        textContent: textContent || null,
        variables: JSON.stringify(input.variables || {}),
        status: "pending",
        priority: input.priority,
        attempts: 0,
        maxAttempts: 5,
        webhookUrl: input.webhookUrl || null,
        externalId: input.externalId || null,
      };

      try {
        await db.insert(emails).values(emailData);
      } catch (error) {
        console.error("[Emails] Failed to insert email:", error);
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message: "Failed to queue email",
        });
      }

      // Enfileirar job no Bull Queue
      const { addEmailJob } = await import('./_core/queue');
      await addEmailJob({
        emailId,
        to: input.to,
        cc: input.cc,
        bcc: input.bcc,
        subject,
        html: htmlContent,
        text: textContent,
        variables: input.variables,
        webhookUrl: input.webhookUrl,
        externalId: input.externalId,
        priority: input.priority,
        attempts: 0,
        maxAttempts: 5,
      });

      return {
        id: emailId,
        status: "pending",
        createdAt: new Date().toISOString(),
      };
    }),

  getStatus: publicProcedure
    .input(getEmailStatusSchema)
    .query(async ({ input, ctx }) => {
      // Verificar API Key
      const apiKey = ctx.req.headers.authorization?.replace('Bearer ', '');
      const apiKeyData = await verifyApiKey(apiKey);

      const db = await getDb();
      if (!db) {
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message: "Database unavailable",
        });
      }

      const email = await db
        .select({
          id: emails.id,
          status: emails.status,
          attempts: emails.attempts,
          sentAt: emails.sentAt,
          failureReason: emails.failureReason,
          createdAt: emails.createdAt,
        })
        .from(emails)
        .where(and(
          eq(emails.id, input.id),
          eq(emails.apiKeyId, apiKeyData.id)
        ))
        .limit(1);

      if (!email.length) {
        throw new TRPCError({
          code: "NOT_FOUND",
          message: "Email not found",
        });
      }

      return email[0];
    }),

  list: publicProcedure
    .input(listEmailsSchema)
    .query(async ({ input, ctx }) => {
      // Verificar API Key
      const apiKey = ctx.req.headers.authorization?.replace('Bearer ', '');
      const apiKeyData = await verifyApiKey(apiKey);

      const db = await getDb();
      if (!db) {
        throw new TRPCError({
          code: "INTERNAL_SERVER_ERROR",
          message: "Database unavailable",
        });
      }

      // Construir condições
      const conditions = [eq(emails.apiKeyId, apiKeyData.id)];
      
      if (input.status) {
        conditions.push(eq(emails.status, input.status));
      }
      
      if (input.to) {
        conditions.push(like(emails.to, `%${input.to}%`));
      }

      // Buscar e-mails
      const emailsList = await db
        .select({
          id: emails.id,
          to: emails.to,
          subject: emails.subject,
          status: emails.status,
          attempts: emails.attempts,
          sentAt: emails.sentAt,
          failureReason: emails.failureReason,
          createdAt: emails.createdAt,
        })
        .from(emails)
        .where(and(...conditions))
        .orderBy(desc(emails.createdAt))
        .limit(input.limit)
        .offset(input.offset);

      // Contar total
      const totalResult = await db
        .select({ count: emails.id })
        .from(emails)
        .where(and(...conditions));

      const total = totalResult.length;

      return {
        items: emailsList,
        total,
        hasMore: input.offset + input.limit < total,
      };
    }),
});

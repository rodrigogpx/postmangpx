import { eq } from 'drizzle-orm';
import { emailQueue, EmailJob } from '../_core/queue';
import { getDb } from '../db';
import { emails, emailLogs, smtpProviders } from '../../drizzle/schema';
import { GmailProvider } from '../providers/gmailProvider';
import { EmailProvider } from '../providers/index';

// Registro de providers
const providerRegistry = new Map<string, EmailProvider>();

// Função para registrar providers
async function registerProviders() {
  const db = await getDb();
  if (!db) return;

  const providers = await db
    .select()
    .from(smtpProviders)
    .where(eq(smtpProviders.isActive, 1));

  for (const provider of providers) {
    try {
      const config = JSON.parse(provider.config);
      let emailProvider: EmailProvider;

      switch (provider.type) {
        case 'gmail':
          emailProvider = new GmailProvider(config);
          break;
        // TODO: Adicionar outros providers
        // case 'sendgrid':
        //   emailProvider = new SendGridProvider(config);
        //   break;
        // case 'aws-ses':
        //   emailProvider = new AwsSesProvider(config);
        //   break;
        // case 'smtp':
        //   emailProvider = new SmtpProvider(config);
        //   break;
        default:
          console.warn(`[Worker] Unknown provider type: ${provider.type}`);
          continue;
      }

      providerRegistry.set(provider.id, emailProvider);
      console.log(`[Worker] Registered provider: ${provider.name} (${provider.type})`);
    } catch (error) {
      console.error(`[Worker] Failed to register provider ${provider.id}:`, error);
    }
  }
}

// Função para obter provider ativo
async function getActiveProvider(): Promise<EmailProvider | null> {
  if (providerRegistry.size === 0) {
    await registerProviders();
  }

  // Por enquanto, pegar o primeiro provider disponível
  // Em produção, implementar lógica de prioridade e failover
  const providers = Array.from(providerRegistry.values());
  return providers.length > 0 ? providers[0] : null;
}

// Função para log de tentativa
async function logEmailAttempt(
  emailId: string,
  providerId: string,
  status: string,
  statusCode?: number,
  message?: string,
  errorDetails?: string,
  processingTime?: number
) {
  const db = await getDb();
  if (!db) return;

  try {
    await db.insert(emailLogs).values({
      id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      emailId,
      providerId,
      status,
      statusCode,
      message,
      errorDetails,
      processingTime,
      createdAt: new Date(),
    });
  } catch (error) {
    console.error('[Worker] Failed to log email attempt:', error);
  }
}

// Função para atualizar status do e-mail
async function updateEmailStatus(
  emailId: string,
  status: string,
  failureReason?: string,
  nextRetryAt?: Date
) {
  const db = await getDb();
  if (!db) return;

  try {
    await db
      .update(emails)
      .set({
        status,
        failureReason,
        nextRetryAt,
        updatedAt: new Date(),
        ...(status === 'sent' ? { sentAt: new Date() } : {}),
      })
      .where(eq(emails.id, emailId));
  } catch (error) {
    console.error('[Worker] Failed to update email status:', error);
  }
}

// Função para enviar webhook
async function sendWebhook(webhookUrl: string, data: any) {
  try {
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      console.error(`[Worker] Webhook failed: ${response.status} ${response.statusText}`);
    }
  } catch (error) {
    console.error('[Worker] Webhook error:', error);
  }
}

// Processador principal de jobs
async function processEmailJob(job: EmailJob) {
  const startTime = Date.now();
  let provider: EmailProvider | null = null;
  let providerId: string | null = null;

  try {
    // Obter provider ativo
    provider = await getActiveProvider();
    if (!provider) {
      throw new Error('No active email provider available');
    }

    providerId = Array.from(providerRegistry.entries())
      .find(([_, p]) => p === provider)?.[0] || null;

    console.log(`[Worker] Processing email ${job.emailId} with provider ${provider.name}`);

    // Enviar e-mail
    const result = await provider.send({
      to: job.to,
      cc: job.cc,
      bcc: job.bcc,
      subject: job.subject,
      html: job.html,
      text: job.text,
    });

    const processingTime = Date.now() - startTime;

    // Log de sucesso
    await logEmailAttempt(
      job.emailId,
      providerId || 'unknown',
      'sent',
      200,
      'Email sent successfully',
      undefined,
      processingTime
    );

    // Atualizar status
    await updateEmailStatus(job.emailId, 'sent');

    // Enviar webhook se fornecido
    if (job.webhookUrl) {
      await sendWebhook(job.webhookUrl, {
        event: 'email.sent',
        data: {
          id: job.emailId,
          externalId: job.externalId,
          messageId: result.messageId,
          timestamp: result.timestamp,
        },
      });
    }

    console.log(`[Worker] Email ${job.emailId} sent successfully`);
    return result;

  } catch (error) {
    const processingTime = Date.now() - startTime;
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';

    // Log de erro
    await logEmailAttempt(
      job.emailId,
      providerId || 'unknown',
      'failed',
      500,
      'Failed to send email',
      errorMessage,
      processingTime
    );

    // Incrementar tentativas
    const db = await getDb();
    if (db) {
      await db
        .update(emails)
        .set({
          attempts: job.attempts + 1,
          failureReason: errorMessage,
          updatedAt: new Date(),
        })
        .where(eq(emails.id, job.emailId));
    }

    // Se atingiu máximo de tentativas, marcar como failed
    if (job.attempts + 1 >= job.maxAttempts) {
      await updateEmailStatus(job.emailId, 'failed', errorMessage);

      // Enviar webhook de falha
      if (job.webhookUrl) {
        await sendWebhook(job.webhookUrl, {
          event: 'email.failed',
          data: {
            id: job.emailId,
            externalId: job.externalId,
            error: errorMessage,
            attempts: job.attempts + 1,
          },
        });
      }
    }

    console.error(`[Worker] Email ${job.emailId} failed:`, error);
    throw error;
  }
}

// Configurar handler na fila simples
emailQueue.setHandler(async (jobData) => {
  await processEmailJob(jobData);
});

// Inicializar workers
console.log('[Worker] Email workers started (Simple In-Memory Queue)');
registerProviders().catch(console.error);


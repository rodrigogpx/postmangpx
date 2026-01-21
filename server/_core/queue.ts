import Bull from 'bull';
import { ENV } from './env';

// Interface para job de e-mail
export interface EmailJob {
  emailId: string;
  to: string;
  cc?: string[];
  bcc?: string[];
  subject: string;
  html?: string;
  text?: string;
  variables?: Record<string, any>;
  webhookUrl?: string;
  externalId?: string;
  priority: 'low' | 'normal' | 'high';
  attempts: number;
  maxAttempts: number;
}

// Criar fila de e-mails
export const emailQueue = new Bull<EmailJob>('email processing', {
  redis: ENV.redisUrl,
  defaultJobOptions: {
    attempts: 5,
    backoff: {
      type: 'exponential',
      delay: 2000, // 2s, 4s, 8s, 16s, 32s
    },
    removeOnComplete: 100, // Manter últimos 100 jobs completos
    removeOnFail: 50, // Manter últimos 50 jobs falhados
  },
});

// Configurar prioridades
// Os handlers reais de processamento estão no server/workers/emailWorker.ts
// Não definimos handlers aqui para evitar erro de "Cannot define the same handler twice"

// Event listeners
emailQueue.on('completed', (job, result) => {
  console.log(`[Queue] Job completed: ${job.data.emailId}`, result);
});

emailQueue.on('failed', (job, err) => {
  console.error(`[Queue] Job failed: ${job.data.emailId}`, err);
});

emailQueue.on('stalled', (job) => {
  console.warn(`[Queue] Job stalled: ${job.data.emailId}`);
});

// Função para adicionar job na fila
export async function addEmailJob(jobData: EmailJob): Promise<Bull.Job<EmailJob>> {
  const priority = jobData.priority === 'high' ? 10 : 
                   jobData.priority === 'low' ? 1 : 5;
  
  return emailQueue.add(jobData.priority, jobData, {
    priority,
    delay: 0,
    attempts: jobData.maxAttempts,
    backoff: {
      type: 'exponential',
      delay: 2000,
    },
  });
}

// Função para obter status da fila
export async function getQueueStats() {
  const waiting = await emailQueue.getWaiting();
  const active = await emailQueue.getActive();
  const completed = await emailQueue.getCompleted();
  const failed = await emailQueue.getFailed();
  
  return {
    waiting: waiting.length,
    active: active.length,
    completed: completed.length,
    failed: failed.length,
    total: waiting.length + active.length + completed.length + failed.length,
  };
}

// Função para limpar jobs antigos
export async function cleanQueue() {
  await emailQueue.clean(24 * 60 * 60 * 1000, 'completed'); // 24 horas
  await emailQueue.clean(7 * 24 * 60 * 60 * 1000, 'failed'); // 7 dias
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('[Queue] SIGTERM received, closing queue...');
  await emailQueue.close();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('[Queue] SIGINT received, closing queue...');
  await emailQueue.close();
  process.exit(0);
});

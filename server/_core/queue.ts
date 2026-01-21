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

// Fila simples em memória para baixo consumo de recursos
// Para produção pesada, usaríamos Bull/Redis, mas aqui focamos em simplicidade
class SimpleQueue {
  private queue: EmailJob[] = [];
  private processing = false;
  private handler: ((job: EmailJob) => Promise<void>) | null = null;

  setHandler(handler: (job: EmailJob) => Promise<void>) {
    this.handler = handler;
  }

  async add(job: EmailJob) {
    this.queue.push(job);
    this.process();
  }

  private async process() {
    if (this.processing || !this.handler || this.queue.length === 0) return;
    
    this.processing = true;
    while (this.queue.length > 0) {
      const job = this.queue.shift();
      if (job) {
        try {
          await this.handler(job);
        } catch (error) {
          console.error(`[Queue] Job failed: ${job.emailId}`, error);
        }
      }
    }
    this.processing = false;
  }

  async getStats() {
    return {
      waiting: this.queue.length,
      active: this.processing ? 1 : 0,
      completed: 0, // Não rastreado na versão simples
      failed: 0,
      total: this.queue.length
    };
  }
}

export const emailQueue = new SimpleQueue();

// Função para adicionar job na fila
export async function addEmailJob(jobData: EmailJob) {
  await emailQueue.add(jobData);
  return { id: jobData.emailId };
}

// Função para obter status da fila
export async function getQueueStats() {
  return await emailQueue.getStats();
}

// Função para limpar jobs antigos (no-op na versão simples)
export async function cleanQueue() {
  // Nada para limpar em memória por enquanto
}

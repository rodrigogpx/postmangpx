# 📖 PostmanGPX - Guia Técnico Detalhado

## Arquitetura da Aplicação

### Stack Tecnológico

```
Frontend: React 19 + TypeScript + Tailwind CSS 4
Backend: Node.js + Express 4 + tRPC 11
Banco: MySQL (Drizzle ORM)
Fila: Redis + Bull
Autenticação: Manus OAuth
API: REST via tRPC
```

### Fluxo de Requisição

```
Cliente HTTP
    ↓
Nginx (Proxy Reverso)
    ↓
Express Server
    ↓
tRPC Router
    ↓
Database / Redis Queue
    ↓
Email Worker (Bull)
    ↓
SMTP Provider
    ↓
Webhook Notification
```

---

## 🗄️ Banco de Dados

### Tabelas Principais

#### `users`
- Usuários do dashboard
- Autenticação via Manus OAuth
- Campos: id, openId, name, email, role, timestamps

#### `api_keys`
- Chaves para autenticação de clientes externos
- Rate limiting por chave
- Campos: id, userId, keyHash, isActive, rateLimit, timestamps

#### `smtp_providers`
- Configurações de provedores SMTP
- Suporte a múltiplos provedores por usuário
- Campos: id, userId, name, type, config, priority, isActive

#### `email_templates`
- Templates de e-mail reutilizáveis
- Suporte a variáveis dinâmicas
- Campos: id, userId, name, subject, htmlContent, variables

#### `emails`
- Histórico de todos os e-mails
- Rastreamento de status
- Campos: id, to, subject, status, attempts, nextRetryAt, webhookUrl

#### `email_logs`
- Logs detalhados de cada tentativa
- Rastreamento de erros
- Campos: id, emailId, status, statusCode, message, errorDetails

#### `webhooks`
- Configurações de webhooks para notificações
- Campos: id, userId, url, events, secret, isActive

#### `metrics`
- Agregações para dashboard
- Atualizado por hora
- Campos: id, userId, date, hour, totalSent, totalSuccessful, totalFailed

---

## 🔌 API REST (tRPC)

### Autenticação

#### Via API Key (Clientes Externos)

```typescript
// Header
Authorization: Bearer sk_live_xxxxxxxxxxxxx

// Validação
const apiKey = req.headers.authorization?.replace('Bearer ', '');
const keyRecord = await verifyApiKey(apiKey);
```

#### Via OAuth (Dashboard)

```typescript
// Cookie automático
// Validado em protectedProcedure
```

### Endpoints Principais

#### `POST /api/trpc/emails.send`

**Input**:
```typescript
{
  to: string;
  cc?: string[];
  bcc?: string[];
  subject: string;
  template?: string; // ID do template
  html?: string;
  text?: string;
  variables?: Record<string, any>;
  webhookUrl?: string;
  externalId?: string;
  priority?: 'low' | 'normal' | 'high';
}
```

**Output**:
```typescript
{
  id: string;
  status: 'pending' | 'queued';
  createdAt: string;
}
```

**Fluxo**:
1. Validar API Key ou autenticação OAuth
2. Validar input com Zod
3. Renderizar template se fornecido
4. Criar registro no banco
5. Enfileirar job no Bull
6. Retornar ID

#### `GET /api/trpc/emails.getStatus`

**Input**:
```typescript
{
  id: string;
}
```

**Output**:
```typescript
{
  id: string;
  status: 'pending' | 'sent' | 'failed' | 'bounced';
  attempts: number;
  sentAt?: string;
  failureReason?: string;
}
```

#### `GET /api/trpc/emails.list`

**Input**:
```typescript
{
  status?: 'pending' | 'sent' | 'failed';
  to?: string;
  from?: string;
  to?: string;
  limit?: number;
  offset?: number;
}
```

**Output**:
```typescript
{
  items: Email[];
  total: number;
  hasMore: boolean;
}
```

---

## 🔄 Sistema de Fila (Bull + Redis)

### Job Structure

```typescript
interface EmailJob {
  emailId: string;
  to: string;
  cc?: string[];
  bcc?: string[];
  subject: string;
  html: string;
  text?: string;
  providerId: string;
  webhookUrl?: string;
  externalId?: string;
}
```

### Processamento

```typescript
// server/workers/emailWorker.ts

emailQueue.process(5, async (job: Bull.Job<EmailJob>) => {
  try {
    // 1. Obter provider
    const provider = await getSmtpProvider(job.data.providerId);
    
    // 2. Enviar e-mail
    const result = await provider.send(job.data);
    
    // 3. Registrar sucesso
    await logEmailSuccess(job.data.emailId, result);
    
    // 4. Atualizar status
    await updateEmailStatus(job.data.emailId, 'sent');
    
    // 5. Disparar webhook
    if (job.data.webhookUrl) {
      await notifyWebhook(job.data.webhookUrl, {
        event: 'email.sent',
        data: { id: job.data.emailId },
      });
    }
    
    return { success: true };
  } catch (error) {
    // Retry automático (até 5 tentativas)
    throw error;
  }
});
```

### Retry Strategy

```typescript
const emailQueue = new Bull('emails', {
  redis: process.env.REDIS_URL,
  defaultJobOptions: {
    attempts: 5,
    backoff: {
      type: 'exponential',
      delay: 2000, // 2s, 4s, 8s, 16s, 32s
    },
    removeOnComplete: true,
    removeOnFail: false,
  },
});
```

---

## 📧 Provedores SMTP

### Interface Comum

```typescript
export interface EmailProvider {
  name: string;
  type: 'gmail' | 'sendgrid' | 'aws-ses' | 'smtp';
  
  send(job: EmailJob): Promise<{
    messageId: string;
    timestamp: string;
  }>;
  
  testConnection(): Promise<boolean>;
  
  getConfig(): Record<string, any>;
}
```

### Implementações

#### Gmail (SMTP)

```typescript
// server/providers/gmailProvider.ts
export class GmailProvider implements EmailProvider {
  private transporter: nodemailer.Transporter;
  
  constructor(config: GmailConfig) {
    this.transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: config.email,
        pass: config.appPassword, // App Password, não senha normal
      },
    });
  }
  
  async send(job: EmailJob) {
    const result = await this.transporter.sendMail({
      from: this.config.email,
      to: job.to,
      cc: job.cc?.join(','),
      bcc: job.bcc?.join(','),
      subject: job.subject,
      html: job.html,
      text: job.text,
    });
    
    return {
      messageId: result.messageId,
      timestamp: new Date().toISOString(),
    };
  }
}
```

#### SendGrid

```typescript
// server/providers/sendgridProvider.ts
import sgMail from '@sendgrid/mail';

export class SendGridProvider implements EmailProvider {
  constructor(config: SendGridConfig) {
    sgMail.setApiKey(config.apiKey);
  }
  
  async send(job: EmailJob) {
    const result = await sgMail.send({
      to: job.to,
      from: this.config.fromEmail,
      cc: job.cc,
      bcc: job.bcc,
      subject: job.subject,
      html: job.html,
      text: job.text,
      customArgs: {
        emailId: job.emailId,
        externalId: job.externalId,
      },
    });
    
    return {
      messageId: result[0].headers['x-message-id'],
      timestamp: new Date().toISOString(),
    };
  }
}
```

#### AWS SES

```typescript
// server/providers/awsSesProvider.ts
import AWS from 'aws-sdk';

export class AwsSesProvider implements EmailProvider {
  private ses: AWS.SES;
  
  constructor(config: AwsSesConfig) {
    this.ses = new AWS.SES({
      accessKeyId: config.accessKeyId,
      secretAccessKey: config.secretAccessKey,
      region: config.region,
    });
  }
  
  async send(job: EmailJob) {
    const result = await this.ses.sendEmail({
      Source: this.config.fromEmail,
      Destination: {
        ToAddresses: [job.to],
        CcAddresses: job.cc,
        BccAddresses: job.bcc,
      },
      Message: {
        Subject: { Data: job.subject },
        Body: {
          Html: { Data: job.html },
          Text: { Data: job.text },
        },
      },
    }).promise();
    
    return {
      messageId: result.MessageId,
      timestamp: new Date().toISOString(),
    };
  }
}
```

---

## 🎨 Frontend (React)

### Estrutura de Componentes

```
client/src/
├── pages/
│   ├── Dashboard.tsx       # Home com estatísticas
│   ├── Emails.tsx          # Listagem de e-mails
│   ├── Templates.tsx       # CRUD de templates
│   ├── Providers.tsx       # Configuração SMTP
│   ├── Logs.tsx            # Visualização de logs
│   └── Settings.tsx        # Configurações do usuário
│
├── components/
│   ├── EmailTable.tsx      # Tabela de e-mails
│   ├── TemplateEditor.tsx  # Editor de templates
│   ├── ProviderForm.tsx    # Formulário de provedor
│   ├── MetricsChart.tsx    # Gráficos
│   └── ui/                 # Componentes shadcn/ui
│
├── hooks/
│   ├── useEmailList.ts     # Hook para listar e-mails
│   ├── useMetrics.ts       # Hook para métricas
│   └── useProviders.ts     # Hook para provedores
│
└── lib/
    └── trpc.ts             # Cliente tRPC
```

### Exemplo de Página

```typescript
// client/src/pages/Emails.tsx
import { trpc } from '@/lib/trpc';
import { EmailTable } from '@/components/EmailTable';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

export default function EmailsPage() {
  const [status, setStatus] = useState<'pending' | 'sent' | 'failed'>();
  
  const { data, isLoading, refetch } = trpc.emails.list.useQuery({
    status,
    limit: 20,
  });
  
  const sendMutation = trpc.emails.send.useMutation({
    onSuccess: () => {
      refetch();
    },
  });
  
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button onClick={() => setStatus(undefined)}>Todos</Button>
        <Button onClick={() => setStatus('pending')}>Pendentes</Button>
        <Button onClick={() => setStatus('sent')}>Enviados</Button>
        <Button onClick={() => setStatus('failed')}>Falhados</Button>
      </div>
      
      {isLoading ? (
        <div>Carregando...</div>
      ) : (
        <EmailTable emails={data?.items || []} />
      )}
    </div>
  );
}
```

---

## 🧪 Testes

### Teste de Procedure

```typescript
// server/emails.send.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { appRouter } from './routers';

describe('emails.send', () => {
  let caller: any;
  
  beforeEach(() => {
    const mockCtx = {
      user: { id: 1, role: 'user' },
      req: {},
      res: {},
    };
    caller = appRouter.createCaller(mockCtx);
  });
  
  it('deve enviar um e-mail com sucesso', async () => {
    const result = await caller.emails.send({
      to: 'test@example.com',
      subject: 'Test Email',
      html: '<p>Hello</p>',
    });
    
    expect(result.id).toBeDefined();
    expect(result.status).toBe('queued');
  });
  
  it('deve validar e-mail inválido', async () => {
    expect(async () => {
      await caller.emails.send({
        to: 'invalid-email',
        subject: 'Test',
        html: '<p>Hello</p>',
      });
    }).rejects.toThrow();
  });
});
```

---

## 🚀 Deployment

### Docker

```dockerfile
FROM node:22-alpine

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --prod

COPY . .

RUN pnpm build

EXPOSE 3000

CMD ["pnpm", "start"]
```

### Environment Variables

```env
# Database
DATABASE_URL=mysql://user:pass@host:3306/postmangpx

# Redis
REDIS_URL=redis://redis:6379

# OAuth
VITE_APP_ID=xxx
OAUTH_SERVER_URL=https://api.manus.im
VITE_OAUTH_PORTAL_URL=https://portal.manus.im

# Email
SMTP_FROM_EMAIL=noreply@example.com

# Webhooks
WEBHOOK_SECRET=xxx
```

---

## 📊 Monitoramento

### Métricas Importantes

- **Volume por hora**: Total de e-mails enviados
- **Taxa de sucesso**: % de e-mails entregues
- **Latência média**: Tempo médio de envio
- **Taxa de retry**: % de e-mails que precisaram retry
- **Tempo de processamento**: Fila vs. envio real

### Logs

Todos os eventos são registrados em `email_logs`:
- Tentativas de envio
- Erros e exceções
- Webhooks disparados
- Métricas de performance

---

## 🔐 Segurança

### API Key

```typescript
// Geração
const apiKey = `sk_live_${nanoid(32)}`;
const keyHash = await hash(apiKey, 10);

// Validação
const keyRecord = await db.query.apiKeys
  .findFirst({
    where: eq(apiKeys.keyHash, await hash(providedKey, 10)),
  });
```

### Rate Limiting

```typescript
// Por API Key
if (apiKey.rateLimit && requestsInWindow > apiKey.rateLimit) {
  throw new TRPCError({
    code: 'TOO_MANY_REQUESTS',
    message: 'Rate limit exceeded',
  });
}
```

### Webhook Signature

```typescript
// Geração
const signature = crypto
  .createHmac('sha256', webhook.secret)
  .update(JSON.stringify(payload))
  .digest('hex');

// Validação
const expectedSignature = crypto
  .createHmac('sha256', webhook.secret)
  .update(body)
  .digest('hex');

if (signature !== expectedSignature) {
  throw new Error('Invalid signature');
}
```

---

## 📚 Referências Rápidas

### Adicionar Nova Tabela

1. Editar `drizzle/schema.ts`
2. Executar `pnpm db:push`
3. Criar helpers em `server/db.ts`
4. Usar em `server/routers.ts`

### Adicionar Novo Procedure

1. Criar em `server/routers.ts`
2. Definir input com Zod
3. Implementar lógica
4. Criar testes
5. Usar no frontend com `trpc.*.useQuery/useMutation`

### Adicionar Novo Provider

1. Criar arquivo em `server/providers/`
2. Implementar interface `EmailProvider`
3. Registrar em `server/providers/index.ts`
4. Testar conexão

---

Boa sorte no desenvolvimento! 🚀

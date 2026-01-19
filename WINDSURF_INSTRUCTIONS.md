# 🚀 PostmanGPX - Instruções para Windsurf

Este documento fornece instruções detalhadas para continuar o desenvolvimento do PostmanGPX usando a plataforma Windsurf.

## 📋 Estado Atual do Projeto

**Checkpoint**: `fede5233`

### ✅ Concluído
- Schema do banco de dados (Drizzle ORM com 8 tabelas)
- Docker Compose simplificado (App + Redis)
- Dockerfile otimizado
- Documentação básica (README, ARCHITECTURE)
- Estrutura de pastas e configurações iniciais

### ⏳ Próximas Fases
1. **API REST** - Endpoints de envio de e-mails
2. **Sistema de Fila** - Bull + Redis para processamento
3. **Dashboard** - Interface React para gerenciamento
4. **Provedores SMTP** - Integração com Gmail, SendGrid, AWS SES
5. **Webhooks e Métricas** - Notificações e estatísticas

---

## 🔧 Como Começar

### 1. Clonar e Preparar

```bash
# Clonar repositório
git clone https://github.com/rodrigogpx/postmangpx.git
cd postmangpx

# Instalar dependências
pnpm install

# Aplicar migrações do banco
pnpm db:push

# Iniciar em desenvolvimento
pnpm dev
```

### 2. Estrutura do Projeto

```
postmangpx/
├── client/                  # Frontend React
│   ├── src/
│   │   ├── pages/          # Páginas principais
│   │   ├── components/     # Componentes reutilizáveis
│   │   ├── lib/            # Utilitários (tRPC client)
│   │   └── App.tsx         # Roteamento
│   └── public/             # Arquivos estáticos
│
├── server/                  # Backend Node.js
│   ├── routers.ts          # Definição de procedures tRPC
│   ├── db.ts               # Helpers de banco de dados
│   ├── _core/              # Infraestrutura (não editar)
│   │   ├── index.ts        # Servidor Express
│   │   ├── context.ts      # Contexto tRPC
│   │   └── trpc.ts         # Configuração tRPC
│   └── workers/            # Workers de fila (criar aqui)
│
├── drizzle/                # Banco de dados
│   ├── schema.ts           # Definição de tabelas
│   └── seed.ts             # Dados iniciais
│
├── shared/                 # Código compartilhado
│   ├── types.ts            # Tipos comuns
│   └── const.ts            # Constantes
│
├── docker-compose.yml      # Orquestração de containers
├── Dockerfile              # Build da imagem
├── package.json            # Dependências
├── todo.md                 # Tarefas do projeto
└── DEVELOPMENT_GUIDE.md    # Guia técnico detalhado
```

---

## 📝 Fases de Desenvolvimento

### Fase 1: API REST Básica (PRÓXIMA)

**Objetivo**: Criar endpoints para envio de e-mails

**Arquivos a Editar**:
- `server/routers.ts` - Adicionar procedures tRPC
- `server/db.ts` - Adicionar helpers de banco

**Procedures a Implementar**:

```typescript
// POST /api/trpc/emails.send
emails.send: protectedProcedure
  .input(z.object({
    to: z.string().email(),
    subject: z.string(),
    template: z.string().optional(),
    variables: z.record(z.any()).optional(),
    webhookUrl: z.string().url().optional(),
  }))
  .mutation(async ({ input, ctx }) => {
    // 1. Validar API Key
    // 2. Renderizar template
    // 3. Enfileirar job
    // 4. Retornar ID do e-mail
  })

// GET /api/trpc/emails.getStatus
emails.getStatus: publicProcedure
  .input(z.object({ id: z.string() }))
  .query(async ({ input }) => {
    // Retornar status do e-mail
  })

// GET /api/trpc/emails.list
emails.list: protectedProcedure
  .input(z.object({
    status: z.enum(['pending', 'sent', 'failed']).optional(),
    limit: z.number().default(10),
    offset: z.number().default(0),
  }))
  .query(async ({ input, ctx }) => {
    // Listar e-mails com filtros
  })
```

**Testes a Criar**:
- `server/emails.send.test.ts`
- `server/emails.list.test.ts`

---

### Fase 2: Sistema de Fila

**Objetivo**: Processar e-mails assincronamente

**Arquivos a Criar**:
- `server/workers/emailWorker.ts` - Worker de processamento
- `server/queue/emailQueue.ts` - Configuração da fila

**Implementação**:

```typescript
// server/queue/emailQueue.ts
import Bull from 'bull';

export const emailQueue = new Bull('emails', {
  redis: process.env.REDIS_URL,
});

export interface EmailJob {
  emailId: string;
  to: string;
  subject: string;
  html: string;
  providerId: string;
}

// server/workers/emailWorker.ts
emailQueue.process(5, async (job: Bull.Job<EmailJob>) => {
  // 1. Obter configuração do provedor SMTP
  // 2. Enviar e-mail
  // 3. Registrar log
  // 4. Atualizar status
  // 5. Disparar webhook se configurado
});

emailQueue.on('completed', (job) => {
  console.log(`Email ${job.data.emailId} enviado com sucesso`);
});

emailQueue.on('failed', (job, err) => {
  console.error(`Email ${job.data.emailId} falhou:`, err);
  // Retry automático configurado no Bull
});
```

---

### Fase 3: Dashboard React

**Objetivo**: Interface para gerenciar e-mails e configurações

**Páginas a Criar**:

1. **Dashboard Home** (`client/src/pages/Dashboard.tsx`)
   - Estatísticas em tempo real
   - Gráficos de volume
   - Últimos e-mails

2. **Listagem de E-mails** (`client/src/pages/Emails.tsx`)
   - Tabela com filtros
   - Status colorido
   - Busca por destinatário

3. **Templates** (`client/src/pages/Templates.tsx`)
   - CRUD de templates
   - Editor HTML
   - Preview

4. **Provedores** (`client/src/pages/Providers.tsx`)
   - Configuração de SMTP
   - Teste de conexão
   - Priorização

5. **Logs** (`client/src/pages/Logs.tsx`)
   - Visualização de logs
   - Filtros avançados
   - Export

---

### Fase 4: Provedores SMTP

**Objetivo**: Suportar múltiplos provedores

**Implementar**:
- `server/providers/gmailProvider.ts`
- `server/providers/sendgridProvider.ts`
- `server/providers/awsSesProvider.ts`
- `server/providers/smtpProvider.ts`

**Interface Comum**:

```typescript
export interface EmailProvider {
  send(email: EmailJob): Promise<{ messageId: string }>;
  testConnection(): Promise<boolean>;
}
```

---

## 🎯 Padrões de Código

### tRPC Procedures

```typescript
// Sempre tipado e validado
export const appRouter = router({
  emails: router({
    send: protectedProcedure
      .input(emailSendSchema)
      .mutation(async ({ input, ctx }) => {
        // Lógica aqui
      }),
  }),
});
```

### Banco de Dados

```typescript
// Sempre usar helpers em server/db.ts
export async function createEmail(data: InsertEmail) {
  const db = await getDb();
  return db.insert(emails).values(data);
}

// No router
const email = await createEmail({
  to: input.to,
  subject: input.subject,
  // ...
});
```

### React Components

```typescript
// Sempre usar tRPC hooks
export function EmailList() {
  const { data, isLoading } = trpc.emails.list.useQuery({
    limit: 10,
  });
  
  const sendMutation = trpc.emails.send.useMutation();
  
  return (
    // Componente aqui
  );
}
```

---

## 🧪 Testes

### Executar Testes

```bash
pnpm test
```

### Padrão de Teste

```typescript
import { describe, it, expect } from 'vitest';
import { appRouter } from './routers';

describe('emails.send', () => {
  it('deve enviar um e-mail', async () => {
    const caller = appRouter.createCaller(mockContext);
    const result = await caller.emails.send({
      to: 'test@example.com',
      subject: 'Test',
    });
    expect(result.id).toBeDefined();
  });
});
```

---

## 🐳 Docker

### Desenvolvimento Local

```bash
# Iniciar containers
docker compose up -d

# Ver logs
docker compose logs -f app

# Parar
docker compose down
```

### Build para Produção

```bash
docker build -t postmangpx:latest .
docker run -p 3000:3000 postmangpx:latest
```

---

## 📚 Recursos Úteis

- **tRPC**: https://trpc.io
- **Drizzle ORM**: https://orm.drizzle.team
- **Bull Queue**: https://github.com/OptimalBits/bull
- **Nodemailer**: https://nodemailer.com
- **React**: https://react.dev

---

## ⚠️ Pontos Importantes

1. **Sempre tipado**: Use TypeScript rigorosamente
2. **Validação**: Use Zod para validar inputs
3. **Testes**: Escreva testes para cada feature
4. **Commits**: Faça commits pequenos e descritivos
5. **Documentação**: Mantenha este arquivo atualizado

---

## 🚨 Troubleshooting

### Erro: "Cannot find module"
```bash
pnpm install
pnpm db:push
```

### Erro: "Redis connection refused"
```bash
docker compose up -d redis
```

### Erro: "Database locked"
```bash
rm data/postmangpx.db
pnpm db:push
```

---

## 📞 Suporte

Para dúvidas sobre a arquitetura ou padrões, consulte `DEVELOPMENT_GUIDE.md`.

Boa sorte! 🎉

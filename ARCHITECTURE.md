# PostmanGPX - Arquitetura Simplificada

## Visão Geral

PostmanGPX é uma plataforma leve de envio de e-mails com foco em simplicidade e facilidade de uso.

```
┌─────────────────────┐
│  Clientes Externos  │
│   (cac360, etc)     │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │  API REST    │
    │  /api/v1/    │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Redis Queue  │
    │ (Bull)       │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   Worker     │
    │ Processa     │
    │ E-mails      │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ SMTP         │
    │ Providers    │
    └──────────────┘

    ┌──────────────┐
    │  SQLite DB   │
    │  (Local)     │
    └──────────────┘

    ┌──────────────┐
    │  Dashboard   │
    │  React UI    │
    └──────────────┘
```

## Componentes Principais

### 1. API REST (`/api/v1/emails`)
- Receber requisições de envio
- Validar autenticação (API Key)
- Enfileirar jobs
- Retornar status

### 2. Redis Queue (Bull)
- Fila de processamento
- Retry automático
- Priorização simples

### 3. Email Worker
- Processar jobs da fila
- Renderizar templates
- Enviar via SMTP
- Registrar logs

### 4. SQLite Database
- Histórico de e-mails
- Templates
- Configurações de provedores
- Logs

### 5. Dashboard (React)
- Estatísticas em tempo real
- Gerenciamento de templates
- Configuração de provedores
- Visualização de logs

## Fluxo Simples

```
1. Cliente → POST /api/v1/emails/send
2. API valida e enfileira job
3. Worker processa job
4. E-mail é enviado via SMTP
5. Status é atualizado no banco
6. Cliente consulta status
```

## Tecnologias

- **Frontend**: React 19 + Tailwind CSS 4
- **Backend**: Node.js + Express + tRPC
- **Database**: SQLite (Drizzle ORM)
- **Queue**: Redis + Bull
- **Containerização**: Docker + Docker Compose

## Escalabilidade

Para escalar:
1. Adicionar mais workers no docker-compose
2. Usar Redis Cluster
3. Migrar para PostgreSQL se necessário

Mas por padrão, tudo roda em um único container!

## Segurança Básica

- API Keys com hash
- Rate limiting por chave
- Validação de entrada
- HTTPS em produção

Simples e eficaz.

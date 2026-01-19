# PostmanGPX - Serviço de E-mail e Mensageria

Plataforma simples e robusta de envio de e-mails com API REST, dashboard moderno e suporte a múltiplos provedores SMTP.

## 🚀 Quick Start

### Pré-requisitos
- Docker
- Docker Compose

### Execução

```bash
# 1. Clonar repositório
git clone https://github.com/rodrigogpx/postmangpx.git
cd postmangpx

# 2. Criar arquivo .env (opcional, usa padrões se não existir)
cp .env.example .env

# 3. Iniciar containers
docker compose up -d

# 4. Acessar aplicação
# Dashboard: http://localhost:3000
# API: http://localhost:3000/api
```

A aplicação estará pronta em segundos!

## 📋 Funcionalidades

- ✅ **API REST** para envio de e-mails
- ✅ **Dashboard moderno** com React + Tailwind
- ✅ **Fila de processamento** com Redis
- ✅ **Múltiplos provedores SMTP** (Gmail, SendGrid, AWS SES, SMTP customizado)
- ✅ **Templates de e-mail** com editor visual
- ✅ **Logs detalhados** com filtros
- ✅ **Autenticação via API Key**
- ✅ **Webhooks** para notificação de status
- ✅ **Métricas e gráficos** de performance
- ✅ **Retry automático** com backoff exponencial

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Aplicação
NODE_ENV=production
PORT=3000
JWT_SECRET=sua_chave_secreta_aqui
API_KEY_SALT=seu_salt_aqui

# Redis
REDIS_URL=redis://redis:6379

# Banco de Dados
DATABASE_URL=file:/app/data/postmangpx.db
```

## 📚 API REST

### Autenticação

Todas as requisições devem incluir a chave de API:

```bash
Authorization: Bearer YOUR_API_KEY
```

### Endpoints Principais

#### Enviar E-mail
```bash
POST /api/v1/emails/send

{
  "to": "user@example.com",
  "subject": "Bem-vindo",
  "template": "welcome",
  "variables": {
    "name": "João"
  }
}
```

#### Obter Status
```bash
GET /api/v1/emails/:id
```

#### Listar E-mails
```bash
GET /api/v1/emails?status=sent&limit=10
```

## 🎨 Dashboard

Acesse o dashboard em `http://localhost:3000` para:

- Visualizar estatísticas em tempo real
- Gerenciar templates de e-mail
- Configurar provedores SMTP
- Visualizar logs detalhados
- Gerenciar webhooks
- Analisar métricas de performance

## 🐳 Docker

### Build Local

```bash
docker build -t postmangpx:latest .
```

### Executar Container Individual

```bash
docker run -p 3000:3000 \
  -e NODE_ENV=production \
  -e JWT_SECRET=sua_chave \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  postmangpx:latest
```

## 📦 Estrutura do Projeto

```
postmangpx/
├── client/              # Frontend React
├── server/              # Backend Node.js
├── drizzle/             # Schema do banco de dados
├── docker-compose.yml   # Orquestração de containers
├── Dockerfile           # Build da imagem
├── package.json         # Dependências
└── README.md            # Este arquivo
```

## 🔐 Segurança

- API Keys com hash SHA-256
- Rate limiting por chave
- HTTPS recomendado em produção
- Webhooks assinados com HMAC-SHA256
- Senhas SMTP criptografadas

## 📊 Monitoramento

A aplicação expõe métricas em:

```bash
GET /health
```

## 🛠️ Troubleshooting

### Containers não iniciam

```bash
# Verificar logs
docker compose logs -f app

# Reiniciar
docker compose restart
```

### Banco de dados corrompido

```bash
# Remover volume e reiniciar
docker compose down -v
docker compose up -d
```

### Redis desconectado

```bash
# Verificar conexão
docker compose exec redis redis-cli ping
```

## 📝 Licença

MIT

## 👥 Suporte

Para dúvidas ou problemas, abra uma issue no repositório.

---

**Desenvolvido com ❤️ para simplificar o envio de e-mails**

# PostmanGPX

Sistema de envio de e-mails transacionais construído com Flask, projetado para facilitar o envio de e-mails através de múltiplos providers SMTP com tracking e gestão de API keys.

## 🚀 Features

- **Múltiplos Providers SMTP**: Configure diversos provedores de e-mail
- **API Keys**: Sistema de autenticação via tokens para integração
- **Dashboard Web**: Interface administrativa para gestão
- **Email Tracking**: Monitoramento de status de entrega
- **Anexos e Imagens**: Suporte a attachments e inline CID
- **Logs Detalhados**: Registro completo de operações

## 📋 Pré-requisitos

- Python 3.8+
- SQLite (padrão) ou PostgreSQL/MySQL
- Docker (opcional)

## 🛠️ Instalação

### Local Development

```bash
# Clone o repositório
git clone https://github.com/rodrigogpx/postmangpx.git
cd postmangpx

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# Inicialize o banco de dados
flask db init
flask db migrate
flask db upgrade

# Execute a aplicação
python app.py
```

### Docker

```bash
# Build e execute
docker-compose up -d
```

## 🔧 Configuração

### Variáveis de Ambiente

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///data/postmangpx.db
# Ou para PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### Providers SMTP

Configure providers através do dashboard em `/providers`:

- **Gmail**: smtp.gmail.com:587
- **Outlook**: smtp-mail.outlook.com:587
- **Amazon SES**: email-smtp.us-east-1.amazonaws.com:587

## 📡 API

### Envio de E-mail

```bash
POST /api/v1/send
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "to": "destinatario@example.com",
  "subject": "Assunto do E-mail",
  "html": "<h1>Conteúdo HTML</h1>",
  "text": "Conteúdo texto plano",
  "from": "remetente@example.com",
  "replyTo": "reply@example.com"
}
```

### Com Anexos

```bash
POST /api/v1/send
Content-Type: multipart/form-data
Authorization: Bearer YOUR_API_KEY

Form Data:
- to: destinatario@example.com
- subject: Assunto
- html: <h1>Conteúdo</h1>
- files: [arquivo1.pdf, imagem.png]
```

## 🎯 Endpoints

### Web Interface
- `/` - Login
- `/dashboard` - Painel principal
- `/emails` - Histórico de e-mails
- `/emails/<id>` - Detalhes do e-mail
- `/providers` - Gestão de providers
- `/api-keys` - Gestão de API keys

### API REST
- `POST /api/v1/send` - Enviar e-mail
- `GET /api/v1/emails` - Listar e-mails
- `GET /api/v1/emails/<id>` - Detalhes do e-mail

## 📊 Estrutura do Banco

```sql
users          - Usuários do sistema
providers      - Configurações SMTP
api_keys       - Tokens de API
emails         - Registros de e-mails
email_logs     - Logs de entrega
```

## 🔐 Segurança

- Senhas hasheadas com Werkzeug
- API keys com tokens seguros
- Proteção CSRF
- Autenticação de sessão

## 📝 Logs

O sistema gera logs detalhados para:
- Tentativas de envio
- Status SMTP
- Erros e falhas
- Delivery tracking

## 🚀 Deploy

### Railway

```bash
# Configure railway.json
railway login
railway link
railway up
```

### Docker Production

```bash
docker build -t postmangpx .
docker run -p 5000:5000 -e DATABASE_URL=postgresql://... postmangpx
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie branch `git checkout -b feature/nova-feature`
3. Commit `git commit -am 'Add new feature'`
4. Push `git push origin feature/nova-feature`
5. Pull Request

## 📄 Licença

MIT License - veja arquivo LICENSE

## 🆘 Suporte

- Issues: [GitHub Issues](https://github.com/rodrigogpx/postmangpx/issues)
- Documentação: [Wiki](https://github.com/rodrigogpx/postmangpx/wiki)

---

**PostmanGPX** - Sistema simples e robusto para envio de e-mails transacionais.
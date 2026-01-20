# Guia de Integração - PostmanGPX

Este documento fornece instruções detalhadas para integrar seu sistema com o PostmanGPX para envio de e-mails de forma escalável e confiável.

## 1. Conceitos Básicos

O PostmanGPX utiliza uma arquitetura baseada em tRPC/API REST com processamento assíncrono via Redis.

### Endpoints Base
- **Produção**: `http://seu-servidor:3000/api/trpc`
- **Ambiente de Teste**: Mesma URL, utilizando uma API Key de teste.

## 2. Autenticação

Todas as requisições devem incluir o cabeçalho `Authorization` com o seu Bearer Token (API Key).

**Formato das API Keys:**
- `pmgpx_live_[32_caracteres]`: Para envios reais.
- `pmgpx_test_[32_caracteres]`: Para simulações e testes.

```http
Authorization: Bearer pmgpx_live_vossos_tokens_de_32_caracteres
```

## 3. Envio de E-mails

### POST `/emails.send`

Este é o endpoint principal para disparar mensagens.

#### Payload (JSON)
| Campo | Tipo | Obrigatório | Descrição |
| :--- | :--- | :--- | :--- |
| `to` | `string` | Sim | E-mail do destinatário. |
| `subject` | `string` | Sim | Assunto da mensagem. |
| `html` | `string` | Condicional | Conteúdo em formato HTML. |
| `text` | `string` | Condicional | Conteúdo em formato texto puro. |
| `template` | `string` | Condicional | UUID do template pré-configurado. |
| `variables` | `object` | Não | Variáveis dinâmicas para o template (ex: `{"nome": "João"}`). |
| `priority` | `enum` | Não | `low`, `normal`, `high`. Padrão: `normal`. |
| `webhookUrl` | `string` | Não | URL para receber notificações de status. |
| `externalId` | `string` | Não | Seu ID de referência interno. |

*Nota: É obrigatório enviar ao menos um dos campos: `html`, `text` ou `template`.*

#### Exemplo com cURL:
```bash
curl -X POST http://localhost:3000/api/trpc/emails.send \
  -H "Authorization: Bearer pmgpx_live_sua_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "cliente@exemplo.com",
    "subject": "Confirmação de Cadastro",
    "html": "<h1>Olá {{nome}}!</h1><p>Seja bem-vindo.</p>",
    "variables": { "nome": "Rodrigo" },
    "priority": "high"
  }'
```

## 4. Consulta de Status

### GET `/emails.getStatus`

Permite verificar o estado atual de um e-mail específico.

#### Query Params:
- `input`: `{"id": "UUID-DO-EMAIL"}`

#### Estados Possíveis:
- `pending`: Aguardando na fila.
- `sent`: Enviado com sucesso ao provedor final.
- `failed`: Falha crítica após todas as tentativas de reenvio.

## 5. Integração via Webhooks

Se você fornecer uma `webhookUrl` no envio, o PostmanGPX enviará um POST para sua URL sempre que o status mudar.

**Exemplo de Payload de Webhook:**
```json
{
  "event": "email.sent",
  "emailId": "uuid-aqui",
  "externalId": "seu-id-opcional",
  "timestamp": "2026-01-20T10:00:00Z"
}
```

## 6. Melhores Práticas

1. **Uso de Variáveis**: Sempre utilize o campo `variables` em vez de concatenar strings no código cliente para evitar problemas de encoding.
2. **ExternalId**: Utilize o `externalId` para correlacionar os logs do PostmanGPX com os registros do seu próprio banco de dados.
3. **Tratamento de Erros**: Verifique o código de status HTTP:
   - `401`: Problemas com API Key.
   - `400`: Payload inválido (Zod validation error).
   - `429`: Limite de taxa (Rate Limit) excedido.

---
*Para suporte técnico, consulte o README.md principal do projeto.*

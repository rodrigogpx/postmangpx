# PostmanGPX - Project TODO (Versão Simplificada)

## Fase 1: Banco de Dados
- [ ] Definir schema Drizzle (emails, templates, providers, api_keys, logs)
- [ ] Criar migrações
- [ ] Seed de dados iniciais

## Fase 2: API REST Básica
- [ ] Autenticação via API Key
- [ ] Endpoint POST /api/v1/emails/send
- [ ] Endpoint GET /api/v1/emails/:id
- [ ] Endpoint GET /api/v1/emails (com filtros)
- [ ] Validação de requisições
- [ ] Rate limiting

## Fase 3: Fila e Worker
- [ ] Configurar Bull + Redis
- [ ] Implementar worker de processamento
- [ ] Retry automático com backoff
- [ ] Logging de jobs

## Fase 4: Provedores SMTP
- [ ] Suporte a Gmail
- [ ] Suporte a SendGrid
- [ ] Suporte a SMTP customizado
- [ ] Seleção de provedor
- [ ] Teste de conexão

## Fase 5: Templates
- [ ] Sistema de templates com variáveis
- [ ] Renderização HTML
- [ ] Renderização texto plano

## Fase 6: Dashboard - Home
- [ ] Layout principal
- [ ] Navegação
- [ ] Autenticação
- [ ] Resumo de estatísticas

## Fase 7: Dashboard - E-mails
- [ ] Listagem de e-mails
- [ ] Filtros (status, data, destinatário)
- [ ] Busca
- [ ] Detalhes de e-mail
- [ ] Paginação

## Fase 8: Dashboard - Templates
- [ ] Listagem de templates
- [ ] Editor visual
- [ ] Preview
- [ ] Teste de template
- [ ] CRUD completo

## Fase 9: Dashboard - Provedores
- [ ] Listagem de provedores
- [ ] Formulário de configuração
- [ ] Teste de conexão
- [ ] Priorização

## Fase 10: Dashboard - Logs
- [ ] Visualização de logs
- [ ] Filtros avançados
- [ ] Busca
- [ ] Export

## Fase 11: Webhooks
- [ ] Endpoint para registrar webhooks
- [ ] Disparo de webhooks
- [ ] Histórico de webhooks
- [ ] Retry automático

## Fase 12: Métricas
- [ ] Dashboard de estatísticas
- [ ] Gráficos de volume
- [ ] Taxa de sucesso
- [ ] Latência média

## Fase 13: Testes e Otimizações
- [ ] Testes unitários
- [ ] Testes de integração
- [ ] Otimizações de performance
- [ ] Documentação

## Fase 14: Deployment
- [ ] Docker + Docker Compose
- [ ] CI/CD básico
- [ ] Documentação de deployment

#!/bin/bash

# Script de Deploy - PostmanGPX
echo "🚀 Iniciando deploy do PostmanGPX..."

# 1. Puxar as últimas alterações do Git
echo "📥 Atualizando código do repositório..."
git pull origin main

# 2. Verificar se o arquivo .env existe, se não, criar do exemplo
if [ ! -f .env ]; then
    echo "⚠️ Arquivo .env não encontrado. Criando a partir do .env.example..."
    cp .env.example .env
    echo "❗ Por favor, edite o arquivo .env com suas configurações reais e execute o script novamente."
    exit 1
fi

# 3. Carregar variáveis de ambiente para o shell (necessário para os build args do Docker)
export $(grep -v '^#' .env | xargs)

# 4. Parar containers antigos (opcional, mas recomendado para limpeza)
echo "🛑 Parando containers atuais..."
docker compose down

# 5. Build e Up
# Usamos --build para garantir que o frontend seja recompilado com as variáveis do .env
echo "🏗️ Construindo e iniciando containers..."
docker compose up -d --build

echo "✅ Deploy finalizado com sucesso!"
echo "📡 Acesse em: http://seu-ip:3000"
echo "📜 Verifique os logs com: docker logs -f postmangpx-app"

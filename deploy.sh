#!/bin/bash

# ============================================
# Script de Deploy - PostmanGPX (Python/Flask)
# ============================================

echo "🚀 Iniciando deploy do PostmanGPX..."

# 1. Puxar as últimas alterações do Git
echo "📥 Atualizando código do repositório..."
git pull origin main

# 2. Parar containers antigos
echo "🛑 Parando containers atuais..."
docker compose down

# 3. Build e Up
echo "🏗️ Construindo e iniciando container..."
docker compose up -d --build

# 4. Aguardar inicialização
echo "⏳ Aguardando inicialização..."
sleep 5

# 5. Verificar status
if docker ps | grep -q postmangpx-app; then
    echo ""
    echo "✅ Deploy finalizado com sucesso!"
    echo ""
    echo "📡 Acesse em: http://$(hostname -I | awk '{print $1}'):3000"
    echo ""
    echo "🔑 Credenciais padrão:"
    echo "   Usuário: admin"
    echo "   Senha:   Carbex100"
    echo ""
    echo "📜 Verifique os logs com: docker logs -f postmangpx-app"
else
    echo "❌ Erro no deploy. Verifique os logs:"
    docker logs postmangpx-app
fi

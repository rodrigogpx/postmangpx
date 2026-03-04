#!/bin/bash

# ============================================
# Script de Atualização - PostmanGPX
# ============================================

echo "🚀 Iniciando atualização do PostmanGPX a partir do GitHub..."

# Entrar no diretório do projeto (ajuste se necessário dependendo de onde é executado)
# cd /caminho/para/o/postmangpx

# 1. Puxar as últimas alterações do Git
echo "📥 Puxando últimas alterações (git pull)..."
git reset --hard HEAD
git pull origin main

# 2. Reconstruir e reiniciar os containers via Docker Compose
echo "🏗️ Reconstruindo e reiniciando o container..."
docker compose down
docker compose up -d --build

# 3. Limpar imagens antigas para não encher o disco da VM
echo "🧹 Limpando imagens Docker antigas (prune)..."
docker image prune -f

echo "✅ Atualização concluída com sucesso!"

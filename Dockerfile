# Stage 1: Build
FROM node:22-alpine AS builder

WORKDIR /app

# Instalar pnpm
RUN npm install -g pnpm

# Copiar arquivos de dependências
COPY package.json pnpm-lock.yaml ./
COPY patches ./patches

# Instalar todas as dependências (incluindo dev)
RUN pnpm install

# Copiar código fonte
COPY . .

# Build Args para o Vite (Frontend)
ARG VITE_APP_ID
ARG VITE_OAUTH_PORTAL_URL
ENV VITE_APP_ID=$VITE_APP_ID
ENV VITE_OAUTH_PORTAL_URL=$VITE_OAUTH_PORTAL_URL

# Build da aplicação
RUN pnpm build

# Stage 2: Runtime (Imagem Final Leve)
FROM node:22-alpine

WORKDIR /app

# Instalar curl para healthcheck e pnpm para start (opcional, pode usar node direto)
RUN apk add --no-cache curl && npm install -g pnpm

# Copiar apenas os arquivos necessários do builder
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/drizzle ./drizzle

# Criar diretório de dados para SQLite e logs
RUN mkdir -p /app/data /app/logs

# Expor porta
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Iniciar aplicação
CMD ["pnpm", "start"]


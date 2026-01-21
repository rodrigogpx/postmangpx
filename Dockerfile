FROM node:22-alpine

WORKDIR /app

# Instalar pnpm e curl para healthcheck
RUN apk add --no-cache curl && \
    npm install -g pnpm && npm cache clean --force

# Copiar dependências
COPY package.json pnpm-lock.yaml ./
COPY patches ./patches

# Instalar dependências
RUN pnpm install

# Copiar código
COPY . .

# Build Args para o Vite (Frontend)
ARG VITE_APP_ID
ARG VITE_OAUTH_PORTAL_URL
ENV VITE_APP_ID=$VITE_APP_ID
ENV VITE_OAUTH_PORTAL_URL=$VITE_OAUTH_PORTAL_URL

# Build
RUN pnpm build

# Criar diretórios de dados
RUN mkdir -p /app/data /app/logs

# Expor porta
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Iniciar aplicação
CMD ["pnpm", "start"]

# PostmanGPX - Python/Flask
FROM python:3.12-alpine

WORKDIR /app

# Instalar dependências do sistema
RUN apk add --no-cache curl

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app.py .
COPY templates ./templates

# Criar diretório de dados para SQLite
RUN mkdir -p /app/data

# Expor porta
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Variáveis de ambiente padrão
ENV PORT=3000
ENV FLASK_DEBUG=false

# Iniciar aplicação com Gunicorn (produção)
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "--workers", "2", "--threads", "4", "app:app"]


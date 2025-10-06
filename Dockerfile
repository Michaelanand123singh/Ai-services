# AI-services/Dockerfile (relevant corrected version)
FROM python:3.11-slim

LABEL maintainer="Bloocube Team"
LABEL version="1.0.0"
LABEL description="Bloocube AI Services for GCP Cloud Run"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV NLTK_DATA=/app/nltk_data

ENV NODE_ENV=production
ENV AI_SERVICE_PORT=8080
ENV AI_SERVICE_HOST=0.0.0.0

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    curl \
    wget \
    git \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /bin/bash -c "App User" appuser

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

RUN python -c "import os, nltk; d=os.environ.get('NLTK_DATA','/app/nltk_data'); os.makedirs(d, exist_ok=True); import nltk; nltk.download('punkt', download_dir=d, quiet=True); nltk.download('stopwords', download_dir=d, quiet=True)" || true

COPY . .

RUN mkdir -p logs data uploads temp && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app

USER appuser

# Create startup script in a safe way using a heredoc to avoid quoting problems
RUN cat <<'EOF' > /app/start.sh
#!/bin/bash
set -euo pipefail

echo "🚀 Starting Bloocube AI Services..."
echo "📊 Environment: ${NODE_ENV:-production}"

: "${PORT:=8080}"
LOG_LEVEL="$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')"
HOST="${AI_SERVICE_HOST:-0.0.0.0}"

echo "🌐 Port: ${PORT}"
echo "🏠 Host: ${HOST}"
echo "🪵 Log level: ${LOG_LEVEL}"

python - <<PY || true
import sys, os
print("PY: python version:", sys.version)
print("PY: PYTHONPATH:", os.environ.get('PYTHONPATH'))
PY

WORKERS="${UVICORN_WORKERS:-2}"
echo "🧵 Uvicorn workers: ${WORKERS}"

exec uvicorn src.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --access-log \
    --log-level "${LOG_LEVEL}"
EOF


RUN chmod +x /app/start.sh

EXPOSE 8080

# I recommend removing Dockerfile HEALTHCHECK for Cloud Run builds (Cloud Run manages healthchecks)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
#     CMD curl -f http://localhost:8080/health || exit 1

CMD ["/app/start.sh"]

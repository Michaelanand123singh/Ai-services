FROM python:3.11-slim

LABEL maintainer="Bloocube Team"
LABEL version="1.0.0"
LABEL description="Bloocube AI Services for GCP Cloud Run"

WORKDIR /app

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV NLTK_DATA=/app/nltk_data
ENV NODE_ENV=production
ENV AI_SERVICE_PORT=8080
ENV AI_SERVICE_HOST=0.0.0.0

# System dependencies
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

# Create non-root user
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /bin/bash -c "App User" appuser

# Python dependencies - optimized for heavy AI packages
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt --timeout=600 --retries=3

# NLTK data
RUN python - <<'PY'
import os, nltk
d = os.environ.get('NLTK_DATA', '/app/nltk_data')
os.makedirs(d, exist_ok=True)
nltk.download('punkt', download_dir=d, quiet=True)
nltk.download('stopwords', download_dir=d, quiet=True)
PY

# Copy app
COPY . .

# Setup directories and permissions
RUN mkdir -p logs data uploads temp && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app

USER appuser

# Startup script
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

# Debug info
echo "🔍 Python version: $(python --version)"
echo "🔍 Working directory: $(pwd)"
echo "🔍 Files in /app: $(ls -la /app)"
echo "🔍 Python path: $(python -c 'import sys; print(sys.path)')"

# Test basic imports first
echo "🧪 Testing basic imports..."
python -c "
try:
    import fastapi
    print('✅ FastAPI imported successfully')
except Exception as e:
    print(f'❌ FastAPI import failed: {e}')

try:
    import uvicorn
    print('✅ Uvicorn imported successfully')
except Exception as e:
    print(f'❌ Uvicorn import failed: {e}')

try:
    import pydantic
    print('✅ Pydantic imported successfully')
except Exception as e:
    print(f'❌ Pydantic import failed: {e}')
"

# Test app creation
echo "🧪 Testing app creation..."
python -c "
try:
    from src.main import app
    print('✅ FastAPI app created successfully')
    print(f'App type: {type(app)}')
except Exception as e:
    print(f'❌ App creation failed: {e}')
    import traceback
    traceback.print_exc()
"

# Test heavy imports (these might fail but shouldn't crash the app)
echo "🧪 Testing heavy AI imports..."
python -c "
try:
    import torch
    print('✅ PyTorch imported successfully')
except Exception as e:
    print(f'⚠️ PyTorch import failed: {e}')

try:
    import transformers
    print('✅ Transformers imported successfully')
except Exception as e:
    print(f'⚠️ Transformers import failed: {e}')

try:
    import faiss
    print('✅ FAISS imported successfully')
except Exception as e:
    print(f'⚠️ FAISS import failed: {e}')
"

# Final startup attempt
echo "🚀 Starting application..."

# Try to start with multiple workers first
WORKERS="${UVICORN_WORKERS:-1}"
echo "🧵 Uvicorn workers: ${WORKERS}"

# Start the application with error handling
if uvicorn src.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --access-log \
    --log-level "${LOG_LEVEL}"; then
    echo "✅ Application started successfully"
else
    echo "⚠️ Multi-worker startup failed, trying single worker..."
    uvicorn src.main:app \
        --host "${HOST}" \
        --port "${PORT}" \
        --access-log \
        --log-level "${LOG_LEVEL}"
fi
EOF

RUN chmod +x /app/start.sh

EXPOSE 8080

CMD ["/app/start.sh"]

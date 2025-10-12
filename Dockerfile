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

# Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# NLTK data (moved to runtime to avoid build issues)
RUN mkdir -p /app/nltk_data

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
echo "🔍 Python path: $(python -c 'import sys; print(sys.path)')"
echo "🔍 Working directory: $(pwd)"
echo "🔍 Files in /app: $(ls -la /app)"

# Test imports
echo "🧪 Testing critical imports..."
python -c "
try:
    import fastapi
    print('✅ FastAPI imported successfully')
except Exception as e:
    print(f'❌ FastAPI import failed: {e}')

try:
    import pydantic_settings
    print('✅ Pydantic Settings imported successfully')
except Exception as e:
    print(f'❌ Pydantic Settings import failed: {e}')

try:
    import faiss
    print('✅ FAISS imported successfully')
except Exception as e:
    print(f'❌ FAISS import failed: {e}')

try:
    from src.core.config import settings
    print('✅ Config imported successfully')
except Exception as e:
    print(f'❌ Config import failed: {e}')
"

# Download NLTK data
echo "📚 Downloading NLTK data..."
python -c "
import os, nltk
d = os.environ.get('NLTK_DATA', '/app/nltk_data')
os.makedirs(d, exist_ok=True)
try:
    nltk.download('punkt', download_dir=d, quiet=True)
    nltk.download('stopwords', download_dir=d, quiet=True)
    print('✅ NLTK data downloaded successfully')
except Exception as e:
    print(f'⚠️ NLTK data download failed: {e}')
"

# Test application startup
echo "🧪 Testing application startup..."
python -c "
try:
    from src.main import app
    print('✅ FastAPI app created successfully')
except Exception as e:
    print(f'❌ FastAPI app creation failed: {e}')
    import traceback
    traceback.print_exc()
"

# Start with single worker for Cloud Run (more reliable)
echo "🚀 Starting application with single worker..."
exec uvicorn src.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --access-log \
    --log-level "${LOG_LEVEL}"
EOF

RUN chmod +x /app/start.sh

EXPOSE 8080

CMD ["/app/start.sh"]

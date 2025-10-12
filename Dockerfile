# =============================================================================
# BLOOCUBE AI SERVICES - OPTIMIZED DOCKERFILE FOR GCP CLOUD RUN
# =============================================================================

# Multi-stage build for better optimization
FROM python:3.11-slim as builder

# Build arguments
ARG BUILDKIT_INLINE_CACHE=1
ARG PIP_NO_CACHE_DIR=1

# Environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    curl \
    wget \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir \
    --timeout=600 \
    --retries=3 \
    -r /tmp/requirements.txt

# Download NLTK data
RUN python -c "
import nltk
import os
nltk_data_dir = '/opt/venv/nltk_data'
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.download('punkt', download_dir=nltk_data_dir, quiet=True)
nltk.download('stopwords', download_dir=nltk_data_dir, quiet=True)
nltk.download('vader_lexicon', download_dir=nltk_data_dir, quiet=True)
"

# =============================================================================
# PRODUCTION STAGE
# =============================================================================
FROM python:3.11-slim as production

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV NLTK_DATA=/app/nltk_data
ENV NODE_ENV=production
ENV AI_SERVICE_PORT=8080
ENV AI_SERVICE_HOST=0.0.0.0
ENV PORT=8080

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    libffi8 \
    libssl3 \
    libxml2 \
    libxslt1.1 \
    zlib1g \
    libjpeg62-turbo \
    libpng16-16 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /bin/bash -c "App User" appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appgroup . .

# Create necessary directories
RUN mkdir -p logs data uploads temp nltk_data && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app

# Copy NLTK data from builder
COPY --from=builder --chown=appuser:appgroup /opt/venv/nltk_data /app/nltk_data

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/ping || exit 1

# Expose port
EXPOSE 8080

# Create startup script
RUN cat <<'EOF' > /app/start.sh
#!/bin/bash
set -euo pipefail

echo "🚀 Starting Bloocube AI Services..."
echo "📊 Environment: ${NODE_ENV:-production}"
echo "🐍 Python version: $(python --version)"
echo "📁 Working directory: $(pwd)"
echo "🔍 Python path: $(python -c 'import sys; print(sys.path)')"

# Set default values
: "${PORT:=8080}"
LOG_LEVEL="$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')"
HOST="${AI_SERVICE_HOST:-0.0.0.0}"

echo "🌐 Port: ${PORT}"
echo "🏠 Host: ${HOST}"
echo "🪵 Log level: ${LOG_LEVEL}"

# Test critical imports
echo "🧪 Testing critical imports..."
python -c "
import sys
import traceback

# Test FastAPI and core dependencies
try:
    import fastapi
    print('✅ FastAPI imported successfully')
except Exception as e:
    print(f'❌ FastAPI import failed: {e}')
    traceback.print_exc()
    sys.exit(1)

try:
    import uvicorn
    print('✅ Uvicorn imported successfully')
except Exception as e:
    print(f'❌ Uvicorn import failed: {e}')
    traceback.print_exc()
    sys.exit(1)

try:
    import pydantic
    print('✅ Pydantic imported successfully')
except Exception as e:
    print(f'❌ Pydantic import failed: {e}')
    traceback.print_exc()
    sys.exit(1)
"

# Test app creation
echo "🧪 Testing app creation..."
python -c "
import sys
import traceback

try:
    from src.main import app
    print('✅ FastAPI app created successfully')
    print(f'App type: {type(app)}')
except Exception as e:
    print(f'❌ App creation failed: {e}')
    traceback.print_exc()
    sys.exit(1)
"

# Test optional AI imports (non-critical)
echo "🧪 Testing optional AI imports..."
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

try:
    import langchain
    print('✅ LangChain imported successfully')
except Exception as e:
    print(f'⚠️ LangChain import failed: {e}')
"

# Start the application
echo "🚀 Starting application..."
WORKERS="${UVICORN_WORKERS:-1}"
echo "🧵 Uvicorn workers: ${WORKERS}"

# Use the main.py launcher for consistency
exec python main.py
EOF

RUN chmod +x /app/start.sh

# Use the startup script
CMD ["/app/start.sh"]
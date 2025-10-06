# =============================================================================
# BLOOCUBE AI SERVICES - PRODUCTION DOCKERFILE FOR GCP CLOUD RUN
# =============================================================================

# Use Python 3.11 slim image for better performance and security
FROM python:3.11-slim

# Set metadata
LABEL maintainer="Bloocube Team"
LABEL version="1.0.0"
LABEL description="Bloocube AI Services for GCP Cloud Run"

# Set working directory
WORKDIR /app

# Set environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV NLTK_DATA=/app/nltk_data

# Set default environment
ENV NODE_ENV=production
ENV AI_SERVICE_PORT=8080
ENV AI_SERVICE_HOST=0.0.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build essentials
    gcc \
    g++ \
    make \
    # Database drivers
    libpq-dev \
    # SSL and crypto
    libffi-dev \
    libssl-dev \
    # Utilities
    curl \
    wget \
    git \
    # Cleanup \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create application user for security
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /bin/bash -c "App User" appuser

# Copy requirements first for better Docker layer caching
COPY requirements.txt ./

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data (no heredoc; compatible with older Dockerfile parsers)
RUN python -c "import os, nltk; d=os.environ.get('NLTK_DATA','/app/nltk_data'); os.makedirs(d, exist_ok=True); nltk.download('punkt', download_dir=d, quiet=True); nltk.download('stopwords', download_dir=d, quiet=True)" || true

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p logs data uploads temp && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Create startup script (Cloud Run friendly)
RUN echo '#!/bin/bash
set -e

# Print startup info
echo "🚀 Starting Bloocube AI Services..."
echo "📊 Environment: ${NODE_ENV:-production}"
PORT_TO_USE=${PORT:-${AI_SERVICE_PORT:-8080}}
echo "🌐 Port: ${PORT_TO_USE}"
echo "🏠 Host: ${AI_SERVICE_HOST:-0.0.0.0}"

# Default workers (I/O bound) can be adjusted via UVICORN_WORKERS env
WORKERS=${UVICORN_WORKERS:-2}
echo "🧵 Uvicorn workers: ${WORKERS}"

# Start the application
exec uvicorn src.main:app \
    --host ${AI_SERVICE_HOST:-0.0.0.0} \
    --port ${PORT_TO_USE} \
    --workers ${WORKERS} \
    --access-log \
    --log-level ${LOG_LEVEL:-info}
' > /app/start.sh && chmod +x /app/start.sh

# Expose port (Cloud Run uses 8080 by default)
EXPOSE 8080

# Health check (Cloud Run uses PORT=8080)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Set the startup command
CMD ["/app/start.sh"]
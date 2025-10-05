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
    # Cleanup
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
    pip install --no-cache-dir -r requirements.txt && \
    python - <<'PY'
import nltk, os
data_dir = os.environ.get('NLTK_DATA', '/app/nltk_data')
os.makedirs(data_dir, exist_ok=True)
try:
    nltk.download('punkt', download_dir=data_dir, quiet=True)
    nltk.download('stopwords', download_dir=data_dir, quiet=True)
except Exception as e:
    print('NLTK download warning:', e)
PY

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p logs data uploads temp && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Create startup script (simple and Cloud Run friendly)
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Print startup info\n\
echo "🚀 Starting Bloocube AI Services..."\n\
echo "📊 Environment: ${NODE_ENV:-production}"\n\
PORT_TO_USE=${PORT:-${AI_SERVICE_PORT:-8080}}\n\
echo "🌐 Port: ${PORT_TO_USE}"\n\
echo "🏠 Host: ${AI_SERVICE_HOST:-0.0.0.0}"\n\
\n\
# Start the application (single process for simplicity on Cloud Run)\n\
exec uvicorn src.main:app \\\n    --host ${AI_SERVICE_HOST:-0.0.0.0} \\\n    --port ${PORT_TO_USE} \\\n    --access-log \\\n    --log-level ${LOG_LEVEL:-info}\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port (Cloud Run uses 8080 by default)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${AI_SERVICE_PORT:-8080}/health || exit 1

# Set the startup command
CMD ["/app/start.sh"]
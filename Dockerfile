# =============================================================================
# BLOOCUBE AI SERVICES - OPTIMIZED DOCKERFILE FOR GCP CLOUD RUN
# =============================================================================

# -----------------------------------------------------------------------------
# STAGE 1 - BUILDER
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Build arguments
ARG BUILDKIT_INLINE_CACHE=1
ARG PIP_NO_CACHE_DIR=1

# Environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first (for better caching)
COPY requirements.txt /tmp/requirements.txt

# Install dependencies (this layer will be cached if requirements.txt doesn't change)
RUN pip install --no-cache-dir --timeout=600 -r /tmp/requirements.txt

# Download required NLTK data (✅ fixed syntax)
RUN python -c "import nltk, os; d='/opt/venv/nltk_data'; os.makedirs(d, exist_ok=True); [nltk.download(x, download_dir=d, quiet=True) for x in ['punkt','stopwords','vader_lexicon']]"

# Download spaCy model
RUN python -c "import spacy; spacy.cli.download('en_core_web_sm')"

# -----------------------------------------------------------------------------
# STAGE 2 - PRODUCTION
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

# Environment setup
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    NLTK_DATA=/app/nltk_data \
    NODE_ENV=production \
    AI_SERVICE_PORT=8080 \
    AI_SERVICE_HOST=0.0.0.0 \
    PORT=8080

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy NLTK data first
COPY --from=builder --chown=appuser:appgroup /opt/venv/nltk_data /app/nltk_data

# Create necessary directories
RUN mkdir -p logs data uploads temp && \
    chown -R appuser:appgroup /app

# Copy only necessary application files (for better caching)
COPY --chown=appuser:appgroup requirements.txt ./
COPY --chown=appuser:appgroup main.py ./
COPY --chown=appuser:appgroup src/ ./src/

# Set final permissions
RUN chmod -R 755 /app

# Create a simple startup script as appuser
USER appuser
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'echo "🚀 Starting Bloocube AI Services..."' >> /app/start.sh && \
    echo 'exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}' >> /app/start.sh && \
    chmod +x /app/start.sh

# Health check (adjust if your app has a different endpoint)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/ping || exit 1

# Expose port
EXPOSE 8080

# -----------------------------------------------------------------------------
# START COMMAND
# -----------------------------------------------------------------------------
CMD ["/app/start.sh"]

# ─────────────────────────────────────────────────────────────
# AIU Backend — Production Dockerfile
# ─────────────────────────────────────────────────────────────

# FROM python:3.12-slim

# Python settings
# ENV PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1 \
#     PYTHONPATH=/app

# WORKDIR /app

# System deps
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     libpq-dev \
#     libffi-dev \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# # Install Python deps
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy project
# COPY . .

# # Create non-root user
# RUN groupadd --gid 1001 aiu && \
#     useradd --uid 1001 --gid aiu --no-create-home aiu && \
#     chown -R aiu:aiu /app

# USER aiu

# # Health check (simple & safe)
# HEALTHCHECK CMD curl -f http://localhost:$PORT/ || exit 1

# # Default command (ONLY start server)
# CMD ["gunicorn", "config.asgi:application", \
#      "-k", "uvicorn.workers.UvicornWorker", \
#      "--bind", "0.0.0.0:8000", \
#      "--workers", "2", \
#      "--timeout", "120"]
# ─────────────────────────────────────────────────────────────────────────────
#  AIU Backend — Dockerfile
#  Works with: Render, Railway, Docker Compose, VPS
#
#  NOTE: collectstatic runs at container START (not build time) so it has
#  access to real environment variables. Static files are served by WhiteNoise.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim AS runtime

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create non-root user for security
RUN groupadd --gid 1001 aiu && \
    useradd --uid 1001 --gid aiu --no-create-home aiu && \
    chown -R aiu:aiu /app

USER aiu

# Health check — uses the public /api/v1/health/ endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health/ || exit 1

# Startup: migrate → collectstatic → start gunicorn
# Using shell form so $PORT is expanded from environment
CMD python manage.py migrate --noinput && \
    python manage.py collectstatic --noinput --clear && \
    gunicorn \
        --worker-class uvicorn.workers.UvicornWorker \
        --workers ${GUNICORN_WORKERS:-2} \
        --bind 0.0.0.0:${PORT:-8000} \
        --timeout 120 \
        --keep-alive 5 \
        --log-level info \
        --access-logfile - \
        --error-logfile - \
        config.asgi:application   change it and give complet
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd --gid 1001 aiu && \
    useradd --uid 1001 --gid aiu --no-create-home aiu && \
    chown -R aiu:aiu /app

USER aiu

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health/ || exit 1

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
        config.asgi:application

# ─────────────────────────────────────────────────────────────────────────────
#  AIU — Makefile
#  Common development and operations commands.
#  Usage: make <target>
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help dev build test lint migrate shell logs clean reset

# Default target
help:
	@echo ""
	@echo "  AIU — Available Commands"
	@echo ""
	@echo "  Development:"
	@echo "    make dev          Start backend, frontend, postgres, and redis"
	@echo "    make dev-workers  Start worker and beat too"
	@echo "    make logs         Tail all service logs"
	@echo "    make shell        Open Django shell"
	@echo "    make migrate      Run database migrations"
	@echo "    make superuser    Create Django superuser"
	@echo ""
	@echo "  Testing:"
	@echo "    make test         Run all backend tests"
	@echo "    make test-cov     Run tests with HTML coverage report"
	@echo "    make lint         Run ruff + eslint + bandit"
	@echo ""
	@echo "  Cleanup:"
	@echo "    make clean        Remove containers and volumes"
	@echo "    make reset        Full reset (WARNING: deletes all data)"
	@echo ""

# ── Development ───────────────────────────────────────────────────────────────

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up backend frontend postgres redis

dev-d:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d backend frontend postgres redis

dev-workers:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile workers up worker beat

build:
	docker compose build

build-no-cache:
	docker compose build --no-cache

logs:
	docker compose logs -f --tail=100

logs-backend:
	docker compose logs backend worker -f --tail=100

shell:
	docker compose exec backend python manage.py shell_plus

migrate:
	docker compose exec backend python manage.py migrate --noinput

makemigrations:
	docker compose exec backend python manage.py makemigrations $(app)

superuser:
	docker compose exec backend python manage.py createsuperuser

collectstatic:
	docker compose exec backend python manage.py collectstatic --noinput

# ── Testing ───────────────────────────────────────────────────────────────────

test:
	docker compose exec backend pytest tests/ -v --tb=short

test-cov:
	docker compose exec backend pytest tests/ --cov=apps --cov-report=html --cov-report=term-missing
	@echo "Coverage report: backend/htmlcov/index.html"

test-fast:
	docker compose exec backend pytest tests/ -x --tb=short -q

# ── Linting ───────────────────────────────────────────────────────────────────

lint:
	@echo "→ Ruff (Python)..."
	docker compose exec backend ruff check apps/ config/
	@echo "→ Ruff format check..."
	docker compose exec backend ruff format --check apps/ config/
	@echo "→ Bandit security scan..."
	docker compose exec backend bandit -r apps/ -ll -ii
	@echo "→ ESLint (TypeScript)..."
	cd frontend && npm run lint
	@echo "✓ All lint checks passed"

lint-fix:
	docker compose exec backend ruff check --fix apps/ config/
	docker compose exec backend ruff format apps/ config/
	cd frontend && npm run lint -- --fix

# ── Database ──────────────────────────────────────────────────────────────────

db-shell:
	docker compose exec postgres psql -U aiu_user -d aiu_db

db-backup:
	@DATE=$$(date +%Y%m%d_%H%M%S); \
	docker compose exec -T postgres pg_dump -U aiu_user aiu_db \
	  | gzip > backups/db_$$DATE.sql.gz; \
	echo "Backup saved: backups/db_$$DATE.sql.gz"

db-restore:
	@echo "Usage: make db-restore FILE=backups/db_YYYYMMDD_HHMMSS.sql.gz"
	@if [ -z "$(FILE)" ]; then echo "ERROR: FILE not set"; exit 1; fi
	zcat $(FILE) | docker compose exec -T postgres psql -U aiu_user -d aiu_db

# ── Celery ────────────────────────────────────────────────────────────────────

worker-status:
	docker compose exec worker celery -A config.celery inspect active

beat-status:
	docker compose exec backend celery -A config.celery beat --loglevel=debug --dry-run

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	docker compose down --remove-orphans
	docker image prune -f

reset:
	@echo "⚠️  This will DELETE all containers, volumes, and data. Press Ctrl+C to cancel."
	@sleep 5
	docker compose down --volumes --remove-orphans
	docker image prune -af

# ── Frontend ──────────────────────────────────────────────────────────────────

frontend-install:
	cd frontend && npm ci

frontend-build:
	cd frontend && npm run build

frontend-dev:
	cd frontend && npm run dev

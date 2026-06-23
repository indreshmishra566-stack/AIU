# AIU — Complete Setup & Deployment Guide

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start — Local Development](#quick-start--local-development)
3. [Environment Configuration](#environment-configuration)
4. [Running the App](#running-the-app)
5. [Running Tests](#running-tests)
6. [Production Deployment](#production-deployment)
7. [CI/CD Setup](#cicd-setup)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Local Machine (required for all options)

| Tool | Version | Check |
|------|---------|-------|
| Docker | 24+ | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |
| Git | any | `git --version` |

> **Windows users:** Use WSL2 with Ubuntu 22.04.
> **Mac users:** Use Docker Desktop.

### Optional (for running without Docker)

| Tool | Version |
|------|---------|
| Python | 3.12+ |
| Node.js | 20+ |
| PostgreSQL | 16+ with pgvector extension |
| Redis | 7.2+ |

---

## Quick Start — Local Development

### Step 1 — Clone and configure

```bash
# Unzip the project
unzip aiu_v2_complete.zip
cd aiu

# Copy environment template
cp .env.example .env
```

### Step 2 — Generate secrets

```bash
# Generate Django secret key
python3 -c "import secrets; print('DJANGO_SECRET_KEY=' + secrets.token_urlsafe(50))"

# Generate JWT signing key
python3 -c "import secrets; print('JWT_SIGNING_KEY=' + secrets.token_urlsafe(50))"

# Generate field encryption key (requires cryptography library)
pip install cryptography --quiet
python3 -c "from cryptography.fernet import Fernet; print('FIELD_ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

Copy each output value into `.env`.

### Step 3 — Edit .env (minimum required)

Open `.env` and set these values — everything else can stay as default for local dev:

```env
# Generate with commands above ↑
DJANGO_SECRET_KEY=your-generated-secret-key-here
JWT_SIGNING_KEY=your-generated-jwt-key-here
FIELD_ENCRYPTION_KEY=your-generated-fernet-key-here

# Your OpenAI or Anthropic key (at least one required)
OPENAI_API_KEY=sk-proj-...
# ANTHROPIC_API_KEY=sk-ant-...  (optional alternative)

# Database passwords (used by docker-compose)
POSTGRES_PASSWORD=choose-a-strong-password
REDIS_PASSWORD=choose-a-redis-password
GRAFANA_PASSWORD=choose-a-grafana-password

# These stay as-is for local development
DATABASE_URL=postgresql://aiu_user:${POSTGRES_PASSWORD}@postgres:5432/aiu_db
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/2
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Step 4 — Start everything

```bash
# Start the local Docker stack
docker compose up
```

On first run this will:
- Pull Docker images (~2 minutes)
- Build your app containers (~3 minutes)
- Start all services

### Step 5 — Initialize the database

Open a second terminal while the containers are running:

```bash
# Run database migrations
docker compose exec backend python manage.py migrate

# Create your admin account
docker compose exec backend python manage.py createsuperuser
# Enter email, first name, last name, password when prompted
```

### Step 6 — Open the app

| URL | What |
|-----|------|
| http://localhost:5173 | Frontend (React + Vite HMR) |
| http://localhost:8000/api/docs/ | API docs (Swagger UI) |
| http://localhost:8000/admin/ | Django admin |
| http://localhost:9090 | Prometheus metrics |
| http://localhost:3001 | Grafana dashboards |

---

## Environment Configuration

### Minimum required variables

```env
DJANGO_SECRET_KEY          # 50+ random chars — NEVER share or commit
JWT_SIGNING_KEY            # 50+ random chars — separate from secret key
FIELD_ENCRYPTION_KEY       # Fernet base64 key — encrypts sensitive DB fields
OPENAI_API_KEY             # OpenAI API key (or set ANTHROPIC_API_KEY instead)
POSTGRES_PASSWORD          # PostgreSQL password
REDIS_PASSWORD             # Redis password
```

### AI Provider

AIU supports OpenAI and Anthropic. Set one:

```env
# Option A: OpenAI (recommended)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
LLM_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=sk-proj-...

# Option B: Anthropic Claude
LLM_PROVIDER=anthropic
LLM_MODEL=claude-opus-4-5
ANTHROPIC_API_KEY=sk-ant-...
```

### Variable reference

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DJANGO_SECRET_KEY` | — | ✅ | Django cryptographic secret |
| `JWT_SIGNING_KEY` | — | ✅ | JWT token signing key |
| `FIELD_ENCRYPTION_KEY` | — | ✅ | AES field encryption key |
| `DATABASE_URL` | — | ✅ | PostgreSQL connection string |
| `REDIS_URL` | — | ✅ | Redis connection string |
| `OPENAI_API_KEY` | — | ✅* | *One AI provider required |
| `ANTHROPIC_API_KEY` | — | ✅* | *One AI provider required |
| `LLM_PROVIDER` | `openai` | | `openai` or `anthropic` |
| `LLM_MODEL` | `gpt-4o` | | Model name |
| `DJANGO_DEBUG` | `False` | | `True` for dev only |
| `DJANGO_ALLOWED_HOSTS` | — | ✅ prod | Comma-separated domains |
| `CORS_ALLOWED_ORIGINS` | — | ✅ prod | Comma-separated origins |
| `AWS_ACCESS_KEY_ID` | — | prod | S3 file storage |
| `SENTRY_DSN` | — | prod | Error tracking |
| `DOMAIN` | — | prod | Your domain name |

---

## Running the App

### Local Docker mode

```bash
# Start everything
docker compose up

# Or in background
docker compose up -d

# View logs
docker compose logs -f --tail=50

# Stop
docker compose down
```

**What runs in dev mode:**
- Backend: Django runserver on port 8000 (auto-reloads on Python file changes)
- Frontend: Vite dev server on port 5173 (HMR — instant React updates)
- Worker: Single-threaded Celery (easier to debug)
- Postgres, Redis, Prometheus, Grafana: same as production

### Using Makefile shortcuts

```bash
make dev          # Start dev stack
make logs         # Tail all logs
make migrate      # Run migrations
make shell        # Django shell
make test         # Run all tests
make lint         # Run all linters
make superuser    # Create admin user
make db-shell     # PostgreSQL shell
make clean        # Remove containers
```

### Without Docker (bare metal)

**Backend:**
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Set environment
export DJANGO_SETTINGS_MODULE=config.settings.development
export DJANGO_SECRET_KEY=your-key
export JWT_SIGNING_KEY=your-jwt-key
export FIELD_ENCRYPTION_KEY=your-fernet-key
export DATABASE_URL=postgresql://user:password@localhost:5432/aiu_db
export REDIS_URL=redis://localhost:6379/0
export OPENAI_API_KEY=sk-...

# Run migrations
python manage.py migrate

# Start dev server
python manage.py runserver 0.0.0.0:8000
```

**Celery worker (new terminal):**
```bash
cd backend
source venv/bin/activate
celery -A config.celery worker --loglevel=info --pool=solo
```

**Celery beat (new terminal):**
```bash
cd backend
source venv/bin/activate
celery -A config.celery beat --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## Running Tests

### All tests

```bash
docker compose exec backend pytest tests/ -v
```

### Specific test files

```bash
# Test the Goals module
docker compose exec backend pytest tests/test_goals.py -v

# Test the AI engine
docker compose exec backend pytest tests/test_ai_engine.py -v

# Test authentication + core API
docker compose exec backend pytest tests/test_api.py -v

# Test memory system
docker compose exec backend pytest tests/test_memory.py -v

# Test habits, analytics, recommendations
docker compose exec backend pytest tests/test_habits_analytics_recs.py -v
```

### With coverage report

```bash
docker compose exec backend pytest tests/ \
  --cov=apps \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=70

# View HTML report (opens in browser)
open backend/htmlcov/index.html
```

### Frontend tests

```bash
cd frontend
npm test
# or
npm test -- --coverage --watchAll=false
```

### Lint checks

```bash
# All linters at once
make lint

# Or individually:
docker compose exec backend ruff check apps/ config/
docker compose exec backend ruff format --check apps/ config/
docker compose exec backend bandit -r apps/ -ll
cd frontend && npm run lint
```

---

## Production Deployment

### Server requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 GB | 8 GB |
| Disk | 40 GB SSD | 80 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Open ports | 80, 443, 22 | 80, 443, 22 |

Good providers: DigitalOcean, Hetzner, Linode, AWS EC2, GCP Compute Engine.

---

### Step 1 — Provision the server

```bash
# SSH into your new server
ssh root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh

# Add your user to docker group (if not root)
usermod -aG docker $USER
newgrp docker

# Verify
docker --version        # Docker 24+
docker compose version  # Docker Compose v2+
```

---

### Step 2 — Install the project

```bash
# Create app directory
mkdir -p /opt/aiu
cd /opt/aiu

# Upload your project files (from your local machine):
# Option A: scp
scp aiu_v2_complete.zip root@YOUR_SERVER_IP:/opt/aiu/
unzip aiu_v2_complete.zip
mv aiu/* .

# Option B: git (if you pushed to GitHub)
git clone https://github.com/YOUR_ORG/aiu.git .
```

---

### Step 3 — Configure environment

```bash
cd /opt/aiu
cp .env.example .env
nano .env  # or: vim .env
```

**Critical production settings:**

```env
# ── Core (generate these values) ─────────────────────────────────────────────
DJANGO_SECRET_KEY=<50+ random chars>
JWT_SIGNING_KEY=<50+ random chars>
FIELD_ENCRYPTION_KEY=<Fernet base64 key>

# ── AI ────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-proj-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o

# ── Database ──────────────────────────────────────────────────────────────────
POSTGRES_PASSWORD=<very-strong-password-30-chars>
DATABASE_URL=postgresql://aiu_user:${POSTGRES_PASSWORD}@postgres:5432/aiu_db

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_PASSWORD=<strong-redis-password>
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/1
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/2

# ── Domain ────────────────────────────────────────────────────────────────────
DOMAIN=yourdomain.com
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
VITE_API_BASE_URL=https://yourdomain.com/api/v1
VITE_WS_BASE_URL=wss://yourdomain.com

# ── Django ────────────────────────────────────────────────────────────────────
DJANGO_DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production

# ── Monitoring (optional but recommended) ────────────────────────────────────
SENTRY_DSN=https://...@sentry.io/...
GRAFANA_PASSWORD=<strong-grafana-password>
```

**Protect .env:**
```bash
chmod 600 /opt/aiu/.env
```

---

### Step 4 — Set up SSL certificate

```bash
# Install certbot
apt install certbot -y

# Point your domain's A record to the server IP first, then:
certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com \
  --email you@example.com \
  --agree-tos \
  --non-interactive

# Certificates saved at:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

**Update nginx.conf** — replace `yourdomain.com` with your actual domain:

```bash
sed -i 's/yourdomain.com/YOURACTUAL.DOMAIN/g' /opt/aiu/infra/nginx/nginx.conf
```

---

### Step 5 — Build and start

```bash
cd /opt/aiu

# Build all Docker images
docker compose build

# Start database and cache first
docker compose up -d postgres redis

# Wait for them to be healthy
docker compose ps  # wait until Status = healthy (30-60 seconds)

# Run database migrations
docker compose run --rm backend python manage.py migrate --noinput

# Collect static files
docker compose run --rm backend python manage.py collectstatic --noinput

# Create admin superuser
docker compose run --rm backend python manage.py createsuperuser

# Start everything
docker compose up -d

# Verify all containers are running
docker compose ps
```

Expected output:
```
NAME                STATUS          PORTS
aiu-postgres-1      Up (healthy)    5432/tcp
aiu-redis-1         Up (healthy)    6379/tcp
aiu-backend-1       Up (healthy)    8000/tcp
aiu-worker-1        Up              -
aiu-beat-1          Up              -
aiu-frontend-1      Up              3000/tcp
aiu-nginx-1         Up              0.0.0.0:80->80, 0.0.0.0:443->443
aiu-prometheus-1    Up              9090/tcp
aiu-grafana-1       Up              3000/tcp
```

---

### Step 6 — Verify deployment

```bash
# Test HTTPS
curl -I https://yourdomain.com

# Test API
curl https://yourdomain.com/api/v1/auth/register/ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"TestPassword123!","first_name":"Test","last_name":"User"}'

# Should return HTTP 201 with tokens
```

---

### Step 7 — Set up automatic backups

```bash
mkdir -p /opt/backups/aiu

cat > /opt/aiu/scripts/backup.sh << 'SCRIPT'
#!/bin/bash
set -e
DATE=$(date +%Y%m%d_%H%M%S)
DIR=/opt/backups/aiu

# Database backup
docker compose -f /opt/aiu/docker-compose.yml exec -T postgres \
  pg_dump -U aiu_user aiu_db | gzip > $DIR/db_$DATE.sql.gz

# Keep only last 30 days
find $DIR -name "*.sql.gz" -mtime +30 -delete

echo "[$(date)] Backup complete: db_$DATE.sql.gz"
SCRIPT

chmod +x /opt/aiu/scripts/backup.sh

# Schedule daily at 2am
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/aiu/scripts/backup.sh >> /var/log/aiu-backup.log 2>&1") | crontab -
```

---

### Step 8 — Set up SSL auto-renewal

```bash
# Add to crontab — renews at noon daily, reloads nginx if renewed
(crontab -l 2>/dev/null; echo "0 12 * * * certbot renew --quiet && docker compose -f /opt/aiu/docker-compose.yml exec nginx nginx -s reload 2>/dev/null || true") | crontab -
```

---

### Step 9 — Set up Celery periodic tasks

```bash
# Load beat schedule into the database
docker compose exec backend python manage.py shell << 'PYTHON'
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json

tasks = [
    {
        "name": "Daily AI Recommendations",
        "task": "ai_engine.generate_daily_recommendations",
        "cron": {"hour": 7, "minute": 0},
    },
    {
        "name": "Daily Snapshots",
        "task": "ai_engine.create_daily_snapshots",
        "cron": {"hour": 0, "minute": 5},
    },
    {
        "name": "Purge Old Behavior Events",
        "task": "ai_engine.purge_old_behavior_events",
        "cron": {"hour": 2, "minute": 0},
    },
    {
        "name": "Weekly Behavior Analysis",
        "task": "ai_engine.run_weekly_behavior_analysis",
        "cron": {"day_of_week": 1, "hour": 3, "minute": 0},
    },
]

for t in tasks:
    schedule, _ = CrontabSchedule.objects.get_or_create(**t["cron"])
    obj, created = PeriodicTask.objects.get_or_create(
        name=t["name"],
        defaults={"crontab": schedule, "task": t["task"], "args": json.dumps([])},
    )
    print(f"{'Created' if created else 'Exists'}: {t['name']}")
PYTHON
```

---

### Step 10 — Configure Grafana

1. Open `https://yourdomain.com/grafana/` (internal route)
2. Login with `admin` / `GRAFANA_PASSWORD`
3. Prometheus datasource is auto-configured
4. Import recommended dashboards:
   - Django: **9628**
   - Redis: **763**
   - PostgreSQL: **9628**
   - Celery: **4926**

---

## CI/CD Setup

### GitHub Actions (included)

The pipeline is at `.github/workflows/ci-cd.yml` and runs automatically on push to `main`.

**Add these secrets to GitHub** (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `DEPLOY_HOST` | Your server IP or hostname |
| `DEPLOY_USER` | SSH username (e.g. `root` or `ubuntu`) |
| `DEPLOY_SSH_KEY` | Contents of `~/.ssh/id_rsa` (private key) |
| `VITE_API_BASE_URL` | `https://yourdomain.com/api/v1` |
| `SLACK_WEBHOOK` | Slack webhook URL (optional) |

**Generate and add deploy SSH key:**

```bash
# On your local machine
ssh-keygen -t ed25519 -f ~/.ssh/aiu_deploy -N ""

# Add public key to server
ssh-copy-id -i ~/.ssh/aiu_deploy.pub root@YOUR_SERVER_IP

# Add private key to GitHub
cat ~/.ssh/aiu_deploy  # copy this into DEPLOY_SSH_KEY secret
```

**Pipeline stages:**

```
push to main
    │
    ├── lint-backend  (ruff + bandit)
    ├── lint-frontend (eslint + tsc)
    │
    ├── test-backend  (pytest + postgres + redis)
    ├── test-frontend (vitest)
    │
    ├── build         (Docker → ghcr.io)
    │
    └── deploy        (SSH → zero-downtime rolling restart)
```

**Zero-downtime deploy process:**
1. Pulls new images
2. Scales backend to 2 instances
3. Waits 15 seconds (new instance starts)
4. Scales back to 1 (old instance stops)
5. Restarts worker and beat
6. Runs migrations
7. Prunes old images

---

## Monitoring

### Prometheus metrics

Available at `http://YOUR_SERVER:9090` (internal only — not exposed to internet).

Key metrics collected:
- `django_http_requests_total` — request count by path + status
- `django_http_request_duration_seconds` — latency histogram
- `celery_tasks_total` — task count by name + state
- `redis_connected_clients` — Redis connections
- `pg_up` — PostgreSQL health

### Grafana dashboards

Access at `http://YOUR_SERVER:3001` (internal only).

### Health check endpoint

```bash
# Check all services
curl http://localhost:8000/metrics  # returns 200 if healthy
```

### Log viewing

```bash
# All services
docker compose logs -f

# Just backend
docker compose logs backend -f --tail=100

# Just Celery worker (shows AI task processing)
docker compose logs worker -f --tail=50

# Filter for errors only
docker compose logs backend 2>&1 | grep "ERROR"

# Structured JSON logs (pipe to jq)
docker compose logs backend 2>&1 | grep "^{" | jq '.message'
```

---

## Troubleshooting

### "docker compose: command not found"
```bash
# Install Docker Compose plugin
apt install docker-compose-plugin -y
# Or use older syntax: docker-compose (with hyphen)
```

### Migrations fail on first run
```bash
# Ensure PostgreSQL is healthy first
docker compose ps postgres  # should show "Up (healthy)"

# Check postgres logs
docker compose logs postgres

# Try again
docker compose run --rm backend python manage.py migrate
```

### "pgvector extension not found"
The project uses `pgvector/pgvector:pg16` image which includes pgvector. If using your own Postgres:
```sql
-- Connect to database and run:
CREATE EXTENSION IF NOT EXISTS vector;
```

### Backend returns 500 on API calls
```bash
# Check backend logs for the traceback
docker compose logs backend --tail=100

# Run Django checks
docker compose exec backend python manage.py check

# Verify environment variables are loaded
docker compose exec backend python manage.py shell -c "from django.conf import settings; print(settings.DEBUG)"
```

### Celery tasks not running
```bash
# Check worker is running
docker compose ps worker

# Test with a simple task
docker compose exec backend python manage.py shell << 'EOF'
from config.celery import debug_task
result = debug_task.delay()
print(result.get(timeout=5))
EOF

# Check Redis connection
docker compose exec redis redis-cli -a $REDIS_PASSWORD ping
# Should return: PONG
```

### AI responses not working
```bash
# Verify API key is set correctly
docker compose exec backend python manage.py shell -c "
from django.conf import settings
key = settings.AI_ENGINE.get('OPENAI_API_KEY', '')
print('Key set:', bool(key), '| Starts with:', key[:8] if key else 'EMPTY')
"

# Test API key directly
docker compose exec backend python3 -c "
import openai, os
client = openai.OpenAI(api_key='$(grep OPENAI_API_KEY /opt/aiu/.env | cut -d= -f2)')
resp = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': 'Say OK'}],
    max_tokens=5,
)
print(resp.choices[0].message.content)
"
```

### Frontend shows blank page
```bash
# Check for JS build errors
docker compose logs frontend

# Rebuild frontend
docker compose build frontend
docker compose up -d frontend
```

### "Address already in use" on port 80/443
```bash
# Find what's using the port
lsof -i :80

# If it's nginx (system):
systemctl stop nginx
systemctl disable nginx

# Then restart docker
docker compose up -d nginx
```

### SSL certificate errors
```bash
# Check certificate exists
ls /etc/letsencrypt/live/yourdomain.com/

# Check certificate expiry
certbot certificates

# Force renewal
certbot renew --force-renewal
docker compose exec nginx nginx -s reload
```

### Database connection refused
```bash
# Check postgres is healthy
docker compose exec postgres pg_isready -U aiu_user -d aiu_db

# Check the DATABASE_URL in .env matches the postgres service
# It should be: postgresql://aiu_user:PASSWORD@postgres:5432/aiu_db
# Note: hostname is "postgres" (the docker service name), not "localhost"
```

### Reset everything (⚠️ deletes all data)

```bash
# Stop and remove all containers + volumes
docker compose down --volumes --remove-orphans

# Remove images
docker image prune -af

# Start fresh
docker compose up -d
docker compose run --rm backend python manage.py migrate
docker compose run --rm backend python manage.py createsuperuser
```

---

## Quick Reference

```bash
# ── Most used commands ───────────────────────────────────────────────────────
make dev              # Start local Docker stack
make logs             # Tail all logs
make migrate          # Run database migrations
make test             # Run all backend tests
make shell            # Open Django interactive shell
make superuser        # Create admin user
make lint             # Run all linters
make deploy           # Zero-downtime production deploy
make db-backup        # Backup database
make clean            # Remove all containers

# ── Direct docker commands ───────────────────────────────────────────────────
docker compose ps                          # List all services + health
docker compose logs backend -f             # Stream backend logs
docker compose exec backend bash           # Shell into backend container
docker compose exec postgres psql -U aiu_user -d aiu_db  # DB shell
docker compose restart backend             # Restart one service
docker compose pull && docker compose up -d  # Update to latest images
```

---

## Support

- **API docs:** `https://yourdomain.com/api/docs/`
- **Admin panel:** `https://yourdomain.com/admin/`
- **Health check:** `https://yourdomain.com/metrics`

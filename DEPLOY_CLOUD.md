# Deploy AIU

This repo is prepared for:

- GitHub as the source repository
- Render for the Django backend, Postgres, Redis-compatible Key Value, Celery worker, and Celery beat
- Vercel for the frontend

## Backend on Render

1. Push the repo to GitHub.
2. In Render, create a new Blueprint.
3. Point it at this repo.
4. Render will read `render.yaml` and create:
   - `aiu-postgres`
   - `aiu-redis`
   - `aiu-backend`
   - `aiu-worker`
   - `aiu-beat`
5. Fill in the required secret env vars:

```text
FIELD_ENCRYPTION_KEY=...
GROQ_API_KEY=...
CORS_ALLOWED_ORIGINS=https://YOUR-FRONTEND.vercel.app
```

## Frontend on Vercel

1. Import the same repo into Vercel.
2. Set the root directory to `frontend`.
3. Add:

```text
VITE_API_BASE_URL=https://YOUR-RENDER-BACKEND.onrender.com/api/v1
VITE_WS_BASE_URL=wss://YOUR-RENDER-BACKEND.onrender.com
```

4. Deploy.

## Local run

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up backend frontend postgres redis
```

Backend:

```text
http://localhost:8000
```

Frontend:

```text
http://localhost:5173
```

# AIU

AIU is a monorepo with:

- `backend/`: Django API and Celery services
- `frontend/`: Vite + React app
- `render.yaml`: Render blueprint for backend infrastructure
- `frontend/vercel.json`: Vercel config for the frontend SPA

## Recommended deployment path

This repo is set up for:

1. GitHub for source control
2. Render for backend, Postgres, Redis-compatible Key Value, worker, and beat
3. Vercel for the frontend

## 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/aiu.git
git push -u origin main
```

## 2. Deploy backend on Render

Render docs: https://render.com/docs/blueprint-spec

1. In Render, choose `New` → `Blueprint`.
2. Connect your GitHub repo.
3. Render will detect [render.yaml](/home/imim/Downloads/aiu/render.yaml).
4. Create the stack.
5. When prompted for secrets, set:

```text
FIELD_ENCRYPTION_KEY=...
GROQ_API_KEY=...
CORS_ALLOWED_ORIGINS=https://YOUR-FRONTEND.vercel.app
```

6. After the backend web service is live, copy its public URL, for example:

```text
https://aiu-backend.onrender.com
```

## 3. Deploy frontend on Vercel

Vercel Vite docs: https://vercel.com/docs/frameworks/frontend/vite

1. In Vercel, import the same GitHub repo.
2. Set the project root directory to `frontend`.
3. Add these environment variables in Vercel:

```text
VITE_API_BASE_URL=https://YOUR-RENDER-BACKEND.onrender.com/api/v1
VITE_WS_BASE_URL=wss://YOUR-RENDER-BACKEND.onrender.com
```

4. Deploy.

## 4. Update backend CORS

After Vercel gives you your frontend domain, update Render:

```text
CORS_ALLOWED_ORIGINS=https://YOUR-PROJECT.vercel.app
```

If you add a custom domain later, include that too as a comma-separated list.

## Local development

### Docker-first

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up backend frontend postgres redis
```

### Python + Vite

1. Copy `.env.example` to `.env`.
2. Install backend dependencies into `.venv`.
3. Install frontend dependencies in `frontend/`.
4. Start backend and frontend separately.

## Notes

- Render background workers are not on the `free` instance type in current Render docs, so the blueprint does not force `free` plans for workers.
- Render now documents `keyvalue` as the preferred Redis-compatible service type, so the blueprint uses that instead of the deprecated `redis` alias.
- The frontend is no longer defined in `render.yaml`, because this repo is now set up for Vercel on the frontend side.

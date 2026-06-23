# ─────────────────────────────────────────────────────────────────────────────
#  AIU Frontend — Multi-stage Dockerfile
#  Stage 1: builder  — Vite build
#  Stage 2: runtime  — Nginx serving static files
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

ARG VITE_API_BASE_URL
ARG VITE_WS_BASE_URL

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_WS_BASE_URL=$VITE_WS_BASE_URL

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --silent

COPY . .
RUN npm run build


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM nginx:1.25-alpine AS runtime

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# SPA routing: all paths serve index.html
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]

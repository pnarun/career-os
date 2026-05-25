# Career OS — Production Infrastructure (Phase 13)

Production-oriented deployment assets for Career OS. Does **not** replace application logic — only infrastructure.

## Structure

```text
infra/
├── docker/           # Compose overlays (local, staging, production)
├── nginx/            # Reverse proxy + WebSocket + static caching
├── scripts/          # Bootstrap and dev helpers
├── monitoring/       # Health check scripts
├── backups/          # MongoDB backup scripts
├── ci_cd/            # GitHub Actions workflow
└── deployment/       # Deploy scripts
```

## Quick start (local)

```bash
# From repo root
cp backend/.env.development backend/.env
docker compose -f docker-compose.yml -f infra/docker/docker-compose.local.yml up -d
```

Services:
- **frontend** — nginx serving Vite build
- **backend-api** — FastAPI
- **worker-engine** — Celery worker (scans, email, AI, analytics)
- **scheduler** — Celery beat
- **redis** — cache, queues, rate limits
- **nginx** — reverse proxy (optional profile)

## Environment files

| File | Purpose |
|------|---------|
| `backend/.env.development` | Local dev |
| `backend/.env.staging` | Staging template |
| `backend/.env.production` | Production template |

Set `ENVIRONMENT=development|staging|production` to load the matching file.

## Health endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness |
| `GET /system/status` | Component health (Mongo, Redis, queue, WS) |
| `GET /system/metrics` | Counters and uptime |

## Enable background queues

```env
REDIS_ENABLED=true
CELERY_ENABLED=true
QUEUE_SCANS_ENABLED=true
```

Manual scans return `{ "status": "queued", "task_id": "..." }` when queue mode is on.

## Worker commands

```bash
celery -A app.core.celery_app:celery_app worker -Q scans,email,ai,analytics,maintenance,default -l info
celery -A app.core.celery_app:celery_app beat -l info
```

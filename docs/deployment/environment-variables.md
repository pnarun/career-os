# Environment variables

## Overview

| Where | What belongs |
|-------|----------------|
| **Render (backend)** | Secrets, DB, JWT, AI keys, CORS |
| **Vercel (frontend)** | Public API URLs only (`VITE_*`) |
| **Never on Vercel** | `JWT_SECRET_KEY`, `MONGO_URI`, API provider secrets |

Frontend and backend do **not** share secret values — they share **URLs** only.

## Backend (`backend/.env.example`)

### Core

| Variable | Example | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `production` | `development` \| `staging` \| `production` |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `MONGO_URI` | `mongodb+srv://...` | Atlas connection string |

### Auth

| Variable | Description |
|----------|-------------|
| `JWT_SECRET_KEY` | Sign access/refresh tokens — **keep stable** |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Default 30 |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Default 7 |
| `AUTH_DEV_EXPOSE_OTP` | `false` in production |
| `AUTH_SEED_DEMO_USERS` | `false` in production |

### CORS / frontend

| Variable | Description |
|----------|-------------|
| `FRONTEND_URL` | Primary Vercel URL (merged into CORS) |
| `CORS_ORIGINS` | JSON array of allowed origins |
| `CORS_ORIGIN_REGEX` | e.g. `https://.*\.vercel\.app` |

### Infrastructure

| Variable | Default (Render blueprint) | Description |
|----------|---------------------------|-------------|
| `REDIS_ENABLED` | `false` | Enable Redis client |
| `REDIS_URL` | `redis://localhost:6379/0` | Auto-disabled if localhost on cloud |
| `CELERY_ENABLED` | `false` | Background workers |
| `QUEUE_SCANS_ENABLED` | `false` | Queue scans to Celery |
| `RATE_LIMIT_ENABLED` | `true` | Redis rate limiting |

### AI & communications

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini |
| `RESEND_API_KEY` | Email delivery |
| `RESEND_FROM_EMAIL` | Verified sender |
| `CLOUDINARY_CLOUD_NAME` | Resume storage |
| `CLOUDINARY_API_KEY` | |
| `CLOUDINARY_API_SECRET` | |

### Playwright

| Variable | Description |
|----------|-------------|
| `PLAYWRIGHT_HEADLESS` | `true` on Render |
| `PLAYWRIGHT_VIEWPORT_WIDTH` | 1280 |
| `PLAYWRIGHT_VIEWPORT_HEIGHT` | 720 |
| `PLAYWRIGHT_DEFAULT_TIMEOUT_MS` | 30000 |

### Scheduler & ops

| Variable | Description |
|----------|-------------|
| `SCHEDULER_HEARTBEAT_ENABLED` | 30-min scheduler log |
| `SCHEDULER_STARTUP_CATCHUP` | Overdue scans on boot |
| `CRON_SECRET` | Header for `/internal/cron/scheduled-scans` |
| `HEALTH_CACHE_SECONDS` | `/health` payload cache TTL |

### Feature flags

| Variable | Description |
|----------|-------------|
| `ASSISTED_APPLY_ENABLED` | Auto-apply features |
| `INTERVIEW_WEB_QUESTIONS_ENABLED` | Web question cache |

### Legacy / migration

| Variable | Description |
|----------|-------------|
| `LEGACY_MIGRATION_EMAIL` | Orphan data assignment |
| `LEGACY_MIGRATION_PASSWORD` | |

### Google OAuth (stub)

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Not wired to routes yet |
| `GOOGLE_CLIENT_SECRET` | |
| `GOOGLE_OAUTH_REDIRECT_URI` | |

## Frontend (`frontend/.env.example`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | **Yes in prod** | `https://api.onrender.com` — must be **https** |
| `VITE_WS_BASE_URL` | Optional | `wss://api.onrender.com` |
| `VITE_ASSISTED_APPLY_ENABLED` | Optional | `"true"` to enable UI |

## Render auto-fix

`config.py` disables `REDIS_ENABLED` when `REDIS_URL` points to localhost on cloud (`RENDER` env detected).

## Related

- [Deployment guide](./render-vercel-deployment.md)
- [Security model](../security/security-model.md)

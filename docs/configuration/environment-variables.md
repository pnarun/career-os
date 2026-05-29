# Environment variables reference

Complete reference for distributed Career OS. Defaults shown are code defaults unless noted.

**Legend:** **API** = career-os · **SW** = scan-worker · **AW** = automation

## Runtime mode

| Variable | Purpose | Values | Services | Default |
|----------|---------|--------|----------|---------|
| `SERVICE_MODE` | Process role | `api`, `scan_worker`, `automation_worker` | All | `api` |
| `SCAN_EXECUTION_MODE` | Scan routing | `inline`, `dispatch` | All | `inline` |
| `ENVIRONMENT` | Profile | `development`, `staging`, `production` | All | `development` |
| `LOG_LEVEL` | Logging | `DEBUG`, `INFO`, ... | All | `INFO` |

### Warnings

| Variable | Warning |
|----------|---------|
| `SCAN_EXECUTION_MODE=inline` on API in prod | API OOM risk |
| `SERVICE_MODE` mismatch with start script | Wrong scheduler/bridge behavior |

## Feature flags

| Variable | Purpose | API prod | SW prod | AW | Default |
|----------|---------|----------|---------|-----|---------|
| `ENABLE_SCHEDULER` | APScheduler | `false` | `true` | `false` | `true` |
| `ENABLE_REALTIME` | WebSocket stack | `true` | `false` | `false` | `true` |
| `ENABLE_PLAYWRIGHT` | Browser automation | `true` | `true` | `true` | `true` |
| `ENABLE_AUTOMATION` | Automation shutdown hooks | `true` | `false` | `true` | `true` |
| `SCHEDULER_STARTUP_CATCHUP` | Overdue scans on boot | optional | `false` | — | `true` |

## Realtime bridge (API only)

| Variable | Purpose | Default |
|----------|---------|---------|
| `REALTIME_BRIDGE_ENABLED` | Mongo → WS loop | `true` |
| `REALTIME_BRIDGE_POLL_SECONDS` | Poll interval | `1.5` |
| `REALTIME_BRIDGE_BATCH_SIZE` | Events per tick | `32` |

## Scan worker

| Variable | Purpose | Default |
|----------|---------|---------|
| `SCAN_WORKER_POLL_SECONDS` | Queue poll | `8` |
| `SCAN_WORKER_MAX_CONCURRENT` | Parallel scans | `1` |
| `SCAN_WORKER_HEARTBEAT_SECONDS` | Idle log interval | `60` |
| `SCAN_TASK_CLAIM_TIMEOUT_SECONDS` | Stale claim reclaim | `300` |
| `SCAN_TASK_EXECUTION_TIMEOUT_SECONDS` | Stale run abandon | `7200` |
| `SCAN_STALE_SECONDS` | API marks stuck scans failed | `7200` |

## Queue / Celery (partial — off in prod)

| Variable | Purpose | Prod typical | Default |
|----------|---------|--------------|---------|
| `CELERY_ENABLED` | Celery workers | `false` | `false` |
| `QUEUE_SCANS_ENABLED` | Celery scan tasks | `false` | `false` |
| `REDIS_ENABLED` | Local Redis client | `false` | `true` |
| `REDIS_URL` | Redis connection | — | `redis://localhost:6379/0` |

## MongoDB

| Variable | Required | Services |
|----------|----------|----------|
| `MONGO_URI` | **Yes** | All backend |

## Upstash (optional cache)

| Variable | Purpose |
|----------|---------|
| `UPSTASH_REDIS_REST_URL` | REST cache |
| `UPSTASH_REDIS_REST_TOKEN` | REST auth |
| `CACHE_RESPONSE_TTL` | Dashboard cache seconds |

## Auth

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET_KEY` | **Required** API — stable across deploys |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Default 30 |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Default 7 |
| `AUTH_DEV_EXPOSE_OTP` | **Never true in prod** |

## CORS / frontend

| Variable | Service |
|----------|---------|
| `FRONTEND_URL` | API |
| `CORS_ORIGINS` | API |
| `CORS_ORIGIN_REGEX` | API |
| `VITE_API_BASE_URL` | Vercel build |
| `VITE_WS_BASE_URL` | Vercel build |

## AI & email & files

| Variable | Services |
|----------|----------|
| `GEMINI_API_KEY` | API, SW (scoring) |
| `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | API, SW |
| `CLOUDINARY_*` | API, SW |
| `API_PUBLIC_URL` | Email asset links |

## TTL retention (Phase 5)

| Variable | Days | Collection |
|----------|------|------------|
| `SCAN_STATE_RETENTION_DAYS` | 7 | `scan_states` |
| `SCAN_TASK_RETENTION_DAYS` | 14 | `scan_execution_tasks` |
| `BROWSER_SESSION_RETENTION_DAYS` | 3 | `browser_sessions` |
| `NOTIFICATION_RETENTION_DAYS` | 30 | `notifications` |
| `REALTIME_EVENT_RETENTION_DAYS` | 1 | `realtime_events` |
| `AUTOMATION_RUN_RETENTION_DAYS` | 30 | `automation_runs` |

## Playwright

| Variable | Description |
|----------|-------------|
| `PLAYWRIGHT_HEADLESS` | `true` on Render |
| `PLAYWRIGHT_DEFAULT_TIMEOUT_MS` | Default 30000 |

## Extension

| Variable | Description |
|----------|-------------|
| `EXTENSION_MIN_VERSION` | Career Lens minimum version |

## Per-service production templates

See [../deployment/render-vercel-deployment.md](../deployment/render-vercel-deployment.md).

Legacy doc: [../deployment/environment-variables.md](../deployment/environment-variables.md) (shorter form).

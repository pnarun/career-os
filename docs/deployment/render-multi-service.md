# Render multi-service deployment

Deploy three backend Web Services from one Docker image.

## Services

| Service name | Command | Plan notes |
|--------------|---------|------------|
| `career-os` or `career-os-api` | `python start_api.py` | Starter recommended for API |
| `career-os-scan-worker` | `python start_scan_worker.py` | Free tier possible with health port |
| `career-os-automation` | `python start_automation_worker.py` | Create manually (not in all blueprints) |

## Blueprint

Use root `render.yaml` — defines API + scan worker. Add automation service in dashboard:

1. New → Web Service → same repo
2. Root: `backend`
3. Docker command: `python start_automation_worker.py`
4. Health check: `/health`

## Shared Dockerfile

`backend/Dockerfile` copies `start_api.py`, `start_scan_worker.py`, `start_automation_worker.py`.

## Health checks

| Service | Path |
|---------|------|
| API | `/health` |
| scan-worker | `/health` |
| automation | `/health` |

## Do not expose workers publicly

Workers only need health checks. No CDN, no user traffic.

## Rollback

Rollback each service independently in Render dashboard → deploy previous commit.

If only API regresses, worker may continue processing old queued tasks.

## Common failures

| Failure | Fix |
|---------|-----|
| Worker exits immediately | Set `PORT`; use Web Service not Background Worker |
| Duplicate schedules | API `ENABLE_SCHEDULER=false` |
| 0% progress | Same `MONGO_URI` on all services |
| CORS errors | `FRONTEND_URL` on API |

See [render-vercel-deployment.md](./render-vercel-deployment.md).

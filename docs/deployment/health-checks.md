# Health checks

## API (`career-os` / `career-os-api`)

| Path | Use |
|------|-----|
| `GET /health` | JSON keep-alive payload |
| `HEAD /health` | Empty **200** (UptimeRobot default) |

Both methods are registered on the same route (`methods=["GET", "HEAD"]`). Logs: `[HEALTH_CHECK] method=GET|HEAD`.

`render.yaml`: `healthCheckPath: /health`

## Scan worker (`career-os-scan-worker`)

Embedded HTTP server (`worker_health_server.py`):

| Path | Port |
|------|------|
| `/health` | `$PORT` (Render injects) |

Command: `python start_scan_worker.py`

## Automation worker (`career-os-automation`)

| Path | Default port |
|------|----------------|
| `/health` | `$PORT` or 10000 local |

Command: `python start_automation_worker.py`

## What health does *not* prove

- Mongo connectivity (may still fail on first request)
- Playwright working (only process alive)
- Queue draining (worker may be idle)

Deep check: trigger test scan + [../testing/worker-verification.md](../testing/worker-verification.md).

## UptimeRobot

Point at API `HEAD /health` every 5 minutes — [uptime-robot-keepalive.md](./uptime-robot-keepalive.md).

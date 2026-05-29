# Service monitoring

## Health endpoints

| Service | URL |
|---------|-----|
| API | `GET /health`, `HEAD /health` |
| scan-worker | `GET /health` on worker host |
| automation | `GET /health` on automation host |

## Detailed API health

```bash
curl "https://API/health?detail=1"
```

Includes memory snapshot when available.

## System routes (authenticated / ops)

| Route | Purpose |
|-------|---------|
| `/system/status` | Component status |
| `/system/metrics` | Metrics snapshot |
| `/system/beta-ops` | Beta operations |

## UptimeRobot

Ping API `HEAD /health` every 5 minutes — reduces Render sleep.

See [../deployment/uptime-robot-keepalive.md](../deployment/uptime-robot-keepalive.md).

## What to alert on

| Signal | Severity |
|--------|----------|
| API health non-200 | Critical |
| Worker health non-200 | High |
| Growing `queued` task count | High |
| Atlas storage >80% M0 | Medium |
| Error rate in `[SCAN_FAILED]` | Medium |

## Render dashboard

Monitor each service: CPU, memory, deploy events, restart loops.

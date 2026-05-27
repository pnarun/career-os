# UptimeRobot keep-alive

Prevent Render free/starter services from sleeping by pinging the lightweight health endpoint.

## Endpoint

| Method | URL | Response |
|--------|-----|----------|
| **HEAD** | `https://YOUR-API.onrender.com/health` | `200` empty body |
| **GET** | same | JSON `{"status":"ok","service":"...","scheduler":"running\|stopped"}` |

**UptimeRobot free tier** uses **HEAD** — supported explicitly.

Render port probe uses **HEAD /** — also returns `200`.

## UptimeRobot setup

| Setting | Value |
|---------|--------|
| Monitor type | HTTP(s) |
| URL | `https://career-os-pd9g.onrender.com/health` (your service URL) |
| HTTP method | HEAD |
| Interval | 5 minutes |
| Timeout | 60 seconds |
| Expected | HTTP 200 |

![UptimeRobot](../assets/screenshots/uptimerobot-monitor.png)

## Why not GET only?

Historically GET-only `/health` returned **405** for HEAD monitors. Both methods are now implemented in `app/api/routes/system.py`.

## Interaction with frontend

`BackendWakeContext` also polls `GET /health` every 5 minutes when online — aligns with UptimeRobot but does not replace it (browser must be open).

## Alternatives

| Option | Cost | Notes |
|--------|------|-------|
| UptimeRobot free | $0 | Recommended MVP |
| Render Cron Job | Paid add-on | `POST /internal/cron/scheduled-scans` |
| Render Starter plan | $7/mo | Less sleep, still use keep-alive for scans |

## Related

- [Render deployment](./render-vercel-deployment.md)
- [APScheduler](../scheduling/apscheduler.md)

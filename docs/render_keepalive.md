# Render free tier keep-alive (UptimeRobot)

> **Canonical:** [deployment/uptime-robot-keepalive.md](./deployment/uptime-robot-keepalive.md)

Career OS runs **APScheduler inside the FastAPI process** on Render. Scheduled scans, email digests, and reminders only run while that process is awake.

## Why Render sleeps

On Render’s **free** web service plan, the app **spins down after ~15 minutes** with no HTTP traffic. While asleep:

- APScheduler does **not** run
- Six-hour scan slots (00:00, 06:00, 12:00, 18:00 IST) are **missed**
- No scan emails are sent until something wakes the server

## Solution: external HTTP pings (UptimeRobot)

Use a **free** external monitor (UptimeRobot, Better Stack, etc.) to call your public health URL every few minutes. That counts as activity and keeps the **same** web service awake—no extra Render services and no paid Render Cron Jobs.

```
UptimeRobot  --GET /health every 5 min-->  Render Web Service (career-os-api)
                                              └── APScheduler (in-process)
```

### What `/health` does

- Returns quickly (cached ~2s, no MongoDB)
- Exposes scheduler state: `running`, `active_jobs`, `next_scheduled`
- Does **not** run scans, Playwright, or heavy providers

Full dependency checks (MongoDB, Redis): `GET /system/status`

## UptimeRobot setup

| Field | Value |
|--------|--------|
| **Monitor type** | HTTP(s) |
| **URL** | `https://YOUR-RENDER-API.onrender.com/health` (include `https://`) |
| **HTTP method** | **HEAD** (UptimeRobot free tier default) or GET — both return **200** |
| **Interval** | 5 minutes |
| **Timeout** | 30–60 seconds |
| **Expected** | HTTP **200** (not 405). Optional keyword: `"status":"ok"` |

Example (replace with your URL):

```text
https://career-os-pd9g.onrender.com/health
```

Or your custom domain:

```text
https://api.lensos.career-lens.in/health
```

### Sample response

```json
{
  "status": "ok",
  "service": "Career OS API",
  "scheduler": "running",
  "scheduler_running": true,
  "active_jobs": 4,
  "preference_scan_jobs": 1,
  "next_scheduled": [
    { "id": "scheduled_scan_...", "next_run": "2026-05-27T00:30:00+00:00" }
  ],
  "timestamp": "2026-05-27T08:00:00+00:00"
}
```

If `scheduler` is `"stopped"` after deploy, check API logs for `[SCHEDULER] Initialized`.

## Render web service env (optional)

| Variable | Default | Purpose |
|----------|---------|---------|
| `SCHEDULER_HEARTBEAT_ENABLED` | `true` | Log `[SCHEDULER] heartbeat alive` every 30 minutes |
| `SCHEDULER_STARTUP_CATCHUP` | `true` | Run one overdue scan after deploy/restart |
| `HEALTH_CACHE_SECONDS` | `2` | Cache `/health` payload for fast pings |

With UptimeRobot keeping the process alive 24/7, startup catch-up mainly helps after **deploy** or rare restarts.

## Frontend keep-alive

When a user has the app open, the frontend also pings `/health` every **5 minutes** (`BackendWakeContext`). The sidebar shows **Online** / **Reconnecting** / **Sleeping**.

UptimeRobot is still required when **no one** has the app open overnight.

## Verify

1. Create the UptimeRobot monitor and wait for one green check.
2. Open Render → **career-os-api** → **Logs** — look for `[SCHEDULER] Initialized` and periodic `[SCHEDULER] heartbeat alive`.
3. `curl https://YOUR-API/health` — confirm `scheduler`: `"running"`.
4. In the app: **Scans & Automation** → enable schedule → **Save**.

## What we do **not** use

- No second Render web service
- No Render Cron Jobs (paid add-on for reliable cron on Render)
- No scan logic on `/health` (keeps pings cheap and safe)

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Monitor **405** Method Not Allowed | Set monitor to **GET**; URL must be `https://.../health`. Redeploy API if using HEAD-only probes |
| Monitor fails / timeout | Cold start: first ping after sleep can take 30–90s; increase UptimeRobot timeout |
| `scheduler: stopped` | API failed during startup; read deploy logs |
| Scans still missing | Schedule saved? `is_active` true? `frequency` = `every_6h`? |
| Duplicate emails after restart | Set `SCHEDULER_STARTUP_CATCHUP=false` if catch-up overlaps with APScheduler misfire |

See also: [DEPLOY.md](./DEPLOY.md)

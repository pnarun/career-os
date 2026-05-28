# Render health checks, keep-alive, and email notifications

## Render Health Check Path (your screenshot)

In **Render → career-os → Settings → Health Checks**:

| Field | Value |
|-------|--------|
| **Health Check Path** | `/health` |

Click **Edit**, enter `/health`, save.

For deeper diagnostics during beta, use `GET /health?detail=1` (Mongo, WebSocket, scans, providers) and `GET /system/beta-ops` (HTML) or `/system/beta-ops/json`. See [Beta readiness](../beta/beta-readiness.md).

### Does this replace UptimeRobot?

| Feature | Render health check | UptimeRobot HEAD `/health` |
|---------|---------------------|----------------------------|
| Detect crashed app | Yes — can restart unhealthy instance | No — external ping only |
| Prevent free-tier **sleep** | **No** — sleep is idle timeout, not failed health | **Yes** — traffic wakes the service |
| Best practice | Set both | Keep 5-minute ping |

**Recommendation:** Use **both**:

1. Render health path = `/health` (recovery if process dies)
2. UptimeRobot = `HEAD https://YOUR-API.onrender.com/health` every 5 min (reduce cold starts)

### Developer status dashboard

Embed your public UptimeRobot page on the API (same pattern as `/logs`):

| URL | Purpose |
|-----|---------|
| `GET /uptime` | Developer hub — live API health + link to UptimeRobot (embedding is blocked by UptimeRobot) |
| `GET /uptime/go` | Redirect to [your status page](https://stats.uptimerobot.com/rIhbIgCMm7) |
| `GET /system/uptime` | OpenAPI alias for `/uptime` |

```env
UPTIMEROBOT_STATUS_PAGE_URL=https://stats.uptimerobot.com/rIhbIgCMm7
```

Local: `http://localhost:8001/uptime` · Production: `https://YOUR-API.onrender.com/uptime`

Blueprint already sets `healthCheckPath: /health` in `render.yaml`; existing services may need a manual update in the dashboard.

---

## Admin email (`ADMIN_NOTIFY_EMAIL`)

One inbox for:

- New user registrations
- Deploy / CI notifications (via API webhook)

### Backend (Render)

```env
ADMIN_NOTIFY_EMAIL=you@example.com
ADMIN_NOTIFY_ENABLED=true
RESEND_API_KEY=re_...
RESEND_FROM_EMAIL=Career OS <onboarding@resend.dev>
CRON_SECRET=<long-random-string>
```

If `ADMIN_NOTIFY_EMAIL` is empty, falls back to `LEGACY_MIGRATION_EMAIL`.

### GitHub Actions (CI success email)

Repo **Settings → Secrets and variables → Actions**:

| Secret | Example |
|--------|---------|
| `CAREER_OS_API_URL` | `https://career-os-pd9g.onrender.com` |
| `CRON_SECRET` | Same as Render `CRON_SECRET` |

Workflow: `.github/workflows/notify-deploy.yml` — runs after **CI succeeds** on `main` and calls:

`POST /internal/notify/deploy` with `X-Cron-Secret`.

### Render deploy success email (webhook)

1. Render → **Integrations** → **Webhooks** (or Notifications)
2. On **Deploy succeeded**, POST to:

```text
https://YOUR-API.onrender.com/internal/notify/deploy
```

Headers:

```text
Content-Type: application/json
X-Cron-Secret: <your CRON_SECRET>
```

Body example:

```json
{
  "component": "render-api",
  "status": "success",
  "url": "https://career-os-pd9g.onrender.com",
  "message": "Render deploy live"
}
```

### Vercel deploy success email

**Option A — Vercel built-in (easiest)**  
Vercel → Project → **Settings → Notifications** → add your email for Production deployments.

**Option B — Deploy hook → API**  
Use Vercel deploy webhook (if available on your plan) to POST the same `/internal/notify/deploy` body with `"component": "vercel-frontend"`.

---

## New user registration email

Automatic when someone registers via `/auth/register`:

- **To:** `ADMIN_NOTIFY_EMAIL`
- **Includes:** email, name, user ID, timezone
- **Skipped** when `ENVIRONMENT=development`

No extra code needed after env vars are set on Render.

---

## Quick checklist

- [ ] Render Health Check Path = `/health`
- [ ] UptimeRobot monitor on `/health` (HEAD)
- [ ] `ADMIN_NOTIFY_EMAIL` on Render
- [ ] `CRON_SECRET` on Render
- [ ] GitHub secrets `CAREER_OS_API_URL` + `CRON_SECRET`
- [ ] Vercel notification email enabled
- [ ] Test: register a user → admin inbox receives mail

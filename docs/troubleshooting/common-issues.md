# Troubleshooting guide

Production issues encountered during Career OS development and deployment.

## Render & deployment

### HEAD /health returns 405

**Symptom:** UptimeRobot Down, HTTP 405  
**Cause:** Monitor used HEAD; route was GET-only  
**Fix:** Deploy `HEAD /health` and `HEAD /` handlers in `system.py`

### FastAPI deploy crash: Invalid response field Union

**Symptom:** `FastAPIError: dict[str, Any] | Response` on import  
**Cause:** Single route with union return type  
**Fix:** Split `@router.get("/health")` and `@router.head("/health")`

### No open ports detected (but app runs)

**Symptom:** Render log shows 405 on `HEAD /` then port scan warning  
**Fix:** `HEAD /` returns 200; bind `0.0.0.0:10000`

### Render cold start / slow login

**Symptom:** “Waking up servers…” 30–90s  
**Mitigation:** UptimeRobot HEAD `/health` every 5 min; Starter plan; frontend `BackendWakeContext`

### Scheduler startup catch-up: `_utc_now_iso` not defined

**Symptom:** `[SCHEDULER] Startup catch-up failed: name '_utc_now_iso' is not defined`  
**Cause:** `notification_service.py` called helper without definition  
**Fix:** Add `_utc_now_iso()` to `notification_service.py`

### Startup scan errors: resume_not_found

**Symptom:** `[SCAN_FAILED] reason=resume_not_found` for demo users  
**Cause:** Active preferences with empty `resume_id`  
**Fix:** Skip scans when `resume_id` blank; upload resume or deactivate preference

## Frontend

### net::ERR_BLOCKED_BY_CLIENT on /health

**Symptom:** Console red errors, app stuck waking  
**Cause:** Ad blocker / privacy extension (not CORS)  
**Fix:** Incognito test; whitelist `*.vercel.app` and `*.onrender.com`; optional Vercel `/api` proxy

### CORS errors (true CORS)

**Symptom:** `blocked by CORS policy` in console  
**Fix:** Set `FRONTEND_URL` on Render to exact Vercel URL; enable `CORS_ORIGIN_REGEX` for previews

### VITE_API_BASE_URL wrong

**Symptom:** Empty API URL in prod, or `http://` mixed content  
**Fix:** `https://` on Vercel env; **redeploy** after change

### WebSocket invalid token loop

**Symptom:** Render logs spam `[REALTIME] invalid token`  
**Cause:** Expired access token + reconnect without refresh  
**Fix:** Deploy `realtimeClient.js` refresh on 4401; log out/in after `JWT_SECRET_KEY` change

## Playwright & automation

### Playwright install fails locally

**Fix:**

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

### Subprocess worker timeout

**Symptom:** Automation health fails, stderr in logs  
**Fix:** Increase timeouts; run `prepare-session` again; check Chromium deps in Docker

### LinkedIn session lost after deploy

**Cause:** Ephemeral container disk  
**Fix:** Re-prepare session; add Render persistent disk for `automation/profiles/`

### Browser lifecycle / zombie Chromium (Windows dev)

**Symptom:** Orphan chromium processes  
**Fix:** Kill processes; ensure worker subprocess exits; avoid in-process Playwright

## Database & Redis

### Redis connection refused on Render

**Symptom:** `localhost:6379` errors  
**Cause:** `REDIS_ENABLED=true` without Render Redis  
**Fix:** `REDIS_ENABLED=false` in `render.yaml` or set real `REDIS_URL`

### MongoDB connection failed

**Fix:** Atlas IP allowlist `div.0.0.0/0` or Render egress IPs; verify `MONGO_URI` user/password

## Scheduler

### Scans not running on schedule

**Check:**

1. `is_active` on preferences
2. `resume_id` set
3. Service awake (UptimeRobot)
4. Logs for `[SCHEDULER] Next scheduled_scan_*`
5. `SCHEDULER_STARTUP_CATCHUP` after long sleep

### Windows PowerShell && fails

**Symptom:** `&&` not valid in PowerShell  
**Fix:** Use `;` separator: `cd backend; python -m pytest`

## Python environment

### pytest / httpx not found

**Fix:** Use project venv:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Quick diagnostic commands

```bash
# Health
curl -I https://YOUR-API.onrender.com/health
curl https://YOUR-API.onrender.com/health

# System status
curl https://YOUR-API.onrender.com/system/status

# DB
curl https://YOUR-API.onrender.com/db-check
```

## Related

- [Deployment](../deployment/render-vercel-deployment.md)
- [UptimeRobot](../deployment/uptime-robot-keepalive.md)
- [Logging](../operations/logging.md)

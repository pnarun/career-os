# Deployment troubleshooting

## API deploys but scans never complete

1. Is **scan-worker** running? `curl WORKER_URL/health`
2. Same **`MONGO_URI`** on API and worker?
3. API `SCAN_EXECUTION_MODE=dispatch`?
4. Worker logs: `[SCAN_TASK] claimed`?

## Frontend 0% forever

1. Poll: `GET /scans/status/{scan_id}` — does `progress` change in API logs `[SCAN_STATE_API]`?
2. Worker logs: `[SCAN_PROGRESS_WRITE]`?
3. If poll works but WS does not: check `[REALTIME_EVENT] published` / `delivered`

## CORS / login failures

- `FRONTEND_URL` exact match (no trailing slash)
- `CORS_ORIGIN_REGEX` for Vercel previews
- Redeploy frontend after `VITE_*` change

## Playwright failures on Render

- Docker image includes Chromium (`playwright install` in Dockerfile)
- `PLAYWRIGHT_HEADLESS=true`
- LinkedIn may require valid session in `browser_sessions`

## Indeed 403 / empty Indeed results

**Known limitation** — Indeed often blocks datacenter IPs. Other providers may still succeed. Documented as **partial** provider success, not total scan failure.

## Build timeout

First Docker build installs Chromium — 10–20 minutes possible. Retry build.

## Web Service vs Background Worker

Use **Web Service** with health port for workers on free tier.

See [../troubleshooting/common-issues.md](../troubleshooting/common-issues.md).

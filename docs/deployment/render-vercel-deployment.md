# Render + Vercel deployment

Full step-by-step deploy guide. Also see legacy [DEPLOY.md](../DEPLOY.md) at repo root.

## Architecture

```mermaid
flowchart LR
  User --> Vercel[Vercel CDN - SPA]
  User --> Render[Render Web Service - Docker]
  Vercel -->|HTTPS API| Render
  Render --> Atlas[(MongoDB Atlas)]
  Uptime[UptimeRobot] -->|HEAD /health| Render
```

## Prerequisites

1. MongoDB Atlas cluster + connection string
2. API keys: Gemini, Resend, Cloudinary
3. GitHub repo connected to Vercel and Render
4. Long random `JWT_SECRET_KEY`

## 1. Backend on Render

### Blueprint (recommended)

1. Render → **New** → **Blueprint** → select `render.yaml`
2. Set secrets in dashboard:

| Variable | Required |
|----------|----------|
| `MONGO_URI` | Yes |
| `JWT_SECRET_KEY` | Yes |
| `FRONTEND_URL` | Yes — exact Vercel URL, no trailing slash |
| `GEMINI_API_KEY` | Yes |
| `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | Yes |
| `CLOUDINARY_*` | Yes |

3. Defaults from blueprint: `REDIS_ENABLED=false`, `CELERY_ENABLED=false`, `ENVIRONMENT=production`
4. **Health check path:** `/health`
5. First Docker build installs Playwright Chromium (**10–20 min** possible)

### Verify backend

```bash
curl -I https://YOUR-SERVICE.onrender.com/health
# HTTP/1.1 200 OK

curl https://YOUR-SERVICE.onrender.com/health
# {"status":"ok","service":"...","scheduler":"running"}
```

![Render dashboard](../assets/screenshots/render-dashboard.png)

## 2. UptimeRobot keep-alive

See [UptimeRobot keep-alive](./uptime-robot-keepalive.md).

- URL: `https://YOUR-SERVICE.onrender.com/health`
- Method: **HEAD** (free tier)
- Interval: 5 minutes
- Timeout: 60 seconds

## 3. Frontend on Vercel

1. Import repo, **Root Directory:** `frontend`
2. Framework: Vite
3. Environment variables (**Production + Preview**):

| Name | Value |
|------|--------|
| `VITE_API_BASE_URL` | `https://YOUR-SERVICE.onrender.com` |
| `VITE_WS_BASE_URL` | `wss://YOUR-SERVICE.onrender.com` |

4. Deploy — `vercel.json` handles SPA routing

**Important:** `VITE_*` are **build-time**. Redeploy after changing them.

![Vercel env](../assets/screenshots/vercel-env.png)

## 4. Wire CORS

On Render:

- `FRONTEND_URL=https://your-app.vercel.app`
- `CORS_ORIGIN_REGEX=https://.*\.vercel\.app` (preview deploys)

## 5. Post-deploy checklist

- [ ] `/health` returns 200 (HEAD and GET)
- [ ] Register/login from Vercel URL works
- [ ] Upload resume in Settings / Resume hub
- [ ] Manual scan runs (`POST /run-scan-now`)
- [ ] WebSocket connects (no infinite invalid-token loop)
- [ ] UptimeRobot monitor green

## Playwright on Render

- Included in `backend/Dockerfile`
- LinkedIn sessions **ephemeral** without persistent disk
- Set `PLAYWRIGHT_HEADLESS=true` in production

## Optional upgrades

| Upgrade | Benefit |
|---------|---------|
| Render Starter ($7) | Less aggressive sleep |
| Render persistent disk | Keep LinkedIn session files |
| Render Redis | Rate limit + Celery + realtime fan-out |

## Local frontend → production API

```bash
cd frontend
cp .env.example .env
# VITE_API_BASE_URL=https://YOUR-SERVICE.onrender.com
npm run dev
```

## Related

- [Environment variables](./environment-variables.md)
- [Production readiness](../production/production-readiness-checklist.md)
- [Troubleshooting](../troubleshooting/common-issues.md)

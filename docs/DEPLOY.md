# Deploy Career OS (Vercel + Render)

| Component | Platform | URL pattern |
|-----------|----------|-------------|
| Frontend (React/Vite) | [Vercel](https://vercel.com) | `https://your-app.vercel.app` |
| Backend (FastAPI) | [Render](https://render.com) | `https://career-os-api.onrender.com` |
| Database | [MongoDB Atlas](https://www.mongodb.com/atlas) | Cloud URI in `MONGO_URI` |

## Prerequisites

1. MongoDB Atlas cluster (free tier is fine) with connection string.
2. API keys: Gemini, Resend, Cloudinary (see `backend/.env.example`).
3. GitHub repo connected to Vercel and Render.

---

## 1. Backend on Render

### Option A — Blueprint (recommended)

1. Render → **New** → **Blueprint**.
2. Connect this repository and select `render.yaml` at the repo root.
3. After the service is created, open **Environment** and set secrets:

| Variable | Required | Notes |
|----------|----------|--------|
| `MONGO_URI` | Yes | Atlas connection string |
| `JWT_SECRET_KEY` | Yes | Long random string |
| `FRONTEND_URL` | Yes | Your Vercel production URL, no trailing slash |
| `GEMINI_API_KEY` | Yes | Resume/copilot AI |
| `RESEND_API_KEY` | Yes | Email |
| `RESEND_FROM_EMAIL` | Yes | Verified sender in Resend |
| `CLOUDINARY_*` | Yes | Resume uploads |
| `CORS_ORIGIN_REGEX` | Optional | Default in blueprint: `https://.*\.vercel\.app` for preview deploys |

4. Wait for the Docker build (includes Playwright Chromium — first build may take several minutes).
5. Note the live URL, e.g. `https://career-os-api.onrender.com`.
6. Verify: `https://career-os-api.onrender.com/health`

### Option B — Manual web service

1. **New** → **Web Service** → connect repo.
2. **Root Directory**: leave empty (repo root).
3. **Runtime**: Docker.
4. **Dockerfile Path**: `backend/Dockerfile`.
5. **Docker Context**: `backend`.
6. **Health Check Path**: `/health`.
7. Add the same environment variables as above.

### Render notes

- **Free/starter plans** spin down when idle; first request after sleep can be slow.
- **Playwright/LinkedIn** runs in the container; LinkedIn session files are ephemeral unless you use persistent disk (optional upgrade).
- **Redis/Celery** are off by default in `render.yaml`. Enable later with a Render Redis instance and set `REDIS_URL` + `REDIS_ENABLED=true`.
- **WebSockets** work on Render web services — use `wss://` from the frontend.

---

## 2. Frontend on Vercel

1. Vercel → **Add New Project** → import the GitHub repo.
2. **Root Directory**: `frontend` (important).
3. Framework preset: **Vite** (or auto-detected).
4. **Environment Variables** (Production and Preview):

| Name | Example value |
|------|----------------|
| `VITE_API_BASE_URL` | `https://career-os-api.onrender.com` |
| `VITE_WS_BASE_URL` | `wss://career-os-api.onrender.com` |

5. Deploy. `frontend/vercel.json` handles SPA routing (all routes → `index.html`).

### Local frontend pointing at Render

```bash
cd frontend
cp .env.example .env
# Edit .env:
# VITE_API_BASE_URL=https://career-os-api.onrender.com
# VITE_WS_BASE_URL=wss://career-os-api.onrender.com
npm run dev
```

---

## 3. Wire frontend ↔ backend

After both are live:

1. **Render** → set `FRONTEND_URL` = `https://your-app.vercel.app` (exact production URL).
2. **Render** → ensure `CORS_ORIGIN_REGEX` = `https://.*\.vercel\.app` if you use Vercel preview URLs.
3. **Vercel** → redeploy if you changed `VITE_*` variables (build-time only).

Test login from the Vercel URL; check browser DevTools → Network for CORS errors.

---

## 4. MongoDB Atlas

1. **Network Access** → allow `0.0.0.0/0` (or Render outbound IPs if you restrict).
2. **Database User** with read/write on `career_os` database.
3. Connection string in `MONGO_URI` with username/password URL-encoded.

---

## 5. Optional services

| Service | When to add |
|---------|-------------|
| Render Redis | Rate limiting, realtime bridge, Celery |
| Custom domain | Configure DNS on Vercel and Render separately |
| Google OAuth | Set `GOOGLE_OAUTH_REDIRECT_URI` to Render callback URL |

---

## 6. Checklist

- [ ] `/health` returns `ok` on Render
- [ ] Vercel app loads and login works
- [ ] `FRONTEND_URL` set on Render
- [ ] `VITE_API_BASE_URL` / `VITE_WS_BASE_URL` set on Vercel
- [ ] `JWT_SECRET_KEY` is not the default dev value
- [ ] `AUTH_DEV_EXPOSE_OTP=false` in production
- [ ] Atlas allows Render connections

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS error on login | Redeploy latest API (auto-allows `*.vercel.app` on Render); set `FRONTEND_URL=https://your-app.vercel.app` |
| 404 on API root `/` | Use `/health`, `/docs`, or `/logs` |
| `Failed to fetch` | Wrong `VITE_API_BASE_URL`; Render service asleep |
| WebSocket fails | Use `wss://` not `ws://`; same host as API |
| Build fails on Render | Check Docker logs; Playwright install needs enough memory |
| Vite still calls localhost | Rebuild Vercel after env change |

See also `README.md` for local development.

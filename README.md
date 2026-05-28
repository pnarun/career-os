# Career OS

<p align="center">
  <img src="frontend/public/career-os-logo.png" alt="Career OS" width="320" />
</p>

**By [ELVA Tech](https://elvatech.in)** · Part of **[Career Lens](https://career-lens.in)**

Career OS is an AI-powered job search and career automation platform. It aggregates roles from multiple boards, scores them against your resume, runs scheduled scans, supports browser-based automation, and provides resume, interview, analytics, and copilot tooling from a single dashboard.

## Documentation

**Full engineering & product documentation:** **[docs/README.md](docs/README.md)**

| Guide | Link |
|-------|------|
| Developer onboarding | [docs/onboarding/developer-onboarding.md](docs/onboarding/developer-onboarding.md) |
| System architecture | [docs/architecture/system-overview.md](docs/architecture/system-overview.md) |
| Deploy (Vercel + Render) | [docs/deployment/render-vercel-deployment.md](docs/deployment/render-vercel-deployment.md) |
| Beta launch checklist | [docs/beta/beta-readiness.md](docs/beta/beta-readiness.md) |
| Career Lens extension | [docs/extension/extension-architecture.md](docs/extension/extension-architecture.md) |
| API reference | [docs/api/api-reference.md](docs/api/api-reference.md) |
| Troubleshooting | [docs/troubleshooting/common-issues.md](docs/troubleshooting/common-issues.md) |
| Screenshots to capture | [docs/assets/README.md](docs/assets/README.md) |

## Features

### Job discovery & matching

- **Multi-provider job feed** — LinkedIn (Playwright), Indeed, Naukri, Instahyre, RemoteOK, Arbeitnow via a unified aggregator with provider diagnostics and circuit breaking
- **Job Match** — Score any role against your parsed resume
- **Unified feed** — Deduped listings with platform metadata and match insights
- **Scan sessions** — Run and track job scans with live execution timeline and scan analytics

### Resume & AI

- **Resume upload** — PDF/DOCX parsing via Cloudinary; skills and profile extraction
- **Resume AI** — ATS scoring, keyword optimization, JD alignment, variants, and feedback
- **New-user onboarding** — After register + platform tour, optional resume prompt; skip locks navigation until upload (existing users are unaffected)

### Applications & automation

- **Applications pipeline** — Saved jobs, apply status, and interview tracking
- **Auto-apply assistant** — Playwright workflows for supported boards (e.g. LinkedIn Easy Apply, Naukri)
- **Automation hub** — Browser session management, prepare/open signals, screenshots, and worker CLI
- **Real-time updates** — WebSockets for scan progress, provider status, automation stream, and notifications

### Career intelligence

- **Career Analytics** — Market trends, salary insights, skill demand, heatmaps, and growth metrics
- **Career Copilot** — AI assistant grounded in your jobs, resume, and preferences
- **Interview Prep** — Readiness scores, mock interviews, question generation, and prep plans

### Auth & UX

- **JWT auth** — Register, login, refresh tokens; password reset; Google OAuth extension point
- **Public landing page** — Marketing site at `/` with sign-in flow
- **Privacy policy** — Public `/privacy-policy` (fixed nav + scrollable sections; linked from landing and sidebar)
- **Beta onboarding** — Welcome modal, Settings → Beta support, ops dashboards (`/system/beta-ops`)
- **Career Lens extension** — Chrome MV3 bridge for LinkedIn session pairing (see `extension/`)
- **Platform tour** — First-login walkthrough with “Don’t show again”
- **PWA** — Install prompt and service worker (production)
- **Profile & settings** — Preferences, provider priority, scan scheduling, notifications

### Production infrastructure

- **Redis** — Cache, rate limiting, Celery broker, realtime bridge
- **Celery queues** — Scan, scoring, notification, analytics, and retry tasks
- **Observability** — Structured logging, `/health` (optional `?detail=1`), `/system/status`, `/system/metrics`, `/system/beta-ops`
- **Resilience** — Retries, circuit breakers on aggregators, configurable rate limits
- **Docker & CI** — Compose overlays for local/staging/production, frontend Dockerfile, GitHub Actions workflow
- **Deploy assets** — `infra/` nginx, backup scripts, bootstrap and deploy helpers

## Architecture

```
career-os/
├── frontend/          # React + Vite dashboard
├── backend/           # FastAPI API, workers, automation
├── extension/         # Career Lens Chrome extension (LinkedIn pairing)
├── docs/              # Engineering & product documentation portal
├── infra/             # Docker, nginx, CI, deployment scripts
├── docker-compose.yml # Redis (+ optional full stack profile)
└── backend/.env.example
```

| Backend package | Purpose |
|-----------------|---------|
| `api/` | HTTP routes (jobs, scans, auth, automation, AI, system) |
| `auth/` | JWT, OAuth, password reset |
| `core/` | Config, Celery, Redis, cache, metrics, rate limit |
| `services/` | Business logic, job sources, resume/interview AI |
| `automation/` | Playwright browser manager and session storage |
| `queues/` | Celery task definitions |
| `realtime/` | WebSocket manager and event streams |
| `workers/` | Celery worker entry |

MongoDB is intended for **MongoDB Atlas**. Redis runs locally via Docker (or in compose for staging/production).

## Tech stack

**Frontend:** React 19, Vite, TypeScript, Tailwind CSS v4, shadcn/ui, lazy-loaded routes

**Backend:** FastAPI, Motor/PyMongo, Celery, Redis, Playwright, Google Gemini, Resend, Cloudinary

**Infrastructure:** Docker, nginx, GitHub Actions

## Local setup

### Prerequisites

- Node.js 20+
- Python 3.12+
- Docker Desktop (for Redis)

### 1. Environment

Copy the example env and fill in your values (never commit `.env` or `backend/.env.*`):

```bash
cd backend
cp .env.example .env
# Edit .env — Atlas URI, Gemini, Resend, Cloudinary, JWT secret, etc.
```

Optional environment-specific files (gitignored): `.env.development`, `.env.production`, `.env.staging`.

### 2. Redis

```bash
docker compose up redis -d
```

### 3. Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload
```

- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: [http://localhost:5173](http://localhost:5173) (landing → sign in → dashboard)

### 5. Tests (backend)

```bash
cd backend
REDIS_ENABLED=false pytest tests/
```

### Optional: full Docker stack

```bash
docker compose --profile full up --build
```

See `infra/README.md` for staging/production compose and deployment notes.

## Deploy (Vercel + Render)

| Layer | Host | Config |
|-------|------|--------|
| Frontend | **Vercel** (`frontend/` root) | `frontend/.env.example`, `frontend/vercel.json` |
| API | **Render** (Docker) | `render.yaml`, `backend/Dockerfile` |

1. Deploy API on Render (Blueprint or Docker web service) — see **[docs/deployment/render-vercel-deployment.md](docs/deployment/render-vercel-deployment.md)** (also [docs/DEPLOY.md](docs/DEPLOY.md)).
2. Set `MONGO_URI`, `JWT_SECRET_KEY`, `FRONTEND_URL`, and other secrets on Render.
3. Deploy frontend on Vercel with **Root Directory** = `frontend`.
4. Set `VITE_API_BASE_URL` and `VITE_WS_BASE_URL` to your Render URL (`https://` / `wss://`).

```bash
# Local frontend → production API
cd frontend && cp .env.example .env
# VITE_API_BASE_URL=https://your-api.onrender.com
```

## Browser automation profiles

Playwright stores per-user session cookies under `backend/app/automation/profiles/`. This directory is **gitignored** (sessions, apply flags, `session_metadata.json`). Only `.gitkeep` placeholders and `session_metadata.example.json` are tracked. Copy the example to `session_metadata.json` locally if your setup expects it.

## Security notes

- Do not commit `backend/.env`, `.env.development`, `.env.production`, or `.env.staging`
- Use strong `JWT_SECRET_KEY` in production
- Set `AUTH_DEV_EXPOSE_OTP=false` outside local dev
- Rotate keys if any secret was ever committed

## License

Private project — add license terms as needed.

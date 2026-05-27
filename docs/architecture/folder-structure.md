# Repository folder structure

## Root

```text
career-os/
├── frontend/                 # React + Vite SPA
├── backend/                  # FastAPI application
├── docs/                     # Documentation portal (this tree)
├── infra/                    # nginx, backups, monitoring helpers
├── render.yaml               # Render Blueprint
├── docker-compose.yml        # Local Redis / optional services
└── README.md                 # Project README (links to docs/)
```

## Backend (`backend/`)

```text
backend/
├── app/
│   ├── main.py               # FastAPI app, lifespan, middleware, routers
│   ├── api/routes/           # Domain HTTP routes (flat paths, no /api prefix)
│   ├── auth/                 # JWT, login, refresh, password reset
│   ├── automation/browser/   # Playwright subprocess worker CLI
│   ├── core/                 # config, database, logging, redis, cache, health
│   ├── models/               # Pydantic documents and API schemas
│   ├── services/             # Business logic
│   │   ├── job_sources/      # Provider adapters + aggregator
│   │   ├── automation/       # Scheduled scan orchestration
│   │   ├── auto_apply/       # Assisted apply flows
│   │   ├── resume_ai/
│   │   ├── interview_ai/
│   │   ├── copilot/
│   │   └── career_analytics/
│   ├── realtime/             # WebSocket manager, Redis bridge, event emitters
│   ├── queues/               # Celery tasks (optional)
│   └── workers/              # Celery worker entry
├── tests/
├── scripts/                  # Probes, keepalive Docker, utilities
├── Dockerfile                # Production image (Playwright + Chromium)
├── requirements.txt
└── .env.example
```

### Route modules (`app/api/routes/`)

| File | Domain |
|------|--------|
| `system.py` | Health, metrics, logs viewer, cron |
| `jobs.py` | Fetch, feed, history |
| `scan.py` | Run scan now, email preview |
| `preferences.py` | User preferences CRUD |
| `applications.py` | Application CRM |
| `automation.py` | Browser sessions, screenshots |
| `notifications.py` | Notifications, career insights |
| `resume_ai.py` | Resume AI endpoints |
| `interview_ai.py` | Interview prep |
| `career_analytics.py` | Analytics dashboards |
| `copilot.py` | Career copilot chat |
| `auto_apply.py` | Assisted apply sessions |
| `dashboard.py` | Dashboard summary |
| `upload.py` | Resume upload |
| `match.py` | Single job match |
| `resumes.py` | Resume list |
| `scan_analytics.py` | Scan session analytics |
| `suggestions.py` | Tag suggestions (roles, skills, etc.) |
| `db.py` | DB connectivity check |

Auth routes live in `app/auth/routes.py` with prefix `/auth`.

## Frontend (`frontend/`)

```text
frontend/
├── src/
│   ├── main.tsx              # Providers, PWA SW registration
│   ├── App.tsx               # Auth gate, AppShell, lazy pages
│   ├── pages/                # Page components (hubs + leaves)
│   ├── layouts/              # DashboardLayout
│   ├── components/           # UI, modals, domain widgets
│   ├── services/             # API client wrappers per domain
│   ├── context/              # Auth, Realtime, BackendWake, onboarding
│   ├── lib/                  # apiClient, realtime, navigation
│   ├── hooks/
│   ├── utils/
│   └── data/                 # Static copy (loading messages, etc.)
├── public/                   # PWA manifest, sw.js
├── vite.config.ts
├── vercel.json               # SPA rewrites, build config
└── .env.example
```

### Navigation model

No React Router URL paths for app pages. State machine:

- `AppPage` in React state
- Persisted in `sessionStorage` key `career-os-active-page`
- Public URL stays `/` (history `replaceState`)

See [Frontend architecture](../frontend/frontend-architecture.md).

## Documentation (`docs/`)

```text
docs/
├── README.md                 # Portal index
├── product/
├── architecture/
├── frontend/
├── backend/
├── database/
├── automation/
├── scheduling/
├── features/
├── deployment/
├── api/
├── security/
├── operations/
├── troubleshooting/
├── onboarding/
├── scaling/
├── engineering/
├── roadmap/
├── ui/
├── production/
└── assets/
    ├── screenshots/
    ├── diagrams/
    ├── ui/
    └── workflows/
```

## Infra (`infra/`)

```text
infra/
├── monitoring/health_check.sh
├── backups/mongo_backup.sh
└── (nginx / deploy helpers as added)
```

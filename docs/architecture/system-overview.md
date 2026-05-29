# System overview

> **Updated architecture:** This page is legacy. Use **[overview.md](./overview.md)** and **[diagrams.md](./diagrams.md)** for the current distributed runtime (API + scan-worker + automation, Mongo queues).

## High-level architecture

```mermaid
flowchart TB
  subgraph Client
    Browser[React SPA - Vercel]
  end

  subgraph API["FastAPI - Render Docker"]
    Routes[HTTP Routes]
    WS[WebSocket /ws/realtime]
    Sched[APScheduler]
    PWWorker[Playwright subprocess workers]
  end

  subgraph Data
    Mongo[(MongoDB Atlas)]
    Redis[(Redis - optional)]
  end

  subgraph External
    Gemini[Google Gemini]
    Resend[Resend Email]
    Cloudinary[Cloudinary]
    Boards[Job boards / LinkedIn]
  end

  Browser -->|HTTPS REST| Routes
  Browser -->|WSS + JWT| WS
  Routes --> Mongo
  Routes --> Redis
  Sched --> Routes
  PWWorker --> Boards
  Routes --> PWWorker
  Routes --> Gemini
  Routes --> Resend
  Routes --> Cloudinary
  Uptime[UptimeRobot HEAD /health] --> Routes
```

## Request lifecycle (authenticated API)

```mermaid
sequenceDiagram
  participant UI as React SPA
  participant API as FastAPI
  participant Auth as JWT + user_context
  participant Svc as Service layer
  participant DB as MongoDB

  UI->>API: apiFetch /jobs/feed + Bearer token
  API->>Auth: get_current_user
  Auth->>DB: load user
  API->>Svc: job_service / unified_feed
  Svc->>DB: query jobs, preferences
  Svc-->>API: JSON response
  API-->>UI: 200 + data
```

## Scan pipeline (scheduled or manual)

```mermaid
flowchart LR
  A[APScheduler or POST /run-scan-now] --> B[scan_runner_service]
  B --> C[discover_and_store_jobs]
  C --> D[aggregator - HTTP providers]
  C --> E[LinkedIn Playwright - if session]
  C --> F[AI scoring + dedupe]
  F --> G[(jobs + scan_sessions)]
  B --> H[email_service]
  B --> I[realtime events]
  B --> J[notification_service]
```

## Deployment topology

```mermaid
flowchart LR
  subgraph Vercel
    FE[Static SPA dist]
  end
  subgraph Render
    BE[career-os-api container]
    CHR[Chromium via Playwright]
  end
  subgraph Atlas
    MONGO[(career_os DB)]
  end
  FE -->|VITE_API_BASE_URL| BE
  BE --> MONGO
  BE --> CHR
```

## Component responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Frontend** | UX, auth tokens in localStorage, wake `/health`, WebSocket client |
| **FastAPI** | REST + WS, business logic orchestration, scheduler host |
| **MongoDB** | Users, preferences, jobs, applications, notifications, runs |
| **Playwright workers** | LinkedIn discovery, session prep, assisted apply (subprocess) |
| **APScheduler** | Per-user scan crons, reminders, heartbeat |
| **Gemini** | Resume AI, copilot, interview, insights |
| **Resend** | Transactional email / digests |

## Health and observability

| Endpoint | Purpose |
|----------|---------|
| `HEAD /` | Render port probe → 200 |
| `HEAD /health` | UptimeRobot free tier keep-alive |
| `GET /health` | JSON `{ status, service, scheduler }` |
| `GET /system/status` | Mongo, Redis, Celery, WS count |
| `GET /logs` | In-memory log viewer (HTML) |

## Cross-cutting concerns

- **CORS:** `FRONTEND_URL` + `CORS_ORIGINS` + optional `CORS_ORIGIN_REGEX` for `*.vercel.app`
- **Rate limiting:** Redis middleware (can disable via `RATE_LIMIT_ENABLED`)
- **Circuit breakers:** Per job provider in aggregator
- **Structured logging:** JSON lines + user email from context

## Related docs

- [Folder structure](./folder-structure.md)
- [Backend architecture](../backend/backend-architecture.md)
- [Frontend architecture](../frontend/frontend-architecture.md)
- [Deployment](../deployment/render-vercel-deployment.md)

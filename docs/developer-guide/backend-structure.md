# Backend structure

```text
backend/app/
├── api/routes/       # FastAPI routers (thin)
├── auth/             # JWT, OAuth hooks
├── core/             # config, database, retention, diagnostics
├── db/               # Mongo indexes
├── models/           # Pydantic schemas
├── runtime/          # bootstrap, service_mode, entrypoint defaults
├── scan_execution/   # distributed scan queue (Phase 1B+)
├── services/         # business logic
│   └── job_sources/  # per-provider fetchers
├── automation/       # Playwright browser layer
├── realtime/         # WebSocket + bridge
└── main.py           # FastAPI app + lifespan
```

## Rule

Routes → services → job_sources/automation. Heavy work never in routes.

## Workers

Not separate packages — same code, different `SERVICE_MODE`.

# Repository structure

```text
career-os/
├── frontend/              # React + Vite SPA
├── backend/               # FastAPI monolith + workers
│   ├── app/
│   │   ├── api/routes/    # HTTP routers
│   │   ├── scan_execution/ # Queue, coordinator, worker loop
│   │   ├── runtime/       # Bootstrap, service_mode
│   │   ├── services/      # Business logic
│   │   ├── realtime/      # WS, bridge, events
│   │   └── automation/    # Playwright
│   ├── start_api.py
│   ├── start_scan_worker.py
│   └── start_automation_worker.py
├── extension/             # Chrome MV3 Career Lens
├── docs/                  # Documentation portal
├── infra/                 # Docker, nginx, scripts
└── render.yaml            # Render blueprint
```

## Key entrypoints

| Command | Use |
|---------|-----|
| `uvicorn app.main:app` | Local monolith |
| `python start_api.py` | Production-like API |
| `python start_scan_worker.py` | Worker |

## Job archival (planned)

See `app/core/job_retention.py` — **not implemented**.

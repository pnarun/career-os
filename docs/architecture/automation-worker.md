# Automation worker

**Service:** `career-os-automation` (deploy manually on Render)  
**Entrypoint:** `python start_automation_worker.py`  
**Status:** **Partial** — process and health server **implemented**; dedicated Playwright job dequeue **planned**

## Current behavior (honest)

Today the automation worker:

- Boots with `SERVICE_MODE=automation_worker`
- Runs a **heartbeat loop** (keeps process alive)
- Exposes **health HTTP** on `PORT` (Render free tier)
- Can publish **realtime events** to Mongo if automation emitters run in this process

Most Playwright-heavy work still runs inside **scan pipelines on the scan worker** (job discovery, LinkedIn fetch). The automation worker is **infrastructure preparation** for isolating long-lived browser sessions from API and scan CPU.

## Responsibilities (target vs today)

| Capability | Status |
|------------|--------|
| Health endpoint for Render | **Implemented** |
| Heartbeat / graceful shutdown | **Implemented** |
| Mongo realtime publish on emit | **Implemented** (via shared `publish_user_event`) |
| Dedicated automation job queue | **Planned** |
| Replace API `automation_service` subprocess | **Planned** |

## Why a third service?

| Problem | Direction |
|---------|-----------|
| API OOM from Playwright | Move browser prep off API over time |
| Scan worker already busy with discovery | Separate concern for session keep-alive / apply flows |
| Render free tier | Web Service + health port (not Background Worker) |

## Production env

```env
SERVICE_MODE=automation_worker
SCAN_EXECUTION_MODE=dispatch
ENABLE_SCHEDULER=false
ENABLE_REALTIME=false
ENABLE_AUTOMATION=true
ENABLE_PLAYWRIGHT=true
MONGO_URI=...
```

## Logs

```
[AUTOMATION_WORKER] ready — Playwright runtime mode
[HEALTH_SERVER_STARTED]
[AUTOMATION_WORKER] heartbeat
```

## Related docs

- [playwright-automation.md](../automation/playwright-automation.md)
- [linkedin-session-management.md](../automation/linkedin-session-management.md)
- [service-boundaries.md](./service-boundaries.md)

# Distributed runtime

## Model

Career OS runs as **multiple Python processes** from the same `backend/` tree. Runtime behavior is controlled by environment variables, primarily `SERVICE_MODE` and `SCAN_EXECUTION_MODE`.

## Entrypoints

| Script | `SERVICE_MODE` | Typical host |
|--------|----------------|--------------|
| `python start_api.py` | `api` | Render Web Service **career-os** / **career-os-api** |
| `python start_scan_worker.py` | `scan_worker` | Render Web Service **career-os-scan-worker** |
| `python start_automation_worker.py` | `automation_worker` | Render Web Service **career-os-automation** (manual blueprint) |
| `uvicorn app.main:app` | `api` (default) | Local monolith dev |

## Feature flags (Phase 0+)

| Variable | API (prod) | Scan worker (prod) | Automation worker |
|----------|------------|--------------------|-------------------|
| `ENABLE_SCHEDULER` | `false` | `true` | `false` |
| `ENABLE_REALTIME` | `true` | `false` | `false` |
| `ENABLE_PLAYWRIGHT` | `true` | `true` | `true` |
| `ENABLE_AUTOMATION` | `true` | `false` | `true` |
| `SCAN_EXECUTION_MODE` | `dispatch` | `dispatch` | `dispatch` |

## Scan execution modes

### `dispatch` (production)

- API **enqueues** tasks in Mongo `scan_execution_tasks`.
- Scan worker **claims** and executes pipelines.
- API does **not** run heavy `discover_and_store_jobs` in the request process.

### `inline` (local / emergency)

- Monolith behavior: scans run in the API process after enqueue or directly.
- `ENABLE_SCHEDULER=true` on API is valid for local all-in-one dev.

## Bootstrap sequence

All processes call `bootstrap_core()`:

1. Mongo connect
2. Optional Redis client init
3. Upstash cache init
4. Mongo indexes + TTL indexes
5. Legacy migration (API typically)

API additionally runs `bootstrap_api_subsystems()`:

- Optional APScheduler (inline monolith only)
- Redis realtime subscriber (**partial** — if `REDIS_ENABLED`)
- **RealtimeBridgeLoop** (**implemented** — Mongo → WebSocket)
- Startup verification + storage report

Scan worker runs `bootstrap_scan_worker_subsystems()`:

- APScheduler + scan worker loop + health HTTP server

## Code modules

| Module | Role |
|--------|------|
| `app/runtime/service_mode.py` | Central runtime decisions |
| `app/runtime/bootstrap.py` | Shared startup/shutdown |
| `app/runtime/entrypoint.py` | Defaults for `start_*.py` scripts |
| `app/scan_execution/` | Task queue, coordinator, worker loop |
| `app/services/realtime_event_store.py` | Cross-service event bus |
| `app/realtime/realtime_bridge_loop.py` | API-only WS fan-out |

## ASCII: request vs execution

```
User → POST /scans/start → API
         ├─ create scan_states (Mongo)
         ├─ insert scan_execution_tasks (Mongo)
         └─ return scan_id immediately

Scan worker loop (every ~8s)
         ├─ claim task
         ├─ execute_background_scan / run_scan_now / automation
         ├─ update scan_states (Mongo)
         └─ publish realtime_events (Mongo)

API RealtimeBridgeLoop (every ~1.5s)
         ├─ claim realtime_events
         └─ WebSocket → browser
```

## Local development options

| Goal | Command / env |
|------|----------------|
| Full monolith | `uvicorn app.main:app` + `SCAN_EXECUTION_MODE=inline` |
| Match production | Terminal 1: `start_api.py`; Terminal 2: `start_scan_worker.py` |
| API only (no worker) | `dispatch` without worker — tasks queue forever |

See [../developer-guide/runtime-modes.md](../developer-guide/runtime-modes.md).

# Service boundaries

Clear ownership prevents duplicate schedulers, double scans, and OOM on API.

## career-os (API)

**Implemented responsibilities**

| In scope | Out of scope |
|----------|--------------|
| REST API + OpenAPI | Executing `discover_and_store_jobs` in dispatch mode |
| JWT auth, CORS | APScheduler in production dispatch topology |
| WebSocket accept + send | Owning scan task claims |
| Enqueue `scan_execution_tasks` | Long-running Playwright |
| Create initial `scan_states` | |
| RealtimeBridgeLoop | |
| Resume upload, dashboard reads | |
| Rate limiting (when Redis available) | |
| `/health`, `/system/*` | |

## career-os-scan-worker

**Implemented responsibilities**

| In scope | Out of scope |
|----------|--------------|
| Claim/run scan tasks | Public user API |
| APScheduler + scheduled scans | WebSocket server |
| Update `scan_states` | User registration |
| Publish `realtime_events` | |
| Playwright in scan pipelines | |
| Health HTTP | |

## career-os-automation

**Partial responsibilities**

| In scope | Out of scope (today) |
|----------|----------------------|
| Process keep-alive | Primary job discovery |
| Health HTTP | APScheduler |
| Future: dedicated browser jobs | API routes |

## Shared codebase rules

| Module | Callable from |
|--------|---------------|
| `scan_execution.manager` | API routes, scheduler |
| `scan_execution.coordinator` | Worker / inline API only |
| `scan_state_service` | API + worker |
| `realtime_event_store` | Workers publish; API consumes |
| `publish_user_event` | Any process; Mongo publish only on workers |

## Anti-patterns

| Misconfiguration | Symptom |
|------------------|---------|
| `ENABLE_SCHEDULER=true` on API + worker | Duplicate scheduled scans |
| `SCAN_EXECUTION_MODE=inline` on API in prod | API OOM |
| Different `MONGO_URI` per service | Stuck progress, empty queue |
| Public traffic to worker URL | Unnecessary attack surface |

## Frontend boundary

Frontend talks **only** to API origin (`VITE_API_BASE_URL`, `VITE_WS_BASE_URL`). Never call worker URLs for app features.

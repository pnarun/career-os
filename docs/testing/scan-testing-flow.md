# Scan testing flow

## Local (production-like)

Terminal 1:

```bash
cd backend
# .env: SERVICE_MODE=api SCAN_EXECUTION_MODE=dispatch ENABLE_SCHEDULER=false
python start_api.py
```

Terminal 2:

```bash
cd backend
python start_scan_worker.py
```

Frontend → start scan.

## Verify API

1. `POST /scans/start` returns `scan_id` immediately (<2s).
2. `GET /scans/status/{scan_id}` — `progress` increases.
3. API logs: `[SCAN_STATE_API] progress=...`

## Verify worker

1. `[SCAN_TASK] queued` → `claimed` → `completed`
2. `[SCAN_PROGRESS_WRITE]`
3. `[REALTIME_EVENT] published`

## Verify Mongo (Atlas)

Collections:

- `scan_execution_tasks` — status transitions
- `scan_states` — `progress`, `providers`
- `jobs` — new documents

## Dispatch guard

With `SCAN_EXECUTION_MODE=dispatch` on API:

- `POST /fetch-jobs` should return **503** (no inline discovery on API).

## Inline fallback test

```env
SCAN_EXECUTION_MODE=inline
uvicorn app.main:app
```

Scan runs in API process — use only for dev.

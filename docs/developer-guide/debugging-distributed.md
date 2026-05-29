# Debugging distributed runtime

## Symptom matrix

| Symptom | Check |
|---------|-------|
| Task queued forever | Worker running? `MONGO_URI`? |
| 0% progress | `scan_states` in Atlas; `[SCAN_PROGRESS_WRITE]` |
| WS silent, poll OK | Bridge logs, `REALTIME_EVENT` |
| Duplicate scheduled scans | Two schedulers enabled |
| API OOM | `SCAN_EXECUTION_MODE=inline` on API? |

## Tools

1. Atlas — collections `scan_execution_tasks`, `scan_states`, `realtime_events`
2. API logs — `[SCAN_STATE_API]`
3. Worker logs — `[SCAN_TASK]`, `[SCAN_PROGRESS_WRITE]`
4. Frontend — Network WS + `/scans/status` calls

## Local two-process

```bash
# Terminal 1
python start_api.py

# Terminal 2  
python start_scan_worker.py

# frontend .env → localhost API
```

## Monolith shortcut

```env
SCAN_EXECUTION_MODE=inline
uvicorn app.main:app --reload
```

Easier breakpoints; not production behavior.

## Guards

`ensure_worker_may_execute_scans()` — if triggered on API in dispatch, misconfiguration.

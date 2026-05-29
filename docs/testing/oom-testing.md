# OOM and memory testing

**Status:** Manual procedure — no automated OOM suite in CI.

## Why it matters

Scan-worker runs Playwright + Chromium on Render **free tier (512MB)**. Memory spikes cause SIGKILL without Python traceback.

## Preconditions

- Local: `SERVICE_MODE=scan_worker`, `SCAN_EXECUTION_MODE=inline` or dispatch with worker running
- `LOG_LEVEL=INFO`

## Procedure

1. Start worker with memory logging enabled (Render dashboard → Metrics).
2. Trigger a **full multi-provider scan** (LinkedIn + Indeed + Naukri if configured).
3. Watch for:
   - Process exit code **137** (OOM)
   - `[SCAN_PROGRESS_WRITE]` stops mid-scan
   - `scan_execution_tasks` stuck in `running` until claim timeout

## Expected mitigations (implemented)

| Mitigation | Location |
|------------|----------|
| `SCAN_WORKER_MAX_CONCURRENT=1` | config |
| Browser teardown after scan | `sync_runner` / session manager |
| TTL cleanup of heavy artifacts | `retention.py`, indexes |

## Failure simulation

1. Set `SCAN_WORKER_MAX_CONCURRENT=3` locally (do **not** deploy).
2. Enqueue 3 scans simultaneously.
3. Observe memory climb and possible crash.

## Recovery verification

After OOM:

1. Redeploy or restart scan-worker.
2. Confirm stale `running` tasks → `abandoned` after `SCAN_TASK_CLAIM_TIMEOUT_SECONDS`.
3. User can start new scan; polling shows fresh `scan_id`.

## Render notes

Free plan: no guaranteed memory — document incidents in [../operations/incident-handling.md](../operations/incident-handling.md).

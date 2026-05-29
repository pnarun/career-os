# Log interpretation

Structured logs use `extra.event` and bracket prefixes.

## Startup

| Log | Meaning |
|-----|---------|
| `[STARTUP] Runtime profile=` | Mode flags summary |
| `[REALTIME_BRIDGE] started` | Mongo WS bridge active (API) |
| `[TTL_INDEX_CREATED]` | New TTL index |
| `[STORAGE_REPORT]` | Collection estimates |

## Scan path

| Log | Service |
|-----|---------|
| `[SCAN_TASK] queued` | API |
| `[SCAN_TASK] claimed` | Worker |
| `[SCAN_PROGRESS_WRITE]` | Worker → Mongo state |
| `[SCAN_STATE_API]` | API poll read |
| `[REALTIME_EVENT] published` | Worker |
| `[REALTIME_EVENT] delivered` | API bridge |

## Scheduler

| Log | Meaning |
|-----|---------|
| `[SCHEDULED_SCAN_SKIPPED]` | Guard prevented duplicate |
| `[SCHEDULED_SCAN_FAILED]` | Automation error |

## Problems

| Log | Action |
|-----|--------|
| `SCAN_STUCK` | Scan timed out — user should retry |
| `SCAN_FAILED` | Check provider errors in state |
| `scan_states mongo save failed` | Mongo connectivity |
| `OOM` / worker restart | Reduce concurrency |

## Render

Use Render log stream per service — filter `career-os` vs `career-os-scan-worker`.

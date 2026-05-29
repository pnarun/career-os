# Runtime modes

See [../architecture/distributed-runtime.md](../architecture/distributed-runtime.md).

## Quick reference

| `SERVICE_MODE` | Process |
|----------------|---------|
| `api` | HTTP + WS + bridge |
| `scan_worker` | Queue + scheduler |
| `automation_worker` | Heartbeat (+ future browser jobs) |

| `SCAN_EXECUTION_MODE` | Behavior |
|-----------------------|----------|
| `dispatch` | API enqueues, worker runs |
| `inline` | Monolith execution |

## start_*.py defaults

`start_api.py` sets dispatch + scheduler false via `entrypoint.py`.

`start_scan_worker.py` sets scheduler true.

# How scans work (developer)

## Entry points

| Trigger | Route / scheduler | Task kind |
|---------|-------------------|-----------|
| UI background scan | `POST /scans/start` | `background_discover` |
| Manual scan + email | `POST /run-scan-now` | `manual_preferences` |
| Cron | APScheduler | `scheduled_automation` |

## Code path

```
Route → scan_execution_manager
     → dispatcher.create_*_task
     → task_store.insert (Mongo)
     → [dispatch] return OR [inline] coordinator.execute_task
```

Worker:

```
ScanWorkerLoop → claim_next_queued_task
              → coordinator.execute_task
              → background_scan_service / scan_runner_service / job_scan_automation
```

## Progress

`scan_state_service` writes Mongo `scan_states`.

`schedule_scan_realtime` → async WS emit (API) + Mongo events (worker).

## Key files

| File | Role |
|------|------|
| `scan_execution/manager.py` | Facade |
| `scan_execution/dispatcher.py` | Enqueue |
| `scan_execution/coordinator.py` | Execute |
| `scan_execution/worker_loop.py` | Poll |
| `services/background_scan_service.py` | Multi-provider discover |
| `services/scan_runner_service.py` | Manual scan + email |

See [../architecture/mongo-queue.md](../architecture/mongo-queue.md).

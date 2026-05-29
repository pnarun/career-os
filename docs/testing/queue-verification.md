# Queue verification (Mongo)

Production queue: collection **`scan_execution_tasks`** (not Celery when `CELERY_ENABLED=false`).

## Enqueue (API)

1. Start scan from UI.
2. In Atlas, find document:
   - `status`: `queued`
   - `scan_id`, `user_id` set
   - `created_at` BSON Date

## Claim (scan-worker)

Within `SCAN_WORKER_POLL_SECONDS` (~8s):

- `status` → `claimed` → `running`
- `claimed_by` / `claimed_at` populated

## Progress (parallel)

Collection **`scan_states`**:

- `progress_percent` increases
- `GET /scans/status/{scan_id}` matches Mongo

## Complete

- Task: `completed` or `failed`
- `scan_states`: terminal status
- Jobs appear in user's job feed (may take indexing)

## Stuck queue tests

| Scenario | Expected |
|----------|----------|
| Worker down | Tasks stay `queued`; API polling shows queued/low progress |
| Worker crash mid-run | Task → `abandoned` after claim timeout |
| Duplicate enqueue | Coordinator should guard duplicate active scans per user |

## Logs

```
[SCAN_DISPATCH]
[SCAN_WORKER_CLAIM]
[SCAN_PROGRESS_WRITE]
```

See [../architecture/mongo-queue.md](../architecture/mongo-queue.md).

# Queue lifecycle (operations)

Mongo collection: `scan_execution_tasks`

## States

```
queued → claimed → running → completed | failed | abandoned
```

## Operational queries (Atlas)

Find stuck queued (worker down):

```javascript
{ status: "queued" }
```

Find long running:

```javascript
{ status: "running" }
```

## Reclaim behavior

Worker startup calls `reclaim_stale_tasks()`:

- Stale **claimed** → back to **queued**
- Stale **running** → **abandoned**

Tune via `SCAN_TASK_CLAIM_TIMEOUT_SECONDS` and `SCAN_TASK_EXECUTION_TIMEOUT_SECONDS`.

## TTL

Documents expire **14 days** after `created_at` via `scan_execution_tasks_ttl`.

## No manual Redis queue

There is no Celery flower dashboard in production. Atlas + logs are source of truth.

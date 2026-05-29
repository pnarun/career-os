# Mongo verification

## Connection

All three backend services must use **identical** `MONGO_URI` database name (`career_os`).

## Collections to inspect

| Collection | What to check |
|------------|---------------|
| `scan_execution_tasks` | `status`, `worker_id`, timestamps |
| `scan_states` | `progress`, `providers_completed` |
| `realtime_events` | `processed`, `event_type` |
| `jobs` | growth per scan |
| `users` | test accounts |

## TTL indexes

After API startup, Atlas → Indexes:

- `scan_states_ttl`
- `scan_execution_tasks_ttl`
- `realtime_events_ttl`

## Storage report

Startup logs:

```
[STORAGE_REPORT] collection=jobs count=...
```

## Active scan state

During scan, `scan_states.updated_at` should be **BSON Date** (TTL requirement).

Legacy ISO-only documents may not TTL until rewritten.

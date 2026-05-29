# TTL cleanup system

Phase 5 automatic expiry on operational collections.

## Retention table

| Collection | Days | Field |
|------------|------|-------|
| `realtime_events` | 1 | `created_at` |
| `browser_sessions` | 3 | `updated_at` |
| `scan_states` | 7 | `updated_at` |
| `scan_execution_tasks` | 14 | `created_at` |
| `notifications` | 30 | `created_at` |
| `automation_runs` | 30 | `started_at` |

**Jobs are NOT TTL-deleted** — archival planned later.

## Requirements

TTL fields must be **BSON Date**. New writes use `mongo_timestamps` helpers.

Legacy ISO-string documents may not expire until updated.

## Verification

Startup logs:

```
[TTL_INDEX_EXISTS] collection=realtime_events
```

Atlas → collection → Indexes → `expireAfterSeconds`

## Manual cleanup

Rarely needed if TTL healthy. For emergencies, delete by `created_at` filter in Atlas UI.

## Storage monitoring

```
[STORAGE_REPORT] collection=jobs count=...
```

Alert if `jobs` or `scan_states` grow unexpectedly fast.

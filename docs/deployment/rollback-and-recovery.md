# Rollback and recovery

## Per-service rollback (Render)

1. Open service → **Events** / **Deploys**
2. Select last green deploy → **Rollback**

Services are independent — rolling back API does not roll back worker.

## Database rollback

MongoDB has **no automatic code rollback**. Application rollbacks must remain compatible with current schema.

TTL and new fields are generally backward-compatible.

## Recovery playbooks

| Incident | Action |
|----------|--------|
| API down | Rollback API; check `/health` |
| Worker down | Redeploy worker; tasks queue in Mongo |
| Stuck scans | Check `scan_execution_tasks` for stale `running`; wait reclaim or mark failed |
| Atlas full | Check `[STORAGE_REPORT]`; verify TTL indexes exist |
| WS dead, poll works | Check `REALTIME_BRIDGE` logs; `ENABLE_REALTIME` |

## Emergency monolith mode

**Not recommended for prod** but supported:

```env
# Single API process only
SCAN_EXECUTION_MODE=inline
ENABLE_SCHEDULER=true
# Stop scan worker service
```

Use only for short incident response.

## Secrets rotation

| Secret | Action |
|--------|--------|
| `JWT_SECRET_KEY` | Rotating logs out all users |
| `MONGO_URI` | Update all 3 Render services simultaneously |

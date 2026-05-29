# Incident handling

## Severity guide

| SEV | Example |
|-----|---------|
| SEV1 | API down, no login |
| SEV2 | Scans never complete |
| SEV3 | WS broken, poll OK |
| SEV4 | Single provider 403 |

## SEV1 — API down

1. Check Render status + deploy logs
2. Rollback API deploy
3. Verify `MONGO_URI`, `JWT_SECRET_KEY`
4. `curl /health`

## SEV2 — Scans stuck

1. Worker `/health`
2. Same `MONGO_URI`?
3. Worker logs for `[SCAN_TASK] claimed`
4. Atlas `scan_execution_tasks` queue depth
5. Redeploy worker

## SEV3 — Realtime only

1. API `ENABLE_REALTIME`, `REALTIME_BRIDGE_ENABLED`
2. Worker `[REALTIME_EVENT] published`
3. API `[REALTIME_EVENT] delivered`
4. Confirm poll works — communicate to users

## SEV4 — Provider failures

Indeed 403 — **expected** on many hosts. Verify other providers in scan state.

## Communication template

> Scan completed with results from [providers]. Indeed was unavailable due to provider restrictions. Your matches from other boards are in your feed.

## Post-incident

Update [../project-status/current-phase.md](../project-status/current-phase.md) if architecture changed.

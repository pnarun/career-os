# Failure simulation

## Worker down

1. Scale scan-worker to 0 or stop service.
2. Start scan — API returns `scan_id`, progress stays at 0%.
3. Start worker — progress resumes.

**Expected:** Queue holds tasks; no data loss.

## API down

1. Worker continues scheduled scans.
2. Frontend cannot login — expected.

## Wrong MONGO_URI on worker

Symptom: API creates tasks; worker never claims.

**Fix:** Align URI.

## Stale claim

Simulate: kill worker during `claimed` state.

After `SCAN_TASK_CLAIM_TIMEOUT_SECONDS`, task returns to `queued`.

## Bridge disabled

```env
REALTIME_BRIDGE_ENABLED=false
```

Polling must still update UI.

## Realtime only API

Worker events not published if `SERVICE_MODE=api` on worker by mistake — WS silent, poll OK.

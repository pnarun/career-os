# Production startup order

## Recommended sequence

1. Verify **MongoDB Atlas** cluster is running and IP allowlist includes Render (`0.0.0.0/0` or Render egress).
2. Deploy **career-os (API)** — creates indexes, TTL, realtime bridge.
3. Deploy **career-os-scan-worker** — scheduler + task consumer.
4. Deploy **career-os-automation** (optional).
5. Deploy **Vercel frontend** with correct `VITE_*`.
6. Configure **UptimeRobot** → `HEAD https://api/health`.

## Verification per service

### API logs

```
[STARTUP] Runtime profile=... realtime_bridge=True
[REALTIME_BRIDGE] started
[TTL_INDEX_CREATED] or [TTL_INDEX_EXISTS]
[STORAGE_REPORT] collection=...
```

### Scan worker logs

```
[HEALTH_SERVER_STARTED]
[SCHEDULER] APScheduler started
[SCAN_WORKER] loop started
```

### Smoke tests

```bash
curl https://API/health
curl https://SCAN-WORKER/health
# Login on frontend → start background scan → progress moves
```

## Cold start after idle

Render free tier may sleep API. UptimeRobot reduces sleep; first request after wake may be slow — expected.

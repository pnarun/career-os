# Realtime scan architecture

Career OS uses **WebSockets for live scan progress** with **HTTP polling as fallback**. Scan orchestration logic is unchanged; events are emitted from existing Redis scan state updates.

## WebSocket lifecycle

1. Frontend connects to `GET /ws/realtime?token=<JWT>` after login (`frontend/src/lib/realtimeClient.js`).
2. Server validates JWT in `backend/app/realtime/realtime_router.py`, registers socket in `RealtimeConnectionManager`.
3. Server sends `{ "event": "connected" }`.
4. Client sends `ping` every 25s; server replies `{ "event": "pong" }`.
5. On disconnect, client exponential-backoff reconnects (unless auth rejected 4401/4403).
6. `navigator.onLine` triggers reconnect when the browser comes back online.

### Multi-worker fan-out

When `REDIS_ENABLED`, `publish_realtime_event` publishes to Redis channel `career_os:realtime`. The in-process subscriber (`redis_bridge.py`) forwards payloads to local WebSocket connections. Single-worker dev mode sends directly to connected sockets.

## Scan event model

Events are user-scoped (all tabs for the same user receive them).

| Event | When | Key fields |
|-------|------|------------|
| `scan_started` | Scan created | `scan_id`, `progress`, `providers` |
| `provider_started` | Provider fetch begins | `scan_id`, `provider`, `current_provider` |
| `provider_completed` | Provider success/failure | `scan_id`, `provider`, `providers`, `jobs_found` |
| `scan_progress` | Phase/progress update | `scan_id`, `status`, `progress` |
| `scan_completed` | Pipeline success | `scan_id`, `jobs_stored`, `result_summary` |
| `scan_failed` | Fatal scan error | `scan_id`, `reason`, `errors` |

Emission path:

```
scan_state_service (Redis state write)
  → schedule_scan_realtime()
  → scan_event_service.emit_*()
  → publish_user_event() → Redis / WebSocket
```

High-level `scan_started` / `scan_completed` also fire from `background_scan_service.py` for email/summary side effects.

## Fallback polling

`pollScanUntilComplete` (`frontend/src/services/scanBackgroundService.js`):

- If WebSocket is **open**: uses `waitForScanCompletion()` — subscribes to WS events, polls HTTP every **~12s** as safety net.
- If WebSocket is **down**: polls every **1.5–5s** (adaptive by progress).
- Deduplicates concurrent waits per `scan_id`.

Terminal state always confirmed via `GET /scans/status/{scan_id}` when WS reports completion (ensures `result_summary` is present).

## Reliability strategy

### Provider timeouts & retries

`aggregate_jobs` wraps each adapter fetch with:

- `asyncio.wait_for(..., timeout=PROVIDER_FETCH_TIMEOUT_SECONDS)` (default 90s)
- Up to `PROVIDER_FETCH_MAX_RETRIES + 1` attempts with short backoff

One provider failure does **not** block others (existing aggregator isolation).

### Stale scan cleanup

`get_scan_state` calls `expire_stale_scan_state` when a scan runs longer than `SCAN_STALE_SECONDS` (default 2h). Stuck scans are marked failed with `SCAN_STUCK` operational log.

### Partial success

Failed providers appear in `providers_failed`; successful jobs still store. UI surfaces partial success via `ScanProgressPanel` and timeline.

## Observability

| Signal | Location |
|--------|----------|
| API latency / slow requests | `ApiLatencyMiddleware`, logs `slow_api` |
| Cache hit ratio | `cache_service` + `CACHE_HIT_RATIO` logs |
| Provider fetch duration/failures | `operational_metrics.record_provider_fetch` |
| Scan duration | `record_scan_duration` on background scan end |
| Mongo aggregations | `mongo_perf.log_aggregation_duration` |
| WebSocket connect/disconnect | `WEBSOCKET_CONNECTED` / `WEBSOCKET_DISCONNECTED` |
| Metrics snapshot | `GET /system/metrics` |

## Frontend UX (no redesign)

- `ScanProgressPanel` — active provider, per-provider job counts, failed providers.
- `LiveExecutionTimeline` — WS event log (unchanged layout).
- `PageErrorBoundary` — isolates Operations/Insights hub crashes.
- `RealtimeContext` — `activeScans` map + `networkOnline` for degraded mode.

## Future worker architecture (not implemented)

Background scans today use **FastAPI `BackgroundTasks`** + Redis state. A future Celery/RQ worker would:

1. Keep the same `scan_state_service` Redis schema.
2. Publish the same WebSocket events via Redis pub/sub.
3. Leave HTTP `POST /scans/start` + `GET /scans/status/{id}` contract unchanged.

No Kafka/Celery is required for current scale.

## Related docs

- [Background scans](./background-scans.md)
- [Redis caching](./redis-caching.md)
- [Frontend optimization](./frontend-optimization.md)

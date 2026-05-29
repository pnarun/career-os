# Realtime bridge (developer)

## Components

| File | Role |
|------|------|
| `services/realtime_event_store.py` | Mongo insert/claim |
| `realtime/realtime_bridge_loop.py` | API poll loop |
| `realtime/websocket_manager.py` | `publish_user_event` |
| `realtime/scan_state_realtime.py` | Scan state → events |

## Publish path (worker)

```python
publish_user_event(user_id, "scan_progress", ...)
  → if not api: publish_realtime_event(...)  # Mongo
  → redis_bridge.publish_realtime_event(...)  # local WS no-op on worker
```

## Consume path (API)

```python
RealtimeBridgeLoop
  → claim_unprocessed_events()
  → realtime_manager.send_to_user()
```

## Local test

Run API + worker with dispatch. Watch API logs for `delivered` when worker `published`.

## Disable bridge

```env
REALTIME_BRIDGE_ENABLED=false
```

Polling must still work.

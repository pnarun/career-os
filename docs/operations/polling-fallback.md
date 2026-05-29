# Polling fallback system

## Why it exists

WebSockets are **best-effort** in production:

- Render cold starts
- Mobile browser sleep
- Tab backgrounding
- Cross-service realtime adds ~1.5s bridge latency

**Polling is the reliability layer.** WebSocket is the enhancement.

## Frontend behavior

`scanBackgroundService.js`:

- Polls `GET /scans/status/{scan_id}` every 1.5–10s (adaptive)
- Uses WebSocket when `realtimeClient.isOpen()`

## Backend behavior

`get_scan_state` reads Mongo `scan_states` directly — no stale cache for active scans.

## Operations expectation

| Symptom | Diagnosis |
|---------|-----------|
| Poll works, WS dead | Bridge or `ENABLE_REALTIME` |
| Neither works | Worker / Mongo state |
| WS only, poll disabled | Frontend bug — should not happen |

## Do not remove polling

Removing poll would break mobile and post-sleep UX.

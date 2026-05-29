# Render cold starts

## What users see

- First request after idle: **5–30+ seconds**
- WebSocket may reconnect
- Scan still completes — may start slowly

## Mitigation

| Tactic | Status |
|--------|--------|
| UptimeRobot `HEAD /health` | **Implemented** |
| Render Starter (paid) | Reduces sleep |
| User education | Set expectations in support |

## API vs worker

Both can sleep on free tier. If API awake but worker asleep, scans queue until worker wakes on health check or request.

Consider UptimeRobot on worker health URL if scans stall after idle.

## Not a bug

Cold start is platform behavior — document in support macros.

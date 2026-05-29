# Realtime verification

## Prerequisites

- API: `ENABLE_REALTIME=true`, `REALTIME_BRIDGE_ENABLED=true`
- Worker: publishing scans
- Frontend connected to `wss://API/...`

## Browser

1. Open DevTools → Network → WS.
2. Confirm connection after login.
3. Start scan — messages with `event: scan_progress`.

## Logs (production)

**Worker:**

```
[REALTIME_EVENT] published type=scan_progress
```

**API:**

```
[REALTIME_BRIDGE] started
[REALTIME_EVENT] delivered recipients=1
```

## Polling fallback test

1. Block WS in devtools OR set slow network.
2. Confirm `GET /scans/status` still updates UI.

## Latency expectations

| Path | Typical delay |
|------|----------------|
| Mongo state → poll | 0–3s (poll interval) |
| Mongo event → WS | 1–3s (bridge poll) |

## Failure: WS works, poll stuck

- Check `scan_states` in Atlas — worker writing?
- Not a bridge issue — worker/state bug.

## Failure: poll works, WS silent

- Check bridge logs on API
- Worker publishing events?
- `ENABLE_REALTIME` on API?

# Frontend integration testing

## Env

```bash
cd frontend
cp .env.example .env
# VITE_API_BASE_URL=http://127.0.0.1:8000
# VITE_WS_BASE_URL=ws://127.0.0.1:8000
npm run dev
```

## Services used

| Client module | Backend |
|---------------|---------|
| `scanBackgroundService.js` | `/scans/start`, `/scans/status` |
| `RealtimeContext.jsx` | WebSocket |
| `scanRealtime.js` | Event mapping |

## Dual-path progress

`pollScanUntilComplete` uses WS when open, else HTTP poll.

Verify both paths in QA matrix.

## Build preview

```bash
npm run build && npm run preview
```

Confirms production bundle + API URLs.

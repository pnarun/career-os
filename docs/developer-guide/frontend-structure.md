# Frontend structure

```text
frontend/src/
├── pages/           # Route-level views
├── components/      # UI + feature components
├── services/        # API clients
├── context/         # Auth, Realtime
└── lib/             # apiClient, scanRealtime
```

## API base URL

`VITE_API_BASE_URL` — build-time on Vercel.

## Scan progress

- `services/scanBackgroundService.js` — poll
- `context/RealtimeContext.jsx` — WebSocket
- `components/scans/ScanProgressPanel.jsx` — UI

See [../frontend/frontend-architecture.md](../frontend/frontend-architecture.md).

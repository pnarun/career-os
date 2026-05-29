# Architecture diagrams

Central reference for topology and flows. See linked docs for narrative detail.

---

## 1. Overall topology

```mermaid
flowchart LR
  U[User] --> V[Vercel SPA]
  V --> API[career-os API]
  API --> M[(MongoDB Atlas)]
  SW[career-os-scan-worker] --> M
  AW[career-os-automation] --> M
  SW -->|publish events| M
  API -->|RealtimeBridge| M
  API -->|WSS| V
```

---

## 2. Scan execution flow

```mermaid
sequenceDiagram
  participant UI as Frontend
  participant API as career-os API
  participant M as MongoDB
  participant W as scan-worker

  UI->>API: POST start scan
  API->>M: insert scan_execution_tasks (queued)
  API->>M: init scan_states
  API-->>UI: scan_id
  loop Poll + WS
    UI->>API: GET /scans/status/{id}
  end
  W->>M: claim task (queued→claimed→running)
  W->>W: Playwright providers
  W->>M: update scan_states progress
  W->>M: publish realtime_events
  API->>M: bridge poll → WebSocket
  W->>M: task completed
```

---

## 3. Realtime event flow

```mermaid
flowchart LR
  W[scan-worker] -->|insert| E[(realtime_events)]
  API[API RealtimeBridgeLoop] -->|claim unprocessed| E
  API --> WS[WebSocketManager]
  WS --> FE[Browser]
  FE -->|fallback poll| API
```

---

## 4. Queue lifecycle

```
queued → claimed → running → completed
                          ↘ failed
                          ↘ abandoned (timeout/crash)
```

Mongo collection: `scan_execution_tasks`.

---

## 5. Worker ownership

```text
┌─────────────────────┬──────────────────────────────────────────┐
│ career-os (API)     │ REST, auth, WS, enqueue, bridge, NO scans  │
│ career-os-scan-worker│ queue consumer, scheduler, Playwright scans│
│ career-os-automation │ heartbeat; future browser job dequeue      │
└─────────────────────┴──────────────────────────────────────────┘
```

---

## 6. Mongo synchronization model

| Collection | Writer(s) | Reader(s) | Purpose |
|------------|-----------|-----------|---------|
| `scan_execution_tasks` | API enqueue, worker update | worker | Work queue |
| `scan_states` | worker (primary) | API poll | Progress % |
| `realtime_events` | worker/services | API bridge | WS fan-out |
| `jobs` | worker | API, UI | Results |

Single `MONGO_URI` — shared Atlas database.

---

## 7. Frontend → backend → worker

```mermaid
flowchart TB
  FE[React SPA]
  FE -->|JWT REST| API[FastAPI API]
  FE -->|WSS + poll| API
  API -->|dispatch only| Q[(scan_execution_tasks)]
  W[scan-worker] -->|poll claim| Q
  W -->|write| S[(scan_states)]
  API -->|read| S
  W -->|publish| R[(realtime_events)]
  API -->|bridge| R
```

---

## ASCII: deployment on Render

```text
                    ┌──────────────┐
                    │   Vercel     │
                    │  frontend    │
                    └──────┬───────┘
                           │ HTTPS / WSS
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌─────────────┐ ┌──────────────┐
        │ career-os│ │scan-worker  │ │ automation   │
        │  (API)   │ │             │ │   worker     │
        └────┬─────┘ └──────┬──────┘ └──────┬───────┘
             └──────────────┼───────────────┘
                            ▼
                    ┌───────────────┐
                    │ MongoDB Atlas │
                    └───────────────┘
```

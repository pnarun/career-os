# Worker lifecycle

## scan-worker

| Event | Behavior |
|-------|----------|
| Deploy | New container, scheduler reload, loop starts |
| Idle | Polls Mongo every ~8s |
| Task claimed | Runs pipeline, updates state, publishes events |
| SIGTERM | Graceful stop — drains in-flight up to timeout |
| OOM kill | Render restarts — stale tasks reclaimed |

## automation worker

| Event | Behavior |
|-------|----------|
| Deploy | Heartbeat loop + health server |
| Idle | Low CPU heartbeat |
| Future | Will dequeue browser jobs |

## API (not a worker but related)

Does not claim scan tasks in dispatch mode. Runs RealtimeBridgeLoop only.

## Scaling workers

Add Render instance with same env — Mongo claim is safe for multiple consumers.

Watch total Playwright RAM.

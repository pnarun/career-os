# Mongo event system

Collection: `realtime_events`

## API

```python
from app.services.realtime_event_store import (
    publish_realtime_event,
    claim_unprocessed_events,
)
```

## When to publish

Automatically from `publish_user_event` on non-API processes.

Do not publish from API (bridge would duplicate WS).

## Schema

See [../architecture/realtime-sync.md](../architecture/realtime-sync.md).

## TTL

1 day — `realtime_events_ttl` on `created_at`.

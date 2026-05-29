# Upstash Redis setup (optional)

**Status:** **Partial** — optional response cache; **not** required for scan queue or realtime in production.

## When to use

- Cache dashboard/analytics responses
- Reduce repeated Mongo reads on hot endpoints

## When not required

Production path uses:

- Mongo `scan_execution_tasks` (queue)
- Mongo `scan_states` (progress)
- Mongo `realtime_events` (cross-service WS)

With `REDIS_ENABLED=false` and no Upstash, app still functions.

## Setup

1. Create Upstash Redis database (REST API).
2. Set on API (and optionally workers if caching there):

```env
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...
```

3. Keep `REDIS_ENABLED=false` unless using local/socket Redis for dev features.

## TTLs

See `CACHE_*_TTL` in [../configuration/environment-variables.md](../configuration/environment-variables.md).

## Warning

Do not assume Redis pub/sub for realtime — production uses Mongo bridge (Phase 6).

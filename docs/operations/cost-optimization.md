# Cost optimization

## Free tier stack

| Service | Cost |
|---------|------|
| Vercel hobby | $0 |
| Render free/starter | $0–7/mo per service |
| Atlas M0 | $0 |
| Upstash free tier | $0 optional |

## Design savings

- Mongo queue vs always-on Redis
- Mongo realtime vs Redis pub/sub
- TTL prevents Atlas upgrade pressure
- Dispatch mode prevents oversized API instances

## When to spend

| Upgrade | Trigger |
|---------|---------|
| Render Starter API | Cold starts hurt UX |
| Render Starter worker | OOM or queue backlog |
| Atlas M2 | Storage >400MB sustained |
| Upstash paid | Cache hit rate justifies |
| Redis + Celery | High scan volume |

## Avoid

- Running scheduler on API (duplicate work + need bigger API)
- `SCAN_WORKER_MAX_CONCURRENT` >1 on 512MB instances
- Storing HTML debug snapshots in prod Mongo (logs gitignored locally)

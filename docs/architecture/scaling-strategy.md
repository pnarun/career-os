# Scaling strategy

Honest tiered plan — what works today vs what requires paid infrastructure.

## Today (implemented)

| Layer | Strategy |
|-------|----------|
| API | Horizontal possible; stateless except WebSockets |
| Scan work | Vertical on scan worker; `SCAN_WORKER_MAX_CONCURRENT` |
| Queue | Mongo `scan_execution_tasks` poll |
| Progress | Mongo `scan_states` |
| Realtime | Mongo `realtime_events` + API bridge |
| Cache | Upstash REST (optional) |
| Data growth | TTL on operational collections |

## Near-term (code exists, not prod-default)

| Layer | Mechanism | Status |
|-------|-----------|--------|
| Task queue | Celery + Redis | **Partial** |
| Realtime | Redis pub/sub | **Partial** |
| Rate limit | Redis | **Partial** (may degrade) |

## Medium-term (planned)

| Need | Approach |
|------|----------|
| Faster queue | Redis/Celery replacing Mongo poll |
| Dedicated Playwright | automation worker dequeue |
| Multiple scan workers | Mongo claim already safe for N workers |
| WS scale-out | Sticky sessions or Redis pub/sub required |
| Job archival | Cold storage after 90 days ([job retention](../developer-guide/repository-structure.md)) |

## Scaling scan workers

Mongo atomic claim supports **multiple scan worker instances**:

- Increase Render instance count OR
- Second Web Service with same env

Watch Atlas connection limits and Playwright RAM per instance.

## API scaling caveats

| Concern | Detail |
|---------|--------|
| WebSockets | Per-process connection pool; bridge on each replica |
| Sticky sessions | Required if multiple API instances and WS |
| Cold starts | Render free tier — first request slow |

## Cost ladder (typical)

1. **Free** — Atlas M0, Render free/starter, Vercel hobby
2. **Starter** — Render paid API + worker, Atlas M2
3. **Growth** — Redis, dedicated worker plan, Atlas M10+

## What not to do prematurely

- Kubernetes for current user scale
- Multi-repo split before team size justifies it
- Redis requirement before traffic justifies cost

See [../roadmap/future-roadmap.md](../roadmap/future-roadmap.md).

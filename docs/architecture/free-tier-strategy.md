# Free-tier optimization strategy

Career OS production is designed to run on **Render free/starter**, **Vercel**, and **MongoDB Atlas M0 (512MB)** without mandatory Redis or Celery.

## Design decisions driven by free tier

| Decision | Why |
|----------|-----|
| Mongo scan queue | No Redis monthly cost |
| Mongo realtime bus | Cross-service WS without Redis pub/sub |
| Scan worker as Web Service | Background Workers require paid plan |
| Health HTTP on workers | Render kills processes without open PORT |
| API `ENABLE_SCHEDULER=false` | Avoid duplicate cron + API OOM |
| `SCAN_WORKER_MAX_CONCURRENT=1` | RAM limit on 512MB instances |
| TTL indexes | Prevent Atlas filling with ops data |
| Polling fallback | WS unreliable on sleep/cold start |
| Upstash optional | REST cache without always-on Redis |

## Render free tier behaviors

| Behavior | Impact |
|----------|--------|
| Service sleep | UptimeRobot pings API `/health` |
| Slow cold start | First scan after idle may delay |
| CPU throttling | Long Playwright runs |
| No persistent disk | Browser sessions in Mongo `browser_sessions` |

## Atlas M0 limits

| Limit | Mitigation |
|-------|------------|
| 512MB storage | TTL on `scan_states`, tasks, events, notifications |
| Connection count | 3 services × pool — monitor connections |
| Shared CPU | Index discipline, no full collection scans in hot paths |

## What we disabled in production blueprint

```env
REDIS_ENABLED=false
CELERY_ENABLED=false
QUEUE_SCANS_ENABLED=false
```

## Operational tradeoffs (transparent)

| Tradeoff | User-visible effect |
|----------|---------------------|
| Mongo poll queue | Up to ~8s before worker picks task |
| Realtime bridge ~1.5s | WS slightly behind Mongo state |
| Single concurrent scan | One heavy scan at a time per worker |
| Indeed / anti-bot | Some providers may return 403 — partial results |

## When to upgrade

| Signal | Upgrade |
|--------|---------|
| Atlas >400MB steady | M2 + review TTL |
| Scan backlog growing | Second worker or faster poll |
| WS scale needs | Paid Redis + pub/sub |
| Always-on latency | Render Starter on API + worker |

See [../operations/cost-optimization.md](../operations/cost-optimization.md).

# Memory management

Heavy memory use comes from **Playwright Chromium**, **job parsing**, and **AI batch scoring** — not from FastAPI itself.

## Risk by process

| Process | Primary RAM drivers |
|---------|---------------------|
| API | Upload parsing, accidental inline scans, WS buffers |
| scan-worker | Playwright + multi-provider fetch + scoring |
| automation-worker | Playwright (future); currently low |

## Protections (implemented)

| Mechanism | Where |
|-----------|--------|
| `SCAN_EXECUTION_MODE=dispatch` | API does not run full scan pipeline |
| `ensure_worker_may_execute_scans()` | Blocks API dispatch-mode execution |
| `SCAN_WORKER_MAX_CONCURRENT=1` | Worker semaphore |
| `gc.collect()` after scans | Coordinator cleanup |
| `MEMORY_BEFORE_SCAN` / `MEMORY_AFTER_SCAN` logs | Diagnostics |
| `/health?detail=1` memory snapshot | API ops |

## OOM scenarios still possible

| Scenario | Service |
|----------|---------|
| LinkedIn + 6 providers one scan | scan-worker |
| Headed Playwright on cloud | Unsupported — headless only |
| Large PDF resume in API | API |
| Multiple API replicas each running scheduler | Misconfiguration |

## Render 512MB guidance

- Keep **one** scan worker instance with `MAX_CONCURRENT=1`
- Do not enable inline scans on API in production
- Monitor `[SCAN_WORKER]` and Render metrics dashboard
- Restart worker after deploy (automatic on Render)

## Diagnostics

```bash
# API detailed health
curl "https://your-api.onrender.com/health?detail=1"

# Logs
[MEMORY_BEFORE_SCAN] [MEMORY_AFTER_SCAN]
```

See [../testing/oom-testing.md](../testing/oom-testing.md).

# Worker verification

## Health

```bash
curl https://career-os-scan-worker.onrender.com/health
# {"status":"ok","service":"scan_worker"}
```

## Scheduler ownership

Only **one** service should log scheduler start in production:

```
[SCHEDULER] Starting APScheduler owner=scan_worker
```

API should log:

```
Scheduler not started owner=none
```

## Queue drain

1. Stop worker.
2. Start scan from UI — task stays `queued` in Mongo.
3. Start worker — task becomes `claimed` within ~8s.

## Concurrent scan limit

With `SCAN_WORKER_MAX_CONCURRENT=1`, second task waits until first completes.

## OOM watch

During heavy scan, monitor Render memory metrics. If OOM, keep concurrency at 1.

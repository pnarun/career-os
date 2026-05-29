# Safe deploy checklist

## Before merge

- [ ] `SCAN_EXECUTION_MODE=dispatch` paths tested locally with worker
- [ ] No new inline scan calls bypassing `scan_execution_manager`
- [ ] Mongo migrations/indexes backward compatible
- [ ] Env vars documented in [environment-variables.md](../configuration/environment-variables.md)

## Deploy order

1. API (`career-os`)
2. scan-worker (`career-os-scan-worker`)
3. automation (if changed)
4. Vercel frontend (if `VITE_*` changed)

## After deploy

- [ ] `/health` all services
- [ ] One background scan E2E
- [ ] Check `[STORAGE_REPORT]` and TTL logs
- [ ] No duplicate scheduler logs on API

## Rollback

Rollback services independently — see [rollback-and-recovery.md](../deployment/rollback-and-recovery.md).

## Do not

- Force push production
- Rotate `JWT_SECRET_KEY` without comms
- Enable Celery in prod without Redis plan

# Common pitfalls

1. **Different `MONGO_URI` per Render service** — queue/state/events split-brain.
2. **`ENABLE_SCHEDULER=true` on API and worker** — duplicate cron scans.
3. **`SCAN_EXECUTION_MODE=inline` on production API** — OOM.
4. **Forgetting to redeploy worker** after scan logic changes.
5. **Expecting WS without bridge on API** — workers don't hold WS connections.
6. **Removing HTTP polling** — breaks mobile/sleep scenarios.
7. **Indeed 403 as P0 bug** — often environmental, partial scans OK.
8. **TTL on ISO strings** — must use BSON Date fields for new writes.
9. **Calling worker URL from frontend** — only API origin.
10. **Celery enabled without Redis** — misconfigured infra.

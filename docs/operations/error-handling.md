# Error handling

## Backend patterns

### HTTP routes

- `HTTPException` for client errors (400, 401, 404)
- Domain exceptions mapped in routes:
  - `UserPreferencesNotFoundError` → 404
  - `UserPreferencesServiceError` → 400/500
  - `ScanRunnerError` → scan failure recorded, 4xx/5xx as appropriate

### Service layer

```python
try:
    await operation()
except SpecificError as exc:
    logger.error("[DOMAIN_FAILED] ...", exc)
    raise ServiceError("user message") from exc
except Exception:
    logger.exception("[DOMAIN_FAILED] ...")
    raise
```

### Automation runs

Long workflows record outcome in `automation_runs`:

- `start_automation_run()` → `complete_automation_run(status=completed|partial|failed)`
- Partial success when some providers fail but jobs stored

### Scan failures

`scan_runner_service` emits `scan_failed` realtime event and logs `[SCAN_FAILED]` with reason:

- `resume_not_found`
- `inactive` preference
- Provider total failure

Scheduled scans **skip** (info log) when:

- Already running
- Inactive
- Missing `resume_id`

### WebSocket rejections

| Code | Reason |
|------|--------|
| 4401 | Missing/invalid token |
| 4403 | Inactive user |

Pattern: accept then close (avoids uvicorn 403 log noise).

### Circuit breakers

Provider failures increment breaker; open circuit skips provider until cooldown — scan continues with other sources.

## Frontend patterns

### API errors

`parseErrorMessage(response)` extracts FastAPI `detail`.

Auth forms show inline `error` state.

### Network

- `apiFetch` refresh on 401 once
- `BackendWakeContext` → `failed` status + retry button on landing
- `realtimeClient` refresh on 4401, stop reconnect if refresh fails

### React Query

Dashboard and feeds use query error boundaries; manual retry via refetch.

### User-facing copy

| State | Message pattern |
|-------|-----------------|
| Cold start | “Waking up our servers…” |
| API missing | “VITE_API_BASE_URL is not set on Vercel” |
| Scan failed | Toast + timeline entry from realtime |

## Error codes reference

| Symptom | HTTP | Action |
|---------|------|--------|
| Unauthorized | 401 | Refresh or re-login |
| Not found | 404 | Check id / ownership |
| Validation | 422 | Fix request body |
| Rate limit | 429 | Back off |
| Server error | 500 | Check `/logs`, Render status |

## Related

- [Logging](./logging.md)
- [Troubleshooting](../troubleshooting/common-issues.md)

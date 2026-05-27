# Logging system

## Overview

Career OS uses **structured JSON logging** to stdout with an in-memory ring buffer for the built-in log viewer.

**Config:** `app/core/logging_config.py`  
**Buffer:** `app/core/log_buffer.py`  
**Startup:** `configure_logging()` in `main.py`

## Log format

Each line is JSON:

```json
{
  "timestamp": "2026-05-27T08:45:40.658736+00:00",
  "user": "arunpn866@gmail.com",
  "service": "career-os-api",
  "level": "INFO",
  "logger": "app.services.scheduler_service",
  "message": "[SCHEDULER] Initialized",
  "event": "log_scheduler_startup_summary"
}
```

Optional fields: `provider`, `scan_id`, `status`, `event` (structured marker).

## User attribution

`UserContextMiddleware` + `set_request_user()` on authenticated HTTP and WebSocket set `user` to email. Unauthenticated requests log as `system`.

## Viewing logs

| URL | Format |
|-----|--------|
| `GET /logs` | HTML table with filters |
| `GET /logs/api` | JSON array |
| `GET /logs/export` | CSV download |
| `GET /system/logs` | Alias |

**Filters:** user, level, limit (10–500)

![Log viewer](../assets/screenshots/api-logs-viewer.png)

## Log levels

| Level | Use |
|-------|-----|
| DEBUG | Health pings (dev), invalid WS token |
| INFO | Startup, scheduler, scan lifecycle |
| WARNING | Skipped scans, provider degradation |
| ERROR | Scan failures, automation errors |
| EXCEPTION | Stack traces via `logger.exception` |

Set via `LOG_LEVEL` env.

## Noise reduction

Third-party loggers (urllib3, httpx, motor, apscheduler) elevated to WARNING in `logging_config.py`.

## Health debug line

`[HEALTH] keepalive ping` at DEBUG when `ENVIRONMENT=development` or `LOG_LEVEL=DEBUG`.

## Render integration

Logs stream to Render dashboard → Logs tab. No persistent retention on free tier — export CSV for incidents.

## Best practices

1. Use `logger.info("...", extra={"event": "my_event"})` for grep-friendly markers
2. Prefix domains: `[SCHEDULER]`, `[SCAN_FAILED]`, `[REALTIME]`
3. Never log tokens, passwords, OTP
4. Use `logger.exception` in `except` blocks for stack traces

## Related

- [Error handling](./error-handling.md)
- [Troubleshooting](../troubleshooting/common-issues.md)

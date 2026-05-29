# Playwright verification

## Local setup

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

Set in `.env`:

```env
ENABLE_PLAYWRIGHT=true
PLAYWRIGHT_HEADLESS=true
```

## Smoke test (headed, local only)

```env
PLAYWRIGHT_HEADLESS=false
```

Run a LinkedIn-only scan from UI or API. Confirm screenshots under `app/automation/logs/screenshots/` when logging enabled.

## Production constraints

| Constraint | Detail |
|------------|--------|
| Headed browsers | **Not available** on Render Linux (`headed_session_prep_available` false) |
| Datacenter IP | Indeed often **403** — partial |
| LinkedIn | Requires valid `browser_sessions` (extension pairing) |

## Verification checklist

- [ ] Chromium launches on scan-worker (`[SCAN_WORKER]` logs)
- [ ] LinkedIn jobs page loads (`after_jobs_load` snapshot if enabled)
- [ ] Session invalid detected → user prompted to reconnect extension
- [ ] Browser context closed after scan (no zombie processes locally)

## Automation worker

`career-os-automation` today: heartbeat + health. Full Playwright dequeue is **Partial** — most automation runs on scan-worker during scans.

See [../architecture/automation-worker.md](../architecture/automation-worker.md).

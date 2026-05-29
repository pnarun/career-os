# How automation works (developer)

## Layers

| Layer | Path |
|-------|------|
| HTTP routes | `api/routes/automation.py` |
| Service | `services/automation_service.py` |
| Browser | `automation/browser/` |
| Sessions | `services/browser_session_store.py` (Mongo) |

## LinkedIn

Extension pairs session → API stores `browser_sessions` → Playwright uses `storage_state`.

## Scan vs automation worker

**Today:** Most Playwright during **scan pipelines** on scan-worker.

**Planned:** Long-lived automation jobs on automation worker.

## Subprocess mode

`AUTOMATION_WORKER_MODE=subprocess` — local dev pattern; cloud uses in-process Playwright on workers.

See [../automation/playwright-automation.md](../automation/playwright-automation.md).

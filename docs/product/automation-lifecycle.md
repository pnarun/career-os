# Automation lifecycle (product)

**Status:** **Partial** — LinkedIn session pairing and scan-time Playwright are production paths; dedicated long-running automation worker jobs are **Planned**.

## What users do

1. Install **Career Lens** Chrome extension.
2. Connect LinkedIn in Career OS → extension syncs session.
3. Run job scans (automation fetches where session exists).
4. Optional: assisted apply flows where enabled (`ASSISTED_APPLY_ENABLED`).

## States users see

| UI state | Meaning |
|----------|---------|
| LinkedIn connected | Valid `browser_sessions` |
| Reconnect required | Session expired or invalid |
| Scan running | Worker fetching via browser |
| Scan complete | Jobs in feed |

## What we do not promise yet

- Fully unattended apply on all boards
- 24/7 browser sessions on cloud workers
- Indeed reliability from datacenter IPs

## Technical path (transparent)

Extension → API stores session → scan-worker Playwright → jobs DB.

Future: **career-os-automation** dequeues dedicated automation runs.

See [../architecture/automation-worker.md](../architecture/automation-worker.md).

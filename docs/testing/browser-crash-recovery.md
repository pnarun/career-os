# Browser crash recovery

## What can crash

- Chromium OOM on worker
- Playwright timeout on slow board
- LinkedIn session expiry mid-scan

## Symptoms

- `scan_execution_tasks.status` = `running` with no progress updates
- Logs stop after Playwright step
- Screenshots show login wall / `session_invalid`

## Automated recovery

| Mechanism | Behavior |
|-----------|----------|
| Claim timeout | `SCAN_TASK_CLAIM_TIMEOUT_SECONDS` → task `abandoned` |
| Scan stale | `SCAN_STALE_SECONDS` — API may mark scan failed |
| User retry | New scan gets new `scan_id` |

## Manual QA steps

1. Start scan; kill Chromium process locally (`pkill chromium`) mid-run.
2. Wait for claim timeout (or restart worker).
3. Confirm UI shows failure or allows new scan (not infinite spinner).
4. Re-pair LinkedIn if `session_invalid` snapshot.

## Session invalid path

Extension → resync → `browser_sessions` updated → retry scan.

See [../automation/linkedin-session-management.md](../automation/linkedin-session-management.md).

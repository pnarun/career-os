# Scheduler testing

## Production rule

Scheduler runs on **scan-worker only**.

## Verify registration

Worker logs on boot:

```
[SCHEDULER] Preference scan jobs: N
```

## Trigger manual

Use UI scheduled scan time OR temporarily set preference to trigger soon.

## Catch-up

`SCHEDULER_STARTUP_CATCHUP=false` on worker (default in `start_scan_worker.py` defaults) — overdue scans only on cron, not every deploy.

## Duplicate prevention

- API `ENABLE_SCHEDULER=false`
- `has_active_task_for_preference` dedup for scheduled tasks
- `_running_scans` set in scheduler service (per-process)

## Email guard

`scheduled_scan_recently_completed` may skip duplicate emails — check logs:

```
[SCHEDULED_SCAN_SKIPPED] reason=recent_slot_completed
```

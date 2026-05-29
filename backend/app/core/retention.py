"""MongoDB retention policy constants (Atlas free-tier protection)."""

from __future__ import annotations

SCAN_STATE_RETENTION_DAYS = 7
SCAN_TASK_RETENTION_DAYS = 14
BROWSER_SESSION_RETENTION_DAYS = 3
NOTIFICATION_RETENTION_DAYS = 30
REALTIME_EVENT_RETENTION_DAYS = 1
AUTOMATION_RUN_RETENTION_DAYS = 30

# Future job archival — not implemented in Phase 5 (see job_retention.py).
JOB_ARCHIVAL_RETENTION_DAYS = 90


def days_to_expire_seconds(days: int) -> int:
    """Convert retention days to MongoDB TTL expireAfterSeconds."""
    return max(1, int(days)) * 24 * 60 * 60

"""Job collection retention — archival placeholder only (Phase 5)."""

from __future__ import annotations

from app.core.retention import JOB_ARCHIVAL_RETENTION_DAYS

# TODO(phase-future): Archive jobs older than JOB_ARCHIVAL_RETENTION_DAYS (~90 days)
# to cold storage or aggregated summaries. Do NOT delete jobs in Phase 5 — user-facing
# history depends on the jobs collection.

__all__ = ["JOB_ARCHIVAL_RETENTION_DAYS"]

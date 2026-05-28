"""Guards against duplicate scan emails within a schedule window."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.user_preferences import UserPreferencesDocument
from app.services.scheduler_service import (
    _hours_since_last_email,
    _uses_six_hour_schedule,
)

# Slightly under 6h so four slots per day still work, but same-slot duplicates are blocked.
SIX_HOUR_EMAIL_COOLDOWN_HOURS = 5.5
DAILY_EMAIL_COOLDOWN_HOURS = 20.0


def email_sent_within_cooldown(
    preferences: UserPreferencesDocument,
    *,
    now_utc: datetime | None = None,
) -> bool:
    """True when a scan email was already sent recently for this preference."""
    now_utc = now_utc or datetime.now(timezone.utc)
    hours = _hours_since_last_email(preferences, now_utc)
    if hours is None:
        return False
    min_hours = (
        SIX_HOUR_EMAIL_COOLDOWN_HOURS
        if _uses_six_hour_schedule(preferences)
        else DAILY_EMAIL_COOLDOWN_HOURS
    )
    return hours < min_hours


def scheduled_scan_recently_completed(
    preferences: UserPreferencesDocument,
    *,
    now_utc: datetime | None = None,
) -> bool:
    """
    Skip redundant scheduled scans when the last email for this slot was just sent
    (e.g. APScheduler + external cron both firing).
    """
    return email_sent_within_cooldown(preferences, now_utc=now_utc)

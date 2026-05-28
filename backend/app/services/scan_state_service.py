"""Persist in-flight scan progress in Redis (1h TTL)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.models.scan_state import (
    TRACKED_SCAN_PROVIDERS,
    ScanProviderState,
    ScanState,
)
from app.core.config import settings
from app.services.cache_service import delete, get_json, set_json
from app.realtime.scan_state_realtime import schedule_scan_realtime

logger = logging.getLogger(__name__)

SCAN_STATE_TTL_SECONDS = 3600
_KEY_PREFIX = "scan:state:"


def _state_key(scan_id: str) -> str:
    return f"{_KEY_PREFIX}{scan_id}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_providers() -> dict[str, ScanProviderState]:
    return {name: ScanProviderState(name=name, status="pending") for name in TRACKED_SCAN_PROVIDERS}


def _load(scan_id: str) -> ScanState | None:
    raw = get_json(_state_key(scan_id))
    if not raw:
        return None
    return ScanState.model_validate(raw)


def _save(state: ScanState) -> None:
    set_json(_state_key(state.scan_id), state.model_dump(mode="json"), SCAN_STATE_TTL_SECONDS)


def create_scan_state(*, scan_id: str, user_id: str) -> ScanState:
    state = ScanState(
        scan_id=scan_id,
        user_id=user_id,
        status="started",
        progress=0,
        providers=_default_providers(),
        started_at=_utc_now_iso(),
    )
    _save(state)
    schedule_scan_realtime(state, "scan_started")
    logger.info(
        "SCAN_STARTED scan_id=%s user_id=%s",
        scan_id,
        user_id,
        extra={"event": "scan_started", "scan_id": scan_id, "user_id": user_id},
    )
    return state


def _parse_iso_age_seconds(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        from datetime import datetime

        started = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - started).total_seconds()
    except ValueError:
        return None


def _is_stale_inflight(
    state: ScanState, max_age_seconds: int | None = None
) -> bool:
    max_age_seconds = max_age_seconds or settings.SCAN_STALE_SECONDS
    if state.status in ("completed", "failed"):
        return False
    age = _parse_iso_age_seconds(state.started_at)
    return age is not None and age > max_age_seconds


def expire_stale_scan_state(
    scan_id: str, *, max_age_seconds: int | None = None
) -> bool:
    max_age_seconds = max_age_seconds or settings.SCAN_STALE_SECONDS
    """Mark long-running scans as failed and remove Redis state."""
    state = _load(scan_id)
    if state is None or not _is_stale_inflight(state, max_age_seconds):
        return False
    logger.error(
        "SCAN_STUCK scan_id=%s user_id=%s age_seconds=%.0f status=%s",
        scan_id,
        state.user_id,
        _parse_iso_age_seconds(state.started_at) or 0,
        state.status,
        extra={
            "event": "SCAN_STUCK",
            "scan_id": scan_id,
            "user_id": state.user_id,
            "status": state.status,
        },
    )
    fail_scan(scan_id, "Scan timed out — please run a new scan")
    return True


def get_scan_state(scan_id: str, *, user_id: str | None = None) -> ScanState | None:
    expire_stale_scan_state(scan_id)
    state = _load(scan_id)
    if state is None:
        return None
    if user_id and state.user_id != user_id:
        return None
    return state


def _recompute_progress(state: ScanState) -> None:
    total = len(TRACKED_SCAN_PROVIDERS)
    done = len(state.providers_completed) + len(state.providers_failed)
    fetch_pct = int((done / total) * 60) if total else 0
    if state.status == "processing":
        state.progress = max(state.progress, 75)
    elif state.status == "fetching":
        state.progress = max(state.progress, min(fetch_pct, 60))
    elif state.status == "completed":
        state.progress = 100
    elif state.status == "failed":
        state.progress = min(state.progress, 99)


def update_scan_progress(
    scan_id: str,
    *,
    progress: int | None = None,
    status: str | None = None,
    current_provider: str | None = None,
    jobs_found: int | None = None,
) -> ScanState | None:
    state = _load(scan_id)
    if not state:
        return None
    if status:
        state.status = status  # type: ignore[assignment]
    if progress is not None:
        state.progress = max(0, min(100, progress))
    if current_provider is not None:
        state.current_provider = current_provider
    if jobs_found is not None:
        state.jobs_found = jobs_found
    _recompute_progress(state)
    _save(state)
    schedule_scan_realtime(state, "scan_progress")
    return state


def mark_provider_running(scan_id: str, provider: str) -> None:
    state = _load(scan_id)
    if not state:
        return
    slot = state.providers.get(provider) or ScanProviderState(name=provider)
    slot.status = "running"
    state.providers[provider] = slot
    state.status = "fetching"
    state.current_provider = provider
    _recompute_progress(state)
    _save(state)
    schedule_scan_realtime(state, "provider_started")
    logger.info(
        "PROVIDER_STARTED scan_id=%s provider=%s",
        scan_id,
        provider,
        extra={"event": "provider_started", "scan_id": scan_id, "provider": provider},
    )


def update_scan_progress_provider(
    scan_id: str,
    provider: str,
    *,
    status: str,
    jobs_found: int = 0,
    error: str = "",
) -> None:
    """Mark a provider completed or failed and refresh aggregate counters."""
    state = _load(scan_id)
    if not state:
        return

    slot = state.providers.get(provider) or ScanProviderState(name=provider)
    if status == "success":
        slot.status = "completed"
        if provider not in state.providers_completed:
            state.providers_completed.append(provider)
        state.providers_failed = [p for p in state.providers_failed if p != provider]
    else:
        slot.status = "failed"
        slot.error = error or "Provider fetch failed"
        if provider not in state.providers_failed:
            state.providers_failed.append(provider)
        if error:
            state.errors.append(f"{provider}: {error}")
    slot.jobs_found = jobs_found
    state.providers[provider] = slot

    state.jobs_found = sum(p.jobs_found for p in state.providers.values())
    state.status = "fetching"
    state.current_provider = provider
    _recompute_progress(state)
    _save(state)
    schedule_scan_realtime(state, "provider_completed")

    logger.info(
        "PROVIDER_COMPLETED scan_id=%s provider=%s status=%s jobs=%d",
        scan_id,
        provider,
        status,
        jobs_found,
        extra={
            "event": "provider_completed",
            "scan_id": scan_id,
            "provider": provider,
            "status": status,
            "jobs_found": jobs_found,
        },
    )


def complete_scan(
    scan_id: str,
    *,
    jobs_stored: int,
    jobs_found: int,
    result_summary: dict[str, Any] | None = None,
) -> ScanState | None:
    state = _load(scan_id)
    if not state:
        return None
    state.status = "completed"
    state.progress = 100
    state.jobs_stored = jobs_stored
    state.jobs_found = jobs_found
    state.completed_at = _utc_now_iso()
    state.current_provider = ""
    state.result_summary = result_summary
    _save(state)
    schedule_scan_realtime(state, "scan_completed")
    logger.info(
        "SCAN_COMPLETED scan_id=%s stored=%d found=%d",
        scan_id,
        jobs_stored,
        jobs_found,
        extra={
            "event": "scan_completed",
            "scan_id": scan_id,
            "jobs_stored": jobs_stored,
            "jobs_found": jobs_found,
        },
    )
    return state


def fail_scan(scan_id: str, error: str) -> ScanState | None:
    state = _load(scan_id)
    if not state:
        return None
    state.status = "failed"
    state.completed_at = _utc_now_iso()
    state.current_provider = ""
    if error and error not in state.errors:
        state.errors.append(error)
    _recompute_progress(state)
    _save(state)
    schedule_scan_realtime(state, "scan_failed")
    logger.error(
        "SCAN_FAILED scan_id=%s error=%s",
        scan_id,
        error,
        extra={"event": "scan_failed", "scan_id": scan_id, "error": error},
    )
    return state


def delete_scan_state(scan_id: str) -> None:
    delete(_state_key(scan_id))

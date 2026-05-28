"""Bridge Redis scan state mutations to WebSocket scan events."""

from __future__ import annotations

import asyncio
import logging

from app.models.scan_state import ScanState
from app.realtime.scan_event_service import (
    emit_provider_completed,
    emit_provider_started,
    emit_scan_progress_update,
)

logger = logging.getLogger(__name__)


def _serialize_providers(state: ScanState) -> dict[str, dict]:
    return {
        name: slot.model_dump(mode="json")
        for name, slot in (state.providers or {}).items()
    }


async def _emit_for_state(state: ScanState, event: str) -> None:
    payload = {
        "scan_id": state.scan_id,
        "status": state.status,
        "progress": state.progress,
        "current_provider": state.current_provider,
        "providers": _serialize_providers(state),
        "providers_completed": list(state.providers_completed),
        "providers_failed": list(state.providers_failed),
        "jobs_found": state.jobs_found,
        "jobs_stored": state.jobs_stored,
        "errors": list(state.errors),
    }

    if event == "provider_started":
        await emit_provider_started(
            state.user_id,
            scan_id=state.scan_id,
            provider=state.current_provider,
            **payload,
        )
    elif event == "provider_completed":
        await emit_provider_completed(
            state.user_id,
            scan_id=state.scan_id,
            provider=state.current_provider,
            **payload,
        )
    else:
        await emit_scan_progress_update(state.user_id, event=event, **payload)


def schedule_scan_realtime(state: ScanState | None, event: str) -> None:
    """Fire-and-forget WS event when called from sync scan state updates."""
    if state is None or not state.user_id:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    task = loop.create_task(_emit_for_state(state, event))

    def _done(t: asyncio.Task) -> None:
        if t.cancelled():
            return
        exc = t.exception()
        if exc:
            logger.debug("scan realtime emit failed: %s", exc)

    task.add_done_callback(_done)

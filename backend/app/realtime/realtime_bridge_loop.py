"""API-only loop: Mongo realtime_events → in-process WebSocket fan-out."""

from __future__ import annotations

import asyncio
import logging
import signal
from typing import Any

from app.core.config import settings
from app.realtime.websocket_manager import realtime_manager
from app.services.realtime_event_store import claim_unprocessed_events, cleanup_old_events

logger = logging.getLogger(__name__)

_cleanup_counter = 0


class RealtimeBridgeLoop:
    """Poll Mongo for worker-published events and deliver to connected clients."""

    def __init__(self) -> None:
        self._stop = asyncio.Event()

    def request_stop(self) -> None:
        self._stop.set()

    async def run_forever(self) -> None:
        poll_seconds = max(0.5, float(settings.REALTIME_BRIDGE_POLL_SECONDS))
        batch_size = max(1, int(settings.REALTIME_BRIDGE_BATCH_SIZE))

        logger.info(
            "[REALTIME_BRIDGE] started poll=%ss batch=%s",
            poll_seconds,
            batch_size,
            extra={
                "event": "REALTIME_BRIDGE_STARTED",
                "poll_seconds": poll_seconds,
                "batch_size": batch_size,
            },
        )

        global _cleanup_counter
        while not self._stop.is_set():
            try:
                docs = await asyncio.to_thread(
                    claim_unprocessed_events,
                    limit=batch_size,
                )
                for doc in docs:
                    await self._deliver(doc)

                _cleanup_counter += 1
                if _cleanup_counter >= max(1, int(300 / poll_seconds)):
                    _cleanup_counter = 0
                    await asyncio.to_thread(cleanup_old_events)

            except Exception:
                logger.exception(
                    "[REALTIME_BRIDGE] poll cycle failed",
                    extra={"event": "REALTIME_BRIDGE_ERROR"},
                )

            try:
                await asyncio.wait_for(self._stop.wait(), timeout=poll_seconds)
            except asyncio.TimeoutError:
                pass

        logger.info(
            "[REALTIME_BRIDGE] stopped",
            extra={"event": "REALTIME_BRIDGE_STOPPED"},
        )

    async def _deliver(self, doc: dict[str, Any]) -> None:
        user_id = (doc.get("user_id") or "").strip()
        payload = doc.get("payload")
        if not user_id or not isinstance(payload, dict):
            return

        event_type = doc.get("event_type") or payload.get("event") or "realtime"
        if not payload.get("event"):
            payload = {**payload, "event": event_type}

        sent = await realtime_manager.send_to_user(user_id, payload)
        event_id = str(doc.get("_id", ""))
        logger.info(
            "[REALTIME_EVENT] delivered event_id=%s type=%s user_id=%s recipients=%s",
            event_id,
            event_type,
            user_id,
            sent,
            extra={
                "event": "REALTIME_EVENT_DELIVERED",
                "event_id": event_id,
                "event_type": event_type,
                "user_id": user_id,
                "recipients": sent,
            },
        )
        if sent:
            logger.debug(
                "[REALTIME_EVENT] processed event_id=%s",
                event_id,
                extra={"event": "REALTIME_EVENT_PROCESSED", "event_id": event_id},
            )


async def start_realtime_bridge_loop() -> asyncio.Task | None:
    from app.runtime.service_mode import runtime

    if not runtime.should_start_realtime_bridge():
        return None

    loop = RealtimeBridgeLoop()

    def _shutdown(*_: object) -> None:
        loop.request_stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _shutdown)
        except (ValueError, OSError):
            pass

    return asyncio.create_task(loop.run_forever(), name="realtime_mongo_bridge")

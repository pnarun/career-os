"""Automation worker idle loop (Phase 1A — Playwright runtime preparation)."""

from __future__ import annotations

import asyncio
import logging
import os
import signal

from app.core.config import settings

logger = logging.getLogger(__name__)


class AutomationWorkerLoop:
    """
    Minimal automation worker runtime.
    Future phases will dequeue Playwright jobs here; for now keeps process alive
    and logs heartbeat while automation subsystem is initialized.
    """

    def __init__(self) -> None:
        self._stop = asyncio.Event()
        self.worker_id = f"automation-worker-{os.getpid()}"

    def request_stop(self) -> None:
        self._stop.set()

    async def run_forever(self) -> None:
        interval = max(15.0, float(settings.SCAN_WORKER_POLL_SECONDS) * 2)
        logger.info(
            "[AUTOMATION_WORKER] loop started worker_id=%s interval=%ss",
            self.worker_id,
            interval,
            extra={"event": "automation_worker_start", "worker_id": self.worker_id},
        )
        while not self._stop.is_set():
            logger.debug(
                "[AUTOMATION_WORKER] heartbeat worker_id=%s playwright=%s",
                self.worker_id,
                settings.ENABLE_PLAYWRIGHT,
            )
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                pass
        logger.info(
            "[AUTOMATION_WORKER] loop stopped worker_id=%s",
            self.worker_id,
            extra={"event": "automation_worker_stop", "worker_id": self.worker_id},
        )


async def run_automation_worker_loop() -> None:
    worker = AutomationWorkerLoop()
    try:
        signal.signal(signal.SIGINT, lambda *_: worker.request_stop())
        signal.signal(signal.SIGTERM, lambda *_: worker.request_stop())
    except (ValueError, OSError):
        pass
    await worker.run_forever()

"""Scan worker polling loop — Phase 1B production worker runtime."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from typing import Any

from app.core.config import settings
from app.scan_execution.coordinator import coordinator
from app.scan_execution import task_store

logger = logging.getLogger(__name__)


class ScanWorkerLoop:
    """Claims queued scan tasks from MongoDB and executes them with safety controls."""

    def __init__(self, *, worker_id: str | None = None) -> None:
        self.worker_id = worker_id or f"scan-worker-{os.getpid()}"
        self._stop = asyncio.Event()
        self._semaphore = asyncio.Semaphore(max(1, int(settings.SCAN_WORKER_MAX_CONCURRENT)))
        self._active_tasks: set[str] = set()
        self._heartbeat_counter = 0

    def request_stop(self) -> None:
        self._stop.set()

    @property
    def active_count(self) -> int:
        return len(self._active_tasks)

    async def run_forever(self) -> None:
        poll_seconds = max(3.0, float(settings.SCAN_WORKER_POLL_SECONDS))
        heartbeat_every = max(1, int(settings.SCAN_WORKER_HEARTBEAT_SECONDS / poll_seconds))

        logger.info(
            "[SCAN_WORKER] loop started worker_id=%s poll=%ss max_concurrent=%s",
            self.worker_id,
            poll_seconds,
            settings.SCAN_WORKER_MAX_CONCURRENT,
            extra={"event": "scan_worker_start", "worker_id": self.worker_id},
        )

        while not self._stop.is_set():
            await task_store.reclaim_stale_tasks()

            if self._semaphore.locked() and self.active_count >= settings.SCAN_WORKER_MAX_CONCURRENT:
                await self._sleep_or_stop(poll_seconds)
                continue

            task = await task_store.claim_next_queued_task(worker_id=self.worker_id)
            if task is None:
                self._heartbeat_counter += 1
                if self._heartbeat_counter >= heartbeat_every:
                    await self._emit_heartbeat()
                    self._heartbeat_counter = 0
                await self._sleep_or_stop(poll_seconds)
                continue

            asyncio.create_task(self._process_task(task))

        await self._drain_active_tasks()
        logger.info(
            "[SCAN_WORKER] loop stopped worker_id=%s",
            self.worker_id,
            extra={"event": "scan_worker_stop", "worker_id": self.worker_id},
        )

    async def _process_task(self, task) -> None:
        async with self._semaphore:
            self._active_tasks.add(task.task_id)
            try:
                timeout = float(settings.SCAN_TASK_EXECUTION_TIMEOUT_SECONDS)
                await asyncio.wait_for(
                    coordinator.execute_task(task),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                from app.scan_execution.models import ScanTaskStatus, utc_now_iso

                await task_store.update_task(
                    task.task_id,
                    status=ScanTaskStatus.ABANDONED,
                    completed_at=utc_now_iso(),
                    error_summary="worker_execution_timeout",
                )
                logger.error(
                    "[SCAN_WORKER] task timeout task_id=%s timeout_s=%s",
                    task.task_id,
                    settings.SCAN_TASK_EXECUTION_TIMEOUT_SECONDS,
                    extra={"event": "scan_worker_task_timeout", "task_id": task.task_id},
                )
            except Exception:
                logger.exception(
                    "[SCAN_WORKER] task failed task_id=%s",
                    task.task_id,
                    extra={"event": "scan_worker_task_failed", "task_id": task.task_id},
                )
            finally:
                self._active_tasks.discard(task.task_id)

    async def _emit_heartbeat(self) -> None:
        snapshot = await task_store.worker_queue_snapshot()
        logger.info(
            "[SCAN_WORKER] heartbeat worker_id=%s active=%s queue=%s",
            self.worker_id,
            self.active_count,
            snapshot,
            extra={
                "event": "scan_worker_heartbeat",
                "worker_id": self.worker_id,
                "active_tasks": self.active_count,
                "queue": snapshot,
            },
        )

    async def _sleep_or_stop(self, seconds: float) -> None:
        try:
            await asyncio.wait_for(self._stop.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            pass

    async def _drain_active_tasks(self, timeout: float = 30.0) -> None:
        if not self._active_tasks:
            return
        logger.info(
            "[SCAN_WORKER] draining active_tasks=%s",
            len(self._active_tasks),
            extra={"event": "scan_worker_drain", "worker_id": self.worker_id},
        )
        deadline = asyncio.get_running_loop().time() + timeout
        while self._active_tasks and asyncio.get_running_loop().time() < deadline:
            await asyncio.sleep(0.5)


async def run_scan_worker_loop() -> None:
    loop = ScanWorkerLoop()
    install_signal_handlers(loop)
    await loop.run_forever()


def install_signal_handlers(worker: ScanWorkerLoop) -> None:
    try:
        signal.signal(signal.SIGINT, lambda *_: worker.request_stop())
        signal.signal(signal.SIGTERM, lambda *_: worker.request_stop())
    except (ValueError, OSError):
        pass

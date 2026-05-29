"""Scan task dispatch — enqueue only on API in dispatch mode."""

from __future__ import annotations

import asyncio
import logging
import time

from fastapi import BackgroundTasks

from app.runtime.service_mode import runtime
from app.scan_execution.guards import ensure_worker_may_execute_scans
from app.scan_execution.models import ScanExecutionTask, ScanTaskKind, ScanTaskStatus
from app.scan_execution import task_store
from app.scan_execution.coordinator import coordinator
from app.services.job_service import generate_scan_id

logger = logging.getLogger(__name__)


class ScanTaskDispatcher:
    """Creates internal scan tasks and routes them to inline or worker queue."""

    async def create_manual_preferences_task(
        self,
        *,
        preference_id: str,
        user_id: str,
        workspace_id: str = "",
        email: str = "",
    ) -> ScanExecutionTask:
        task = ScanExecutionTask(
            task_id=task_store.new_task_id(),
            kind=ScanTaskKind.MANUAL_PREFERENCES,
            status=ScanTaskStatus.QUEUED,
            user_id=user_id,
            workspace_id=workspace_id,
            email=email,
            preference_id=preference_id,
        )
        return await task_store.insert_task(task)

    async def create_background_discover_task(
        self,
        *,
        scan_id: str,
        user_id: str,
        workspace_id: str = "",
        email: str = "",
        resume_id: str | None = None,
        preference_id: str | None = None,
        send_email: bool = False,
    ) -> ScanExecutionTask:
        task = ScanExecutionTask(
            task_id=task_store.new_task_id(),
            scan_id=scan_id,
            kind=ScanTaskKind.BACKGROUND_DISCOVER,
            status=ScanTaskStatus.QUEUED,
            user_id=user_id,
            workspace_id=workspace_id,
            email=email,
            resume_id=resume_id or "",
            preference_id=preference_id or "",
            send_email=send_email,
        )
        return await task_store.insert_task(task)

    async def create_scheduled_automation_task(
        self,
        *,
        preference_id: str,
    ) -> ScanExecutionTask | None:
        if await task_store.has_active_task_for_preference(
            preference_id,
            kind=ScanTaskKind.SCHEDULED_AUTOMATION,
        ):
            logger.info(
                "[SCAN_DISPATCH] skip duplicate scheduled task preference_id=%s",
                preference_id,
                extra={"event": "scan_task_deduplicated", "preference_id": preference_id},
            )
            return None

        task = ScanExecutionTask(
            task_id=task_store.new_task_id(),
            scan_id=generate_scan_id(),
            kind=ScanTaskKind.SCHEDULED_AUTOMATION,
            status=ScanTaskStatus.QUEUED,
            preference_id=preference_id,
        )
        return await task_store.insert_task(task)

    def should_execute_inline(self) -> bool:
        return runtime.should_execute_scans_inline()

    async def dispatch_inline(
        self,
        task: ScanExecutionTask,
        *,
        background_tasks: BackgroundTasks | None = None,
    ) -> None:
        """Run task in this process — inline monolith only."""
        ensure_worker_may_execute_scans()

        if task.kind == ScanTaskKind.MANUAL_PREFERENCES:
            await coordinator.execute_task(task)
            return

        if background_tasks is not None:
            background_tasks.add_task(_run_task_coro, task)
            return

        asyncio.create_task(_run_task_coro(task))

    async def dispatch_to_worker_queue(self, task: ScanExecutionTask) -> None:
        """Leave task queued for scan_worker process — API returns immediately."""
        t0 = time.perf_counter()
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.info(
            "[SCAN_DISPATCH] enqueued task_id=%s kind=%s user_id=%s scan_id=%s",
            task.task_id,
            task.kind.value,
            task.user_id,
            task.scan_id,
            extra={
                "event": "scan_task_enqueued",
                "task_id": task.task_id,
                "kind": task.kind.value,
                "user_id": task.user_id,
                "scan_id": task.scan_id,
                "dispatch_latency_ms": latency_ms,
            },
        )


async def _run_task_coro(task: ScanExecutionTask) -> None:
    try:
        await coordinator.execute_task(task)
    except Exception:
        logger.exception(
            "[SCAN_DISPATCH] inline background task failed task_id=%s",
            task.task_id,
            extra={"event": "scan_dispatch_failed", "task_id": task.task_id},
        )


dispatcher = ScanTaskDispatcher()

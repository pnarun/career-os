"""Scan execution coordinator — runs tasks on scan_worker or inline monolith only."""

from __future__ import annotations

import gc
import logging

from app.core.runtime_diagnostics import log_memory_event
from app.scan_execution.guards import ensure_worker_may_execute_scans
from app.scan_execution.models import ScanExecutionTask, ScanTaskKind, ScanTaskStatus, utc_now_iso
from app.scan_execution import task_store
from app.services.automation.job_scan_automation_service import run_daily_job_scan_automation
from app.services.background_scan_service import execute_background_scan
from app.services.scan_runner_service import ScanRunnerError, ScanRunResult, run_scan_now
from app.services.user_preferences_service import get_preferences_by_id

logger = logging.getLogger(__name__)


class ScanRuntimeCoordinator:
    """Owns scan lifecycle execution — never invoked from API in dispatch mode."""

    async def execute_task(self, task: ScanExecutionTask) -> ScanRunResult | None:
        ensure_worker_may_execute_scans()

        if task.status == ScanTaskStatus.CLAIMED:
            started = utc_now_iso()
            await task_store.update_task(
                task.task_id,
                status=ScanTaskStatus.RUNNING,
                started_at=started,
                worker_id=task.worker_id or None,
            )
            task.status = ScanTaskStatus.RUNNING
            task.started_at = started
        elif task.status == ScanTaskStatus.QUEUED:
            started = utc_now_iso()
            await task_store.update_task(
                task.task_id,
                status=ScanTaskStatus.RUNNING,
                started_at=started,
                worker_id=task.worker_id or None,
            )
            task.status = ScanTaskStatus.RUNNING
            task.started_at = started
        elif task.status != ScanTaskStatus.RUNNING:
            raise ScanRunnerError(f"Task {task.task_id} not executable (status={task.status.value})")

        logger.info(
            "[SCAN_TASK] started task_id=%s kind=%s scan_id=%s worker_id=%s user_id=%s",
            task.task_id,
            task.kind.value,
            task.scan_id,
            task.worker_id,
            task.user_id,
            extra={
                "event": "scan_task_started",
                "task_id": task.task_id,
                "kind": task.kind.value,
                "scan_id": task.scan_id,
                "worker_id": task.worker_id,
                "user_id": task.user_id,
            },
        )
        log_memory_event(
            "MEMORY_BEFORE_SCAN",
            task_id=task.task_id,
            kind=task.kind.value,
            scan_id=task.scan_id,
            worker_id=task.worker_id,
        )

        try:
            if task.kind == ScanTaskKind.MANUAL_PREFERENCES:
                result = await self._run_manual_preferences(task)
                await task_store.update_task(
                    task.task_id,
                    status=ScanTaskStatus.COMPLETED,
                    scan_id=result.scan_id,
                    completed_at=utc_now_iso(),
                    result_summary={
                        "stored": result.stored,
                        "emailed": result.emailed,
                        "scan_timestamp": result.scan_timestamp,
                        "jobs_found": len(result.top_jobs),
                    },
                )
                logger.info(
                    "[SCAN_TASK] completed task_id=%s scan_id=%s stored=%d",
                    task.task_id,
                    result.scan_id,
                    result.stored,
                    extra={
                        "event": "scan_task_completed",
                        "task_id": task.task_id,
                        "scan_id": result.scan_id,
                        "user_id": task.user_id,
                    },
                )
                return result

            if task.kind == ScanTaskKind.BACKGROUND_DISCOVER:
                await self._run_background_discover(task)
                await task_store.update_task(
                    task.task_id,
                    status=ScanTaskStatus.COMPLETED,
                    scan_id=task.scan_id,
                    completed_at=utc_now_iso(),
                )
                logger.info(
                    "[SCAN_TASK] completed task_id=%s scan_id=%s",
                    task.task_id,
                    task.scan_id,
                    extra={
                        "event": "scan_task_completed",
                        "task_id": task.task_id,
                        "scan_id": task.scan_id,
                        "user_id": task.user_id,
                    },
                )
                return None

            if task.kind == ScanTaskKind.SCHEDULED_AUTOMATION:
                await self._run_scheduled_automation(task)
                await task_store.update_task(
                    task.task_id,
                    status=ScanTaskStatus.COMPLETED,
                    completed_at=utc_now_iso(),
                )
                logger.info(
                    "[SCAN_TASK] completed task_id=%s preference_id=%s",
                    task.task_id,
                    task.preference_id,
                    extra={
                        "event": "scan_task_completed",
                        "task_id": task.task_id,
                        "preference_id": task.preference_id,
                    },
                )
                return None

            raise ScanRunnerError(f"Unknown scan task kind: {task.kind}")

        except Exception as exc:
            summary = str(exc)[:500]
            await task_store.update_task(
                task.task_id,
                status=ScanTaskStatus.FAILED,
                error=summary,
                error_summary=summary,
                completed_at=utc_now_iso(),
            )
            logger.exception(
                "[SCAN_TASK] failed task_id=%s kind=%s",
                task.task_id,
                task.kind.value,
                extra={
                    "event": "scan_task_failed",
                    "task_id": task.task_id,
                    "kind": task.kind.value,
                    "user_id": task.user_id,
                },
            )
            raise
        finally:
            log_memory_event(
                "MEMORY_AFTER_SCAN",
                task_id=task.task_id,
                kind=task.kind.value,
                scan_id=task.scan_id,
                worker_id=task.worker_id,
            )
            self._cleanup_after_scan(task.task_id)

    async def _run_manual_preferences(self, task: ScanExecutionTask) -> ScanRunResult:
        preferences = await get_preferences_by_id(
            task.preference_id,
            user_id=task.user_id or None,
        )
        return await run_scan_now(preferences)

    async def _run_background_discover(self, task: ScanExecutionTask) -> None:
        await execute_background_scan(
            scan_id=task.scan_id,
            user_id=task.user_id,
            workspace_id=task.workspace_id,
            email=task.email,
            resume_id=task.resume_id or None,
            preferences_id=task.preference_id or None,
            send_email=task.send_email,
        )

    async def _run_scheduled_automation(self, task: ScanExecutionTask) -> None:
        await run_daily_job_scan_automation(task.preference_id)

    @staticmethod
    def _cleanup_after_scan(task_id: str) -> None:
        gc.collect()
        logger.debug(
            "[SCAN_EXECUTION] cleanup task_id=%s",
            task_id,
            extra={"event": "scan_execution_cleanup", "task_id": task_id},
        )


coordinator = ScanRuntimeCoordinator()

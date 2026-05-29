"""Scan execution manager — facade for API routes and scheduler."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import BackgroundTasks

from app.models.user_preferences import UserPreferencesDocument
from app.scan_execution.dispatcher import dispatcher
from app.scan_execution.coordinator import coordinator
from app.services.scan_runner_service import ScanRunResult, ScanRunnerError
from app.services.scan_state_service import create_scan_state
from app.services.background_scan_service import new_scan_id

logger = logging.getLogger(__name__)


@dataclass
class ManualScanOutcome:
    """Result of POST /run-scan-now — sync result or queued dispatch."""

    queued: bool = False
    task_id: str = ""
    result: ScanRunResult | None = None


class ScanExecutionManager:
    """
    Single entry point for scan execution requests.
    In dispatch mode the API only enqueues — never runs heavy pipelines.
    """

    async def run_manual_scan_now(
        self,
        preferences: UserPreferencesDocument,
        *,
        user_id: str,
        workspace_id: str = "",
        email: str = "",
    ) -> ManualScanOutcome:
        task = await dispatcher.create_manual_preferences_task(
            preference_id=preferences.id,
            user_id=user_id,
            workspace_id=workspace_id,
            email=email,
        )

        if dispatcher.should_execute_inline():
            result = await coordinator.execute_task(task)
            if result is None:
                raise ScanRunnerError("Manual scan returned no result")
            return ManualScanOutcome(queued=False, task_id=task.task_id, result=result)

        await dispatcher.dispatch_to_worker_queue(task)
        return ManualScanOutcome(queued=True, task_id=task.task_id)

    async def submit_background_scan(
        self,
        *,
        background_tasks: BackgroundTasks | None = None,
        user_id: str,
        workspace_id: str = "",
        email: str = "",
        resume_id: str | None = None,
        preferences_id: str | None = None,
        send_email: bool = False,
    ) -> str:
        """Returns scan_id. Lightweight — no scan pipeline in API process when dispatch mode."""
        scan_id = new_scan_id()
        create_scan_state(scan_id=scan_id, user_id=user_id)

        task = await dispatcher.create_background_discover_task(
            scan_id=scan_id,
            user_id=user_id,
            workspace_id=workspace_id,
            email=email,
            resume_id=resume_id,
            preference_id=preferences_id,
            send_email=send_email,
        )

        if dispatcher.should_execute_inline():
            await dispatcher.dispatch_inline(task, background_tasks=background_tasks)
        else:
            await dispatcher.dispatch_to_worker_queue(task)

        return scan_id

    async def dispatch_scheduled_scan(self, preference_id: str) -> str | None:
        task = await dispatcher.create_scheduled_automation_task(preference_id=preference_id)
        if task is None:
            return None

        if dispatcher.should_execute_inline():
            await coordinator.execute_task(task)
        else:
            await dispatcher.dispatch_to_worker_queue(task)

        return task.task_id

    async def get_task_status(self, task_id: str, *, user_id: str | None = None) -> dict | None:
        from app.scan_execution import task_store

        task = await task_store.get_task(task_id)
        if task is None:
            return None
        if user_id and task.user_id and task.user_id != user_id:
            return None
        return task.to_public_dict()


scan_execution_manager = ScanExecutionManager()

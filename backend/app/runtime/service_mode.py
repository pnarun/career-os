"""Centralized service runtime mode handling."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from app.core.config import settings

ScanExecutionMode = Literal["inline", "dispatch"]


class ServiceMode(str, Enum):
    API = "api"
    SCAN_WORKER = "scan_worker"
    AUTOMATION_WORKER = "automation_worker"

    @classmethod
    def from_env(cls, raw: str | None) -> ServiceMode:
        value = (raw or "api").strip().lower()
        mapping = {
            "api": cls.API,
            "scan_worker": cls.SCAN_WORKER,
            "scan-worker": cls.SCAN_WORKER,
            "automation_worker": cls.AUTOMATION_WORKER,
            "automation-worker": cls.AUTOMATION_WORKER,
        }
        return mapping.get(value, cls.API)


class RuntimeManager:
    """Single place for mode-aware subsystem decisions."""

    @property
    def mode(self) -> ServiceMode:
        return ServiceMode.from_env(settings.SERVICE_MODE)

    def is_api(self) -> bool:
        return self.mode == ServiceMode.API

    def is_scan_worker(self) -> bool:
        return self.mode == ServiceMode.SCAN_WORKER

    def is_automation_worker(self) -> bool:
        return self.mode == ServiceMode.AUTOMATION_WORKER

    def should_start_scheduler(self) -> bool:
        """Scheduler owned by scan_worker in dispatch topology; inline monolith keeps API scheduler."""
        if not settings.ENABLE_SCHEDULER:
            return False
        if self.is_scan_worker():
            return True
        if self.is_api() and self.scan_execution_mode() == "inline":
            return True
        return False

    def scheduler_owner_label(self) -> str:
        if not settings.ENABLE_SCHEDULER:
            return "disabled"
        if self.should_start_scheduler():
            return self.mode.value
        return "none"

    def should_start_realtime(self) -> bool:
        return settings.ENABLE_REALTIME and self.is_api()

    def should_start_automation_shutdown(self) -> bool:
        return settings.ENABLE_AUTOMATION and (
            self.is_api() or self.is_automation_worker()
        )

    def should_run_scan_worker_loop(self) -> bool:
        return self.is_scan_worker()

    def should_run_automation_worker_loop(self) -> bool:
        return self.is_automation_worker()

    def scan_execution_mode(self) -> ScanExecutionMode:
        mode = (settings.SCAN_EXECUTION_MODE or "inline").strip().lower()
        return "dispatch" if mode == "dispatch" else "inline"

    def should_execute_scans_inline(self) -> bool:
        """
        When True, this process runs scan tasks immediately after dispatch.
        API + inline (default) preserves monolith behavior.
        """
        if self.is_scan_worker():
            return False
        return self.scan_execution_mode() == "inline"

    def should_enqueue_scans_for_worker(self) -> bool:
        """When True, API/schedulers only enqueue; scan_worker process executes."""
        if self.is_scan_worker():
            return False
        return self.scan_execution_mode() == "dispatch"

    def should_publish_realtime_to_mongo(self) -> bool:
        """Worker processes publish WS events to Mongo for API bridge delivery."""
        return not self.is_api()

    def should_start_realtime_bridge(self) -> bool:
        """Mongo → WebSocket bridge runs on API only."""
        return (
            settings.ENABLE_REALTIME
            and settings.REALTIME_BRIDGE_ENABLED
            and self.is_api()
        )

    def profile_summary(self) -> dict[str, object]:
        return {
            "service_mode": self.mode.value,
            "scan_execution_mode": self.scan_execution_mode(),
            "scheduler": self.should_start_scheduler(),
            "realtime": self.should_start_realtime(),
            "realtime_bridge": self.should_start_realtime_bridge(),
            "scan_worker_loop": self.should_run_scan_worker_loop(),
            "automation_worker_loop": self.should_run_automation_worker_loop(),
            "execute_scans_inline": self.should_execute_scans_inline(),
            "scheduler_owner": self.scheduler_owner_label(),
        }


runtime = RuntimeManager()

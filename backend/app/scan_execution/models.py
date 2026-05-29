"""Internal scan task model — Mongo-backed dispatch queue (Phase 1B)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ScanTaskKind(str, Enum):
    MANUAL_PREFERENCES = "manual_preferences"
    BACKGROUND_DISCOVER = "background_discover"
    SCHEDULED_AUTOMATION = "scheduled_automation"


class ScanTaskStatus(str, Enum):
    QUEUED = "queued"
    CLAIMED = "claimed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"

    @classmethod
    def active_statuses(cls) -> frozenset[ScanTaskStatus]:
        return frozenset({cls.QUEUED, cls.CLAIMED, cls.RUNNING})


class ScanExecutionTask(BaseModel):
    task_id: str
    scan_id: str = ""
    kind: ScanTaskKind
    status: ScanTaskStatus = ScanTaskStatus.QUEUED
    user_id: str = ""
    workspace_id: str = ""
    email: str = ""
    preference_id: str = ""
    resume_id: str = ""
    send_email: bool = False
    error: str = ""
    error_summary: str = ""
    result_summary: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)
    claimed_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    worker_id: str = ""
    dispatch_latency_ms: float | None = None

    def to_mongo(self) -> dict[str, Any]:
        data = self.model_dump(mode="json")
        data["kind"] = self.kind.value
        data["status"] = self.status.value
        return data

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]) -> ScanExecutionTask:
        payload = dict(doc)
        payload.pop("_id", None)
        if "kind" in payload and not isinstance(payload["kind"], ScanTaskKind):
            payload["kind"] = ScanTaskKind(payload["kind"])
        if "status" in payload and not isinstance(payload["status"], ScanTaskStatus):
            payload["status"] = ScanTaskStatus(payload["status"])
        if "created_at" in payload:
            from app.core.mongo_timestamps import coerce_to_iso

            payload["created_at"] = coerce_to_iso(payload["created_at"])
        if "started_at" in payload and payload["started_at"]:
            from app.core.mongo_timestamps import coerce_to_iso

            payload["started_at"] = coerce_to_iso(payload["started_at"])
        if "completed_at" in payload and payload["completed_at"]:
            from app.core.mongo_timestamps import coerce_to_iso

            payload["completed_at"] = coerce_to_iso(payload["completed_at"])
        if "claimed_at" in payload and payload["claimed_at"]:
            from app.core.mongo_timestamps import coerce_to_iso

            payload["claimed_at"] = coerce_to_iso(payload["claimed_at"])
        return cls.model_validate(payload)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "scan_id": self.scan_id,
            "kind": self.kind.value,
            "status": self.status.value,
            "user_id": self.user_id,
            "preference_id": self.preference_id,
            "worker_id": self.worker_id,
            "error_summary": self.error_summary or self.error,
            "result_summary": self.result_summary,
            "created_at": self.created_at,
            "claimed_at": self.claimed_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "dispatch_latency_ms": self.dispatch_latency_ms,
        }

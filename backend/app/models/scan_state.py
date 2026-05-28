"""Redis-backed scan execution state for background scans."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ScanLifecycleStatus = Literal[
    "started",
    "fetching",
    "processing",
    "completed",
    "failed",
]

ProviderStatus = Literal["pending", "running", "completed", "failed"]

TRACKED_SCAN_PROVIDERS: tuple[str, ...] = (
    "remoteok",
    "arbeitnow",
    "indeed",
    "naukri",
    "instahyre",
    "linkedin",
)


class ScanProviderState(BaseModel):
    name: str
    status: ProviderStatus = "pending"
    jobs_found: int = 0
    error: str = ""


class ScanState(BaseModel):
    scan_id: str
    user_id: str
    status: ScanLifecycleStatus = "started"
    progress: int = 0
    current_provider: str = ""
    providers: dict[str, ScanProviderState] = Field(default_factory=dict)
    providers_completed: list[str] = Field(default_factory=list)
    providers_failed: list[str] = Field(default_factory=list)
    jobs_found: int = 0
    jobs_stored: int = 0
    errors: list[str] = Field(default_factory=list)
    started_at: str
    completed_at: str | None = None
    result_summary: dict[str, Any] | None = None


class ScanStartRequest(BaseModel):
    resume_id: str | None = None
    preferences_id: str | None = None
    send_email: bool = False


class ScanStartResponse(BaseModel):
    scan_id: str
    status: str = "started"


class ScanStatusResponse(BaseModel):
    scan_id: str
    status: ScanLifecycleStatus
    progress: int
    current_provider: str = ""
    providers: dict[str, ScanProviderState] = Field(default_factory=dict)
    providers_completed: list[str] = Field(default_factory=list)
    providers_failed: list[str] = Field(default_factory=list)
    jobs_found: int = 0
    jobs_stored: int = 0
    errors: list[str] = Field(default_factory=list)
    started_at: str
    completed_at: str | None = None
    result_summary: dict[str, Any] | None = None

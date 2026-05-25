from typing import Any, Literal

from pydantic import BaseModel, Field

AutomationRunType = Literal[
    "daily_scan",
    "high_match_alert",
    "follow_up_reminder",
    "interview_reminder",
    "daily_digest",
    "weekly_insights",
]

AutomationRunStatus = Literal["running", "completed", "failed", "partial"]


class AutomationRunDocument(BaseModel):
    id: str
    run_type: AutomationRunType
    status: AutomationRunStatus
    preference_id: str = ""
    scan_id: str = ""
    jobs_analyzed: int = 0
    high_matches_found: int = 0
    notifications_sent: int = 0
    providers_succeeded: list[str] = Field(default_factory=list)
    providers_failed: list[str] = Field(default_factory=list)
    error: str = ""
    started_at: str
    completed_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "AutomationRunDocument":
        return cls(
            id=str(document["_id"]),
            run_type=document["run_type"],
            status=document["status"],
            preference_id=document.get("preference_id", ""),
            scan_id=document.get("scan_id", ""),
            jobs_analyzed=document.get("jobs_analyzed", 0),
            high_matches_found=document.get("high_matches_found", 0),
            notifications_sent=document.get("notifications_sent", 0),
            providers_succeeded=document.get("providers_succeeded") or [],
            providers_failed=document.get("providers_failed") or [],
            error=document.get("error", ""),
            started_at=document["started_at"],
            completed_at=document.get("completed_at", ""),
            metadata=document.get("metadata") or {},
        )


class AutomationAnalytics(BaseModel):
    scans_completed: int = 0
    jobs_analyzed: int = 0
    notifications_sent: int = 0
    high_matches_found: int = 0
    provider_performance: dict[str, int] = Field(default_factory=dict)
    recent_runs: list[AutomationRunDocument] = Field(default_factory=list)

from typing import Any

from pydantic import BaseModel, Field


class JobQualityFields(BaseModel):
    """Apply validation and usefulness scoring for automation readiness."""

    has_apply_url: bool = False
    is_easy_apply_possible: bool = False
    job_quality_score: int = 0
    is_suspicious: bool = False
    quality_flags: list[str] = Field(default_factory=list)


class JobCreate(BaseModel):
    """Payload for persisting a job with match intelligence."""

    title: str
    company: str
    location: str = ""
    apply_url: str
    source: str
    description: str = ""
    easy_apply: bool = False
    job_type: str = ""
    remote_priority: bool = False
    india_focused: bool = False
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    match_percentage: int = 0
    recommendation: str = ""
    scan_id: str = ""
    scan_timestamp: str = ""
    is_latest_scan: bool = False
    already_seen: bool = False
    has_apply_url: bool = False
    is_easy_apply_possible: bool = False
    job_quality_score: int = 0
    is_suspicious: bool = False
    quality_flags: list[str] = Field(default_factory=list)


class JobDocument(BaseModel):
    """Job document as stored in MongoDB."""

    id: str
    title: str
    company: str
    location: str
    apply_url: str
    source: str
    description: str
    easy_apply: bool
    job_type: str
    remote_priority: bool
    india_focused: bool
    matched_skills: list[str]
    missing_skills: list[str]
    match_percentage: int
    recommendation: str
    created_at: str
    scan_id: str = ""
    scan_timestamp: str = ""
    is_latest_scan: bool = False
    already_seen: bool = False
    has_apply_url: bool = False
    is_easy_apply_possible: bool = False
    job_quality_score: int = 0
    is_suspicious: bool = False
    quality_flags: list[str] = Field(default_factory=list)

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "JobDocument":
        apply_url = document.get("apply_url", "")
        has_apply_url = document.get(
            "has_apply_url",
            bool(apply_url and apply_url.startswith("http")),
        )
        return cls(
            id=str(document["_id"]),
            title=document["title"],
            company=document["company"],
            location=document.get("location", ""),
            apply_url=apply_url,
            source=document["source"],
            description=document.get("description", ""),
            easy_apply=document.get("easy_apply", False),
            job_type=document.get("job_type", ""),
            remote_priority=document.get("remote_priority", False),
            india_focused=document.get("india_focused", False),
            matched_skills=document.get("matched_skills", []),
            missing_skills=document.get("missing_skills", []),
            match_percentage=document.get("match_percentage", 0),
            recommendation=document.get("recommendation", ""),
            created_at=document["created_at"],
            scan_id=document.get("scan_id", ""),
            scan_timestamp=document.get("scan_timestamp", ""),
            is_latest_scan=document.get("is_latest_scan", False),
            already_seen=document.get("already_seen", False),
            has_apply_url=has_apply_url,
            is_easy_apply_possible=document.get("is_easy_apply_possible", False),
            job_quality_score=document.get("job_quality_score", 0),
            is_suspicious=document.get("is_suspicious", False),
            quality_flags=document.get("quality_flags", []),
        )


class JobHistoryItem(BaseModel):
    """Slim job payload for historical debug feed."""

    id: str
    title: str
    company: str
    location: str
    source: str
    match_percentage: int
    scan_id: str = ""
    created_at: str
    remote_priority: bool = False
    india_focused: bool = False
    has_apply_url: bool = False
    is_easy_apply_possible: bool = False
    job_quality_score: int = 0
    is_suspicious: bool = False
    quality_flags: list[str] = Field(default_factory=list)
    apply_url: str = ""

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "JobHistoryItem":
        apply_url = document.get("apply_url", "")
        has_apply_url = document.get(
            "has_apply_url",
            bool(apply_url and apply_url.startswith("http")),
        )
        return cls(
            id=str(document["_id"]),
            title=document["title"],
            company=document["company"],
            location=document.get("location", ""),
            source=document["source"],
            match_percentage=document.get("match_percentage", 0),
            scan_id=document.get("scan_id", ""),
            created_at=document["created_at"],
            remote_priority=document.get("remote_priority", False),
            india_focused=document.get("india_focused", False),
            has_apply_url=has_apply_url,
            is_easy_apply_possible=document.get("is_easy_apply_possible", False),
            job_quality_score=document.get("job_quality_score", 0),
            is_suspicious=document.get("is_suspicious", False),
            quality_flags=document.get("quality_flags", []),
            apply_url=apply_url,
        )


class ScanFetchResponse(BaseModel):
    """Summary returned after a job discovery scan completes."""

    scan_id: str
    scan_timestamp: str
    fetched: int
    filtered: int
    accepted: int
    stored: int
    skipped_already_shown: int
    top_jobs_returned: int
    quality_rejected: int = 0
    resume_id: str = ""

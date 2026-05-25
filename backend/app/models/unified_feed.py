from typing import Any

from pydantic import BaseModel, Field


class UnifiedFeedJob(BaseModel):
    """Common normalized job schema for the unified feed."""

    job_id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    description: str = ""
    apply_url: str = ""
    source: str = ""
    source_priority: int = 0
    easy_apply: bool = False
    remote: bool = False
    salary: str = ""
    posted_at: str = ""
    match_score: int = 0
    job_quality_score: int = 0
    skills: list[str] = Field(default_factory=list)
    experience_level: str = ""
    recommendation: str = ""
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    experience_alignment: str = ""
    career_fit: str = ""
    why_match: list[str] = Field(default_factory=list)
    match_breakdown: dict[str, float] = Field(default_factory=dict)
    scan_id: str = ""
    scan_timestamp: str = ""
    has_apply_url: bool = False
    is_suspicious: bool = False
    quality_flags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UnifiedFeedResponse(BaseModel):
    total_jobs: int = 0
    duplicates_removed: int = 0
    providers: dict[str, int] = Field(default_factory=dict)
    jobs: list[UnifiedFeedJob] = Field(default_factory=list)
    scan_id: str = ""
    scan_timestamp: str = ""

from typing import Any

from pydantic import BaseModel, Field

from app.services.job_sources.base.provider_diagnostics import ProviderFetchDiagnostic


class RawSourceJob(BaseModel):
    """Provider-specific job payload before normalization."""

    source: str
    source_job_id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    remote: bool = False
    apply_url: str = ""
    description: str = ""
    posted_at: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class NormalizedSourceJob(BaseModel):
    """Unified job schema across all providers."""

    source: str
    source_job_id: str = ""
    title: str
    company: str
    location: str = ""
    remote: bool = False
    apply_url: str = ""
    description: str = ""
    posted_at: str = ""
    fetch_timestamp: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    easy_apply: bool = False
    job_type: str = ""
    tags: list[str] = Field(default_factory=list)

    def to_pipeline_dict(self) -> dict[str, Any]:
        """Convert to legacy pipeline dict used by filter/match/store."""
        job_type = self.job_type or ("remote" if self.remote else "")
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "apply_url": self.apply_url,
            "source": self.source,
            "description": self.description,
            "easy_apply": self.easy_apply,
            "job_type": job_type,
            "tags": self.tags,
            "remote_priority": False,
            "india_focused": False,
            "source_job_id": self.source_job_id,
            "fetch_timestamp": self.fetch_timestamp,
            "posted_at": self.posted_at,
            "metadata": self.metadata,
        }


class SourceFetchResult(BaseModel):
    """Per-source fetch outcome."""

    source: str
    jobs: list[NormalizedSourceJob] = Field(default_factory=list)
    fetched_count: int = 0
    error: str | None = None
    duration_ms: int = 0
    diagnostic: ProviderFetchDiagnostic | None = None


class AggregatorFetchResult(BaseModel):
    """Combined multi-source aggregation summary."""

    jobs: list[dict[str, Any]] = Field(default_factory=list)
    total_fetched: int = 0
    total_after_dedupe: int = 0
    sources: dict[str, int] = Field(default_factory=dict)
    failed_sources: list[str] = Field(default_factory=list)
    source_errors: dict[str, str] = Field(default_factory=dict)
    provider_diagnostics: list[ProviderFetchDiagnostic] = Field(default_factory=list)

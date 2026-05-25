from typing import Any

from pydantic import BaseModel, Field


class ScanSummaryDetail(BaseModel):
    """Rich analytics payload for scan transparency (API + email + UI)."""

    total_fetched: int = 0
    qualified_jobs: int = 0
    rejected_jobs: int = 0
    duplicates_removed: int = 0
    sources: dict[str, int] = Field(default_factory=dict)
    failed_sources: list[str] = Field(default_factory=list)
    top_source: str = ""
    top_source_count: int = 0
    locations: dict[str, int] = Field(default_factory=dict)
    platforms_scanned: int = 0
    provider_status: list[dict[str, Any]] = Field(default_factory=list)
    source_errors: dict[str, str] = Field(default_factory=dict)


class ScanSessionDocument(BaseModel):
    """Persisted scan session analytics in MongoDB."""

    id: str = ""
    scan_id: str
    scan_timestamp: str
    total_fetched: int = 0
    qualified_jobs: int = 0
    rejected_jobs: int = 0
    duplicates_removed: int = 0
    source_breakdown: dict[str, int] = Field(default_factory=dict)
    failed_sources: list[str] = Field(default_factory=list)
    location_breakdown: dict[str, int] = Field(default_factory=dict)
    top_source: str = ""
    top_source_count: int = 0
    resume_id: str = ""
    provider_status: list[dict[str, Any]] = Field(default_factory=list)
    source_errors: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "ScanSessionDocument":
        return cls(
            id=str(document["_id"]),
            scan_id=document["scan_id"],
            scan_timestamp=document["scan_timestamp"],
            total_fetched=document.get("total_fetched", 0),
            qualified_jobs=document.get("qualified_jobs", 0),
            rejected_jobs=document.get("rejected_jobs", 0),
            duplicates_removed=document.get("duplicates_removed", 0),
            source_breakdown=document.get("source_breakdown", {}),
            failed_sources=document.get("failed_sources", []),
            location_breakdown=document.get("location_breakdown", {}),
            top_source=document.get("top_source", ""),
            top_source_count=document.get("top_source_count", 0),
            resume_id=document.get("resume_id", ""),
            provider_status=document.get("provider_status", []),
            source_errors=document.get("source_errors", {}),
        )

    def to_summary_detail(self) -> ScanSummaryDetail:
        platforms = len([c for c in self.source_breakdown.values() if c > 0])
        platforms += len(self.failed_sources)
        return ScanSummaryDetail(
            total_fetched=self.total_fetched,
            qualified_jobs=self.qualified_jobs,
            rejected_jobs=self.rejected_jobs,
            duplicates_removed=self.duplicates_removed,
            sources=self.source_breakdown,
            failed_sources=self.failed_sources,
            top_source=self.top_source,
            top_source_count=self.top_source_count,
            locations=self.location_breakdown,
            platforms_scanned=platforms,
            provider_status=list(self.provider_status),
            source_errors=dict(self.source_errors),
        )

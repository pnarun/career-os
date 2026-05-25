from typing import Any, Literal

from pydantic import BaseModel, Field

ApplicationStatus = Literal[
    "saved",
    "applied",
    "interview",
    "assessment",
    "rejected",
    "offer",
    "ghosted",
    "withdrawn",
]

APPLICATION_STATUSES: tuple[str, ...] = (
    "saved",
    "applied",
    "interview",
    "assessment",
    "rejected",
    "offer",
    "ghosted",
    "withdrawn",
)


class StatusHistoryEntry(BaseModel):
    status: str
    timestamp: str


class ApplicationCreatePayload(BaseModel):
    job_id: str = ""
    title: str
    company: str
    source: str = ""
    apply_url: str = ""
    match_score: int = 0
    resume_id: str = ""
    remote: bool = False
    easy_apply: bool = False
    location: str = ""
    matched_skills: list[str] = Field(default_factory=list)
    notes: str = ""


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationNotesUpdate(BaseModel):
    notes: str = ""


class ApplicationDocument(BaseModel):
    application_id: str
    job_id: str = ""
    title: str
    company: str
    source: str = ""
    apply_url: str = ""
    status: str = "saved"
    notes: str = ""
    applied_at: str = ""
    updated_at: str = ""
    created_at: str = ""
    match_score: int = 0
    resume_id: str = ""
    remote: bool = False
    easy_apply: bool = False
    location: str = ""
    matched_skills: list[str] = Field(default_factory=list)
    status_history: list[StatusHistoryEntry] = Field(default_factory=list)

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "ApplicationDocument":
        history = document.get("status_history") or []
        return cls(
            application_id=str(document["_id"]),
            job_id=document.get("job_id", ""),
            title=document.get("title", ""),
            company=document.get("company", ""),
            source=document.get("source", ""),
            apply_url=document.get("apply_url", ""),
            status=document.get("status", "saved"),
            notes=document.get("notes", ""),
            applied_at=document.get("applied_at", ""),
            updated_at=document.get("updated_at", ""),
            created_at=document.get("created_at", ""),
            match_score=int(document.get("match_score") or 0),
            resume_id=document.get("resume_id", ""),
            remote=bool(document.get("remote")),
            easy_apply=bool(document.get("easy_apply")),
            location=document.get("location", ""),
            matched_skills=list(document.get("matched_skills") or []),
            status_history=[
                StatusHistoryEntry(
                    status=str(entry.get("status", "")),
                    timestamp=str(entry.get("timestamp", "")),
                )
                for entry in history
            ],
        )


class ApplicationAnalytics(BaseModel):
    total_saved: int = 0
    total_applied: int = 0
    interviews: int = 0
    offers: int = 0
    rejections: int = 0
    response_rate: float = 0.0
    top_sources: list[dict[str, Any]] = Field(default_factory=list)
    top_skills: list[dict[str, Any]] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    application_id: str
    title: str
    company: str
    status: str
    timestamp: str


class ApplicationTimelineResponse(BaseModel):
    events: list[TimelineEvent] = Field(default_factory=list)

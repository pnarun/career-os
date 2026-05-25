from typing import Any, Literal

from pydantic import BaseModel, Field

ApplyState = Literal[
    "IDLE",
    "OPENING_JOB",
    "DETECTING_FORM",
    "UPLOADING_RESUME",
    "FILLING_FIELDS",
    "DETECTING_QUESTIONS",
    "WAITING_CONFIRMATION",
    "SUBMITTING",
    "SUCCESS",
    "FAILED",
    "CAPTCHA_BLOCKED",
    "CANCELLED",
]

ApplyProvider = Literal["linkedin", "naukri"]


class FilledField(BaseModel):
    label: str
    value: str
    confidence: float = 1.0
    source: str = "resume"


class DetectedQuestion(BaseModel):
    label: str
    question_type: str
    suggested_answer: str = ""
    confidence: float = 0.0
    requires_confirmation: bool = True
    answered: bool = False


class ApplySessionCreate(BaseModel):
    job_id: str = ""
    job_url: str
    title: str = ""
    company: str = ""
    source: str = "linkedin"
    resume_id: str = ""
    match_score: int = 0


class ApplySessionDocument(BaseModel):
    id: str
    session_id: str
    state: ApplyState
    job_id: str = ""
    job_url: str
    title: str = ""
    company: str = ""
    source: str = "linkedin"
    resume_id: str = ""
    match_score: int = 0
    filled_fields: list[FilledField] = Field(default_factory=list)
    detected_questions: list[DetectedQuestion] = Field(default_factory=list)
    unknown_questions: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    screenshots: list[str] = Field(default_factory=list)
    error: str = ""
    confirmation_required: bool = False
    confirmed: bool = False
    submitted: bool = False
    application_id: str = ""
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "ApplySessionDocument":
        return cls(
            id=str(document["_id"]),
            session_id=document.get("session_id", str(document["_id"])),
            state=document.get("state", "IDLE"),
            job_id=document.get("job_id", ""),
            job_url=document.get("job_url", ""),
            title=document.get("title", ""),
            company=document.get("company", ""),
            source=document.get("source", "linkedin"),
            resume_id=document.get("resume_id", ""),
            match_score=int(document.get("match_score", 0)),
            filled_fields=[FilledField(**f) for f in (document.get("filled_fields") or [])],
            detected_questions=[
                DetectedQuestion(**q) for q in (document.get("detected_questions") or [])
            ],
            unknown_questions=document.get("unknown_questions") or [],
            confidence_score=float(document.get("confidence_score", 0)),
            screenshots=document.get("screenshots") or [],
            error=document.get("error", ""),
            confirmation_required=document.get("confirmation_required", False),
            confirmed=document.get("confirmed", False),
            submitted=document.get("submitted", False),
            application_id=document.get("application_id", ""),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            metadata=document.get("metadata") or {},
        )


class ApplyConfirmRequest(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)


class ApplyAnalytics(BaseModel):
    attempts_today: int = 0
    max_per_day: int = 10
    cooldown_seconds: int = 60
    can_apply: bool = True
    last_apply_at: str = ""

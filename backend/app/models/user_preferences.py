from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field

DEFAULT_ENABLED_PROVIDERS = [
    "linkedin",
    "indeed",
    "naukri",
    "instahyre",
    "remoteok",
    "arbeitnow",
]

CareerFocus = Literal["backend", "fullstack", "devops", "ai_ml", "cloud", "general"]
AiStrictness = Literal["balanced", "strict", "relaxed"]
AtsOptimizationMode = Literal["standard", "aggressive", "conservative"]


class UserPreferencesCreate(BaseModel):
    """Payload for creating scan delivery preferences."""

    email: EmailStr
    resume_id: str
    scan_time: str = "08:00"
    timezone: str = "Asia/Kolkata"
    frequency: str = "every_6h"
    is_active: bool = True
    email_notifications: bool = True
    in_app_notifications: bool = True
    min_match_threshold: int = Field(default=50, ge=0, le=100)
    remote_only: bool = False
    preferred_locations: list[str] = Field(default_factory=list)
    digest_frequency: str = "daily"
    high_match_alerts: bool = True
    follow_up_reminders: bool = True
    notice_period_days: int = Field(default=30, ge=0, le=365)
    willing_to_relocate: bool = True
    work_authorization: str = "Authorized to work"
    expected_salary: str = ""
    enabled_providers: list[str] = Field(default_factory=lambda: list(DEFAULT_ENABLED_PROVIDERS))
    provider_priority: list[str] = Field(default_factory=lambda: list(DEFAULT_ENABLED_PROVIDERS))
    career_focus: CareerFocus = "general"
    ai_strictness: AiStrictness = "balanced"
    ats_optimization_mode: AtsOptimizationMode = "standard"
    interview_reminders: bool = True
    scan_completion_alerts: bool = True
    auto_email_on_scan: bool = True
    target_roles: list[str] = Field(default_factory=list)
    target_skills: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
    years_experience: int = Field(default=0, ge=0, le=50)
    use_default_six_hour_schedule: bool = True


class UserPreferencesUpdate(BaseModel):
    """Partial update for scan delivery preferences."""

    email: EmailStr | None = None
    resume_id: str | None = None
    scan_time: str | None = None
    timezone: str | None = None
    frequency: str | None = None
    is_active: bool | None = None
    email_notifications: bool | None = None
    in_app_notifications: bool | None = None
    min_match_threshold: int | None = Field(default=None, ge=0, le=100)
    remote_only: bool | None = None
    preferred_locations: list[str] | None = None
    digest_frequency: str | None = None
    high_match_alerts: bool | None = None
    follow_up_reminders: bool | None = None
    notice_period_days: int | None = Field(default=None, ge=0, le=365)
    willing_to_relocate: bool | None = None
    work_authorization: str | None = None
    expected_salary: str | None = None
    enabled_providers: list[str] | None = None
    provider_priority: list[str] | None = None
    career_focus: CareerFocus | None = None
    ai_strictness: AiStrictness | None = None
    ats_optimization_mode: AtsOptimizationMode | None = None
    interview_reminders: bool | None = None
    scan_completion_alerts: bool | None = None
    auto_email_on_scan: bool | None = None
    target_roles: list[str] | None = None
    target_skills: list[str] | None = None
    target_companies: list[str] | None = None
    years_experience: int | None = Field(default=None, ge=0, le=50)
    use_default_six_hour_schedule: bool | None = None


class UserPreferencesDocument(BaseModel):
    """User preferences stored in MongoDB."""

    id: str
    user_id: str = ""
    workspace_id: str = ""
    email: str
    resume_id: str
    scan_time: str
    timezone: str
    frequency: str
    is_active: bool
    created_at: str
    updated_at: str
    last_email_scan_id: str = ""
    last_email_sent_at: str = ""
    email_notifications: bool = True
    in_app_notifications: bool = True
    min_match_threshold: int = 50
    remote_only: bool = False
    preferred_locations: list[str] = Field(default_factory=list)
    digest_frequency: str = "daily"
    high_match_alerts: bool = True
    follow_up_reminders: bool = True
    notice_period_days: int = Field(default=30, ge=0, le=365)
    willing_to_relocate: bool = True
    work_authorization: str = "Authorized to work"
    expected_salary: str = ""
    enabled_providers: list[str] = Field(default_factory=lambda: list(DEFAULT_ENABLED_PROVIDERS))
    provider_priority: list[str] = Field(default_factory=lambda: list(DEFAULT_ENABLED_PROVIDERS))
    career_focus: CareerFocus = "general"
    ai_strictness: AiStrictness = "balanced"
    ats_optimization_mode: AtsOptimizationMode = "standard"
    interview_reminders: bool = True
    scan_completion_alerts: bool = True
    auto_email_on_scan: bool = True
    target_roles: list[str] = Field(default_factory=list)
    target_skills: list[str] = Field(default_factory=list)
    target_companies: list[str] = Field(default_factory=list)
    years_experience: int = Field(default=0, ge=0, le=50)
    use_default_six_hour_schedule: bool = True

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "UserPreferencesDocument":
        enabled = document.get("enabled_providers") or list(DEFAULT_ENABLED_PROVIDERS)
        priority = document.get("provider_priority") or enabled
        return cls(
            id=str(document["_id"]),
            user_id=document.get("user_id", ""),
            workspace_id=document.get("workspace_id", ""),
            email=document["email"],
            resume_id=document["resume_id"],
            scan_time=document.get("scan_time", "08:00"),
            timezone=document.get("timezone", "Asia/Kolkata"),
            frequency=document.get("frequency", "every_6h"),
            is_active=document.get("is_active", True),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            last_email_scan_id=document.get("last_email_scan_id", ""),
            last_email_sent_at=document.get("last_email_sent_at", ""),
            email_notifications=document.get("email_notifications", True),
            in_app_notifications=document.get("in_app_notifications", True),
            min_match_threshold=int(document.get("min_match_threshold", 50)),
            remote_only=document.get("remote_only", False),
            preferred_locations=document.get("preferred_locations") or [],
            digest_frequency=document.get("digest_frequency", "daily"),
            high_match_alerts=document.get("high_match_alerts", True),
            follow_up_reminders=document.get("follow_up_reminders", True),
            notice_period_days=int(document.get("notice_period_days", 30)),
            willing_to_relocate=document.get("willing_to_relocate", True),
            work_authorization=document.get("work_authorization", "Authorized to work"),
            expected_salary=document.get("expected_salary", ""),
            enabled_providers=list(enabled),
            provider_priority=list(priority),
            career_focus=document.get("career_focus", "general"),
            ai_strictness=document.get("ai_strictness", "balanced"),
            ats_optimization_mode=document.get("ats_optimization_mode", "standard"),
            interview_reminders=document.get("interview_reminders", True),
            scan_completion_alerts=document.get("scan_completion_alerts", True),
            auto_email_on_scan=document.get("auto_email_on_scan", True),
            target_roles=list(document.get("target_roles") or []),
            target_skills=list(document.get("target_skills") or []),
            target_companies=list(document.get("target_companies") or []),
            years_experience=int(document.get("years_experience") or 0),
            use_default_six_hour_schedule=document.get("use_default_six_hour_schedule", True),
        )

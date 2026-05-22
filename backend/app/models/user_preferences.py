from typing import Any

from pydantic import BaseModel, EmailStr, Field


class UserPreferencesCreate(BaseModel):
    """Payload for creating scan delivery preferences."""

    email: EmailStr
    resume_id: str
    scan_time: str = "08:00"
    timezone: str = "Asia/Kolkata"
    frequency: str = "daily"
    is_active: bool = True


class UserPreferencesUpdate(BaseModel):
    """Partial update for scan delivery preferences."""

    email: EmailStr | None = None
    resume_id: str | None = None
    scan_time: str | None = None
    timezone: str | None = None
    frequency: str | None = None
    is_active: bool | None = None


class UserPreferencesDocument(BaseModel):
    """User preferences stored in MongoDB."""

    id: str
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

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "UserPreferencesDocument":
        return cls(
            id=str(document["_id"]),
            email=document["email"],
            resume_id=document["resume_id"],
            scan_time=document.get("scan_time", "08:00"),
            timezone=document.get("timezone", "Asia/Kolkata"),
            frequency=document.get("frequency", "daily"),
            is_active=document.get("is_active", True),
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            last_email_scan_id=document.get("last_email_scan_id", ""),
            last_email_sent_at=document.get("last_email_sent_at", ""),
        )

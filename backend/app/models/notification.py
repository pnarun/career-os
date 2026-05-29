from typing import Any, Literal

from pydantic import BaseModel, Field

from app.core.mongo_timestamps import coerce_to_iso

NotificationType = Literal[
    "high_match",
    "daily_digest",
    "follow_up",
    "interview_reminder",
    "weekly_insights",
    "scan_complete",
    "remote_jobs",
]

NotificationChannel = Literal["in_app", "email"]
NotificationPriority = Literal["normal", "high"]


class NotificationCreate(BaseModel):
    type: NotificationType
    title: str
    message: str
    channel: NotificationChannel = "in_app"
    priority: NotificationPriority = "normal"
    metadata: dict[str, Any] = Field(default_factory=dict)
    preference_id: str = ""


class NotificationDocument(BaseModel):
    id: str
    type: NotificationType
    title: str
    message: str
    channel: NotificationChannel
    priority: NotificationPriority
    read: bool
    metadata: dict[str, Any] = Field(default_factory=dict)
    preference_id: str = ""
    created_at: str

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "NotificationDocument":
        return cls(
            id=str(document["_id"]),
            type=document["type"],
            title=document["title"],
            message=document["message"],
            channel=document.get("channel", "in_app"),
            priority=document.get("priority", "normal"),
            read=document.get("read", False),
            metadata=document.get("metadata") or {},
            preference_id=document.get("preference_id", ""),
            created_at=coerce_to_iso(document.get("created_at")),
        )


class NotificationListResponse(BaseModel):
    notifications: list[NotificationDocument]
    unread_count: int
    total: int

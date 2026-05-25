from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field

UserRole = Literal["user", "admin"]


class UserDocument(BaseModel):
    id: str
    email: str
    full_name: str
    timezone: str = "Asia/Kolkata"
    created_at: str
    last_login: str = ""
    is_active: bool = True
    role: UserRole = "user"
    workspace_id: str = ""
    preferences: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "UserDocument":
        return cls(
            id=str(document["_id"]),
            email=document["email"],
            full_name=document.get("full_name", ""),
            timezone=document.get("timezone", "Asia/Kolkata"),
            created_at=document["created_at"],
            last_login=document.get("last_login", ""),
            is_active=document.get("is_active", True),
            role=document.get("role", "user"),
            workspace_id=document.get("workspace_id", ""),
            preferences=document.get("preferences") or {},
        )


class UserPublic(BaseModel):
    id: str
    email: str
    full_name: str
    timezone: str
    role: UserRole
    workspace_id: str
    is_active: bool
    created_at: str = ""
    last_login: str = ""

    @classmethod
    def from_document(cls, doc: UserDocument) -> "UserPublic":
        return cls(
            id=doc.id,
            email=doc.email,
            full_name=doc.full_name,
            timezone=doc.timezone,
            role=doc.role,
            workspace_id=doc.workspace_id,
            is_active=doc.is_active,
            created_at=doc.created_at,
            last_login=doc.last_login,
        )

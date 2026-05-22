from typing import Any

from pydantic import BaseModel, Field


class ResumeCreate(BaseModel):
    """Payload for persisting a parsed resume (pre-save)."""

    resume_url: str
    public_id: str
    filename: str
    raw_text: str = ""
    skills: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    experience_keywords: list[str] = Field(default_factory=list)

    # Reserved for future multi-user support
    user_id: str | None = None


class ResumeDocument(BaseModel):
    """Resume document as stored in MongoDB."""

    id: str
    resume_url: str
    public_id: str
    filename: str
    raw_text: str
    skills: list[str]
    emails: list[str]
    links: list[str]
    experience_keywords: list[str]
    uploaded_at: str
    created_at: str
    user_id: str | None = None

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "ResumeDocument":
        return cls(
            id=str(document["_id"]),
            resume_url=document["resume_url"],
            public_id=document["public_id"],
            filename=document["filename"],
            raw_text=document.get("raw_text", ""),
            skills=document.get("skills", []),
            emails=document.get("emails", []),
            links=document.get("links", []),
            experience_keywords=document.get("experience_keywords", []),
            uploaded_at=document["uploaded_at"],
            created_at=document["created_at"],
            user_id=document.get("user_id"),
        )

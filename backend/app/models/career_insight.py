from typing import Any

from pydantic import BaseModel, Field


class CareerInsightDocument(BaseModel):
    id: str
    insight_type: str
    title: str
    message: str
    category: str = "general"
    metadata: dict[str, Any] = Field(default_factory=dict)
    preference_id: str = ""
    created_at: str

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "CareerInsightDocument":
        return cls(
            id=str(document["_id"]),
            insight_type=document["insight_type"],
            title=document["title"],
            message=document["message"],
            category=document.get("category", "general"),
            metadata=document.get("metadata") or {},
            preference_id=document.get("preference_id", ""),
            created_at=document["created_at"],
        )


class CareerInsightsSummary(BaseModel):
    insights: list[CareerInsightDocument] = Field(default_factory=list)
    top_skills_to_learn: list[str] = Field(default_factory=list)
    strongest_alignment: str = ""
    best_source: str = ""

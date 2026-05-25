from typing import Any

from pydantic import BaseModel, Field


class WorkspaceDocument(BaseModel):
    id: str
    name: str
    owner_id: str
    created_at: str
    settings: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_mongo(cls, document: dict[str, Any]) -> "WorkspaceDocument":
        return cls(
            id=str(document["_id"]),
            name=document["name"],
            owner_id=document["owner_id"],
            created_at=document["created_at"],
            settings=document.get("settings") or {},
        )

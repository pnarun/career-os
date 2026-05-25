import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database
from app.models.workspace import WorkspaceDocument

logger = logging.getLogger(__name__)

WORKSPACES_COLLECTION = "workspaces"


class WorkspaceServiceError(Exception):
    pass


class WorkspaceNotFoundError(WorkspaceServiceError):
    pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_collection() -> AsyncIOMotorCollection:
    return get_database()[WORKSPACES_COLLECTION]


async def ensure_workspace_indexes() -> None:
    collection = _get_collection()
    await collection.create_index("owner_id")


async def create_workspace(name: str, owner_id: str, settings: dict[str, Any] | None = None) -> WorkspaceDocument:
    now = _utc_now_iso()
    document: dict[str, Any] = {
        "name": name.strip() or "My Workspace",
        "owner_id": owner_id,
        "created_at": now,
        "settings": settings or {},
    }
    result = await _get_collection().insert_one(document)
    document["_id"] = result.inserted_id
    logger.info("Workspace created name=%s owner=%s", document["name"], owner_id)
    return WorkspaceDocument.from_mongo(document)


async def get_workspace_by_id(workspace_id: str) -> WorkspaceDocument:
    try:
        object_id = ObjectId(workspace_id)
    except InvalidId as exc:
        raise WorkspaceNotFoundError(f"Invalid workspace id: {workspace_id}") from exc

    document = await _get_collection().find_one({"_id": object_id})
    if not document:
        raise WorkspaceNotFoundError(f"Workspace not found: {workspace_id}")
    return WorkspaceDocument.from_mongo(document)


async def list_workspaces_for_user(user_id: str) -> list[WorkspaceDocument]:
    cursor = _get_collection().find({"owner_id": user_id}).sort("created_at", -1)
    documents = await cursor.to_list(length=50)
    return [WorkspaceDocument.from_mongo(doc) for doc in documents]

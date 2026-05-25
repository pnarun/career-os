import logging
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database
from app.core.user_context import get_request_user_id
from app.models.resume import ResumeCreate, ResumeDocument
from app.services.cloudinary_service import ResumeUploadResult
from app.services.resume_parser_service import ParsedResumeProfile

logger = logging.getLogger(__name__)

RESUMES_COLLECTION = "resumes"


class ResumeServiceError(Exception):
    """Raised when a resume database operation fails."""


class ResumeNotFoundError(ResumeServiceError):
    """Raised when a resume document cannot be found."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_resumes_collection() -> AsyncIOMotorCollection:
    return get_database()[RESUMES_COLLECTION]


async def ensure_resume_indexes() -> None:
    collection = _get_resumes_collection()
    await collection.create_index("user_id")
    await collection.create_index([("user_id", 1), ("created_at", -1)])
    await collection.create_index([("user_id", 1), ("uploaded_at", -1)])


def build_resume_create(
    upload_result: ResumeUploadResult,
    parsed_profile: ParsedResumeProfile,
) -> ResumeCreate:
    """Map upload + parse results into a MongoDB-ready create payload."""
    return ResumeCreate(
        resume_url=upload_result["secure_url"],
        public_id=upload_result["public_id"],
        filename=upload_result["original_filename"],
        raw_text=parsed_profile.get("raw_text", ""),
        skills=parsed_profile.get("skills", []),
        emails=parsed_profile.get("emails", []),
        links=parsed_profile.get("links", []),
        experience_keywords=parsed_profile.get("experience_keywords", []),
    )


def _document_from_create(parsed_resume_data: ResumeCreate) -> dict[str, Any]:
    timestamp = _utc_now_iso()
    document: dict[str, Any] = {
        "resume_url": parsed_resume_data.resume_url,
        "public_id": parsed_resume_data.public_id,
        "filename": parsed_resume_data.filename,
        "raw_text": parsed_resume_data.raw_text,
        "skills": parsed_resume_data.skills,
        "emails": parsed_resume_data.emails,
        "links": parsed_resume_data.links,
        "experience_keywords": parsed_resume_data.experience_keywords,
        "uploaded_at": timestamp,
        "created_at": timestamp,
    }
    user_id = parsed_resume_data.user_id or get_request_user_id()
    if user_id:
        document["user_id"] = user_id
    return document


async def save_resume(parsed_resume_data: ResumeCreate) -> ResumeDocument:
    """Persist a parsed resume profile to MongoDB."""
    document = _document_from_create(parsed_resume_data)

    try:
        collection = _get_resumes_collection()
        result = await collection.insert_one(document)
        document["_id"] = result.inserted_id
        logger.info(
            "Resume saved to MongoDB: id=%s public_id=%s",
            result.inserted_id,
            parsed_resume_data.public_id,
        )
        return ResumeDocument.from_mongo(document)
    except RuntimeError as exc:
        logger.error("MongoDB not initialized: %s", exc)
        raise ResumeServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to save resume to MongoDB")
        raise ResumeServiceError("Failed to save resume") from exc


async def get_resume_by_id(resume_id: str) -> ResumeDocument:
    """Fetch a single resume by MongoDB ObjectId string."""
    try:
        object_id = ObjectId(resume_id)
    except InvalidId as exc:
        raise ResumeNotFoundError(f"Invalid resume id: {resume_id}") from exc

    try:
        collection = _get_resumes_collection()
        query: dict[str, Any] = {"_id": object_id}
        user_id = get_request_user_id()
        if user_id:
            query["user_id"] = user_id
        document = await collection.find_one(query)
    except RuntimeError as exc:
        raise ResumeServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to fetch resume id=%s", resume_id)
        raise ResumeServiceError("Failed to fetch resume") from exc

    if not document:
        raise ResumeNotFoundError(f"Resume not found: {resume_id}")

    return ResumeDocument.from_mongo(document)


def get_resume_by_id_sync(resume_id: str) -> ResumeDocument | None:
    """Sync resume fetch for Playwright worker subprocess."""
    import os

    from pymongo import MongoClient

    try:
        object_id = ObjectId(resume_id)
    except InvalidId:
        return None

    uri = os.getenv("MONGO_URI", "").strip()
    if not uri:
        return None

    client = MongoClient(uri)
    document = client["career_os"][RESUMES_COLLECTION].find_one({"_id": object_id})
    client.close()
    if not document:
        return None
    return ResumeDocument.from_mongo(document)


async def get_all_resumes() -> list[ResumeDocument]:
    """Return all resumes, newest first (ready for future user scoping)."""
    try:
        collection = _get_resumes_collection()
        query: dict[str, Any] = {}
        user_id = get_request_user_id()
        if user_id:
            query["user_id"] = user_id
        cursor = collection.find(query).sort("created_at", -1)
        documents = await cursor.to_list(length=None)
        return [ResumeDocument.from_mongo(doc) for doc in documents]
    except RuntimeError as exc:
        raise ResumeServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to list resumes")
        raise ResumeServiceError("Failed to list resumes") from exc

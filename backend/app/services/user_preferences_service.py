import logging
import re
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database
from app.models.user_preferences import (
    UserPreferencesCreate,
    UserPreferencesDocument,
    UserPreferencesUpdate,
)

logger = logging.getLogger(__name__)

PREFERENCES_COLLECTION = "user_preferences"
SCAN_TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
ALLOWED_FREQUENCIES = frozenset({"daily"})


class UserPreferencesServiceError(Exception):
    """Raised when preferences persistence fails."""


class UserPreferencesNotFoundError(UserPreferencesServiceError):
    """Raised when preferences cannot be found."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_collection() -> AsyncIOMotorCollection:
    return get_database()[PREFERENCES_COLLECTION]


def validate_scan_time(scan_time: str) -> str:
    """Validate HH:MM (24h) scan time."""
    normalized = (scan_time or "").strip()
    if not SCAN_TIME_PATTERN.match(normalized):
        raise UserPreferencesServiceError(
            "Invalid scan_time. Use 24-hour format HH:MM (e.g. 08:00)."
        )
    hour, minute = normalized.split(":")
    return f"{int(hour):02d}:{minute}"


def validate_frequency(frequency: str) -> str:
    normalized = (frequency or "daily").strip().lower()
    if normalized not in ALLOWED_FREQUENCIES:
        raise UserPreferencesServiceError(
            f"Unsupported frequency '{frequency}'. Supported: daily"
        )
    return normalized


async def save_preferences(payload: UserPreferencesCreate) -> UserPreferencesDocument:
    """Create new preferences (one record per email)."""
    scan_time = validate_scan_time(payload.scan_time)
    frequency = validate_frequency(payload.frequency)
    email = str(payload.email).strip().lower()

    try:
        collection = _get_collection()
        existing = await collection.find_one({"email": email})
        if existing:
            raise UserPreferencesServiceError(
                f"Preferences already exist for {email}. Use PUT /preferences to update."
            )

        now = _utc_now_iso()
        document: dict[str, Any] = {
            "email": email,
            "resume_id": payload.resume_id.strip(),
            "scan_time": scan_time,
            "timezone": payload.timezone.strip() or "Asia/Kolkata",
            "frequency": frequency,
            "is_active": payload.is_active,
            "created_at": now,
            "updated_at": now,
            "last_email_scan_id": "",
            "last_email_sent_at": "",
        }
        result = await collection.insert_one(document)
        document["_id"] = result.inserted_id
        logger.info("Preferences saved for email=%s id=%s", email, result.inserted_id)
        return UserPreferencesDocument.from_mongo(document)
    except UserPreferencesServiceError:
        raise
    except RuntimeError as exc:
        raise UserPreferencesServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to save preferences")
        raise UserPreferencesServiceError("Failed to save preferences") from exc


async def get_preferences() -> UserPreferencesDocument | None:
    """Return the most recently updated preferences (MVP single-user)."""
    try:
        collection = _get_collection()
        document = await collection.find_one(sort=[("updated_at", -1)])
        if not document:
            return None
        return UserPreferencesDocument.from_mongo(document)
    except RuntimeError as exc:
        raise UserPreferencesServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to fetch preferences")
        raise UserPreferencesServiceError("Failed to fetch preferences") from exc


async def get_preferences_by_id(preference_id: str) -> UserPreferencesDocument:
    try:
        object_id = ObjectId(preference_id)
    except InvalidId as exc:
        raise UserPreferencesNotFoundError(f"Invalid preference id: {preference_id}") from exc

    try:
        collection = _get_collection()
        document = await collection.find_one({"_id": object_id})
    except RuntimeError as exc:
        raise UserPreferencesServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to fetch preferences id=%s", preference_id)
        raise UserPreferencesServiceError("Failed to fetch preferences") from exc

    if not document:
        raise UserPreferencesNotFoundError(f"Preferences not found: {preference_id}")

    return UserPreferencesDocument.from_mongo(document)


async def update_preferences(
    preference_id: str,
    payload: UserPreferencesUpdate,
) -> UserPreferencesDocument:
    """Update preferences by MongoDB id."""
    try:
        object_id = ObjectId(preference_id)
    except InvalidId as exc:
        raise UserPreferencesNotFoundError(f"Invalid preference id: {preference_id}") from exc

    updates: dict[str, Any] = {}
    if payload.email is not None:
        updates["email"] = str(payload.email).strip().lower()
    if payload.resume_id is not None:
        updates["resume_id"] = payload.resume_id.strip()
    if payload.scan_time is not None:
        updates["scan_time"] = validate_scan_time(payload.scan_time)
    if payload.timezone is not None:
        updates["timezone"] = payload.timezone.strip() or "Asia/Kolkata"
    if payload.frequency is not None:
        updates["frequency"] = validate_frequency(payload.frequency)
    if payload.is_active is not None:
        updates["is_active"] = payload.is_active

    if not updates:
        return await get_preferences_by_id(preference_id)

    updates["updated_at"] = _utc_now_iso()

    try:
        collection = _get_collection()
        result = await collection.find_one_and_update(
            {"_id": object_id},
            {"$set": updates},
            return_document=True,
        )
    except RuntimeError as exc:
        raise UserPreferencesServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to update preferences id=%s", preference_id)
        raise UserPreferencesServiceError("Failed to update preferences") from exc

    if not result:
        raise UserPreferencesNotFoundError(f"Preferences not found: {preference_id}")

    logger.info("Preferences updated id=%s", preference_id)
    return UserPreferencesDocument.from_mongo(result)


async def get_active_preferences() -> list[UserPreferencesDocument]:
    """Return all active preferences for scheduler registration."""
    try:
        collection = _get_collection()
        cursor = collection.find({"is_active": True}).sort("updated_at", -1)
        documents = await cursor.to_list(length=None)
        return [UserPreferencesDocument.from_mongo(doc) for doc in documents]
    except RuntimeError as exc:
        raise UserPreferencesServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to list active preferences")
        raise UserPreferencesServiceError("Failed to list active preferences") from exc


async def mark_email_sent(preference_id: str, scan_id: str) -> None:
    """Record successful email delivery to prevent duplicate sends."""
    try:
        object_id = ObjectId(preference_id)
    except InvalidId as exc:
        raise UserPreferencesNotFoundError(f"Invalid preference id: {preference_id}") from exc

    now = _utc_now_iso()
    try:
        collection = _get_collection()
        await collection.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "last_email_scan_id": scan_id,
                    "last_email_sent_at": now,
                    "updated_at": now,
                }
            },
        )
    except RuntimeError as exc:
        raise UserPreferencesServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to mark email sent for id=%s", preference_id)
        raise UserPreferencesServiceError("Failed to update email delivery state") from exc

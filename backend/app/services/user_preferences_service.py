import logging
import re
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database
from app.core.user_context import get_request_user_id, require_request_user_id
from app.models.user_preferences import (
    UserPreferencesCreate,
    UserPreferencesDocument,
    UserPreferencesUpdate,
)

logger = logging.getLogger(__name__)

PREFERENCES_COLLECTION = "user_preferences"
SCAN_TIME_PATTERN = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
ALLOWED_FREQUENCIES = frozenset({"daily", "weekly"})
ALLOWED_DIGEST_FREQUENCIES = frozenset({"daily", "weekly"})
HIGH_MATCH_THRESHOLD = 85


def _extended_preference_fields(payload) -> dict[str, Any]:
    """Optional extended fields stored on preferences documents."""
    fields: dict[str, Any] = {}
    for name in (
        "enabled_providers",
        "provider_priority",
        "career_focus",
        "ai_strictness",
        "ats_optimization_mode",
        "interview_reminders",
        "scan_completion_alerts",
        "auto_email_on_scan",
    ):
        value = getattr(payload, name, None)
        if value is not None:
            fields[name] = value
    return fields


class UserPreferencesServiceError(Exception):
    """Raised when preferences persistence fails."""


class UserPreferencesNotFoundError(UserPreferencesServiceError):
    """Raised when preferences cannot be found."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_collection() -> AsyncIOMotorCollection:
    return get_database()[PREFERENCES_COLLECTION]


async def ensure_preferences_indexes() -> None:
    collection = _get_collection()
    await collection.create_index("user_id", unique=True)
    await collection.create_index("email")


def validate_scan_time(scan_time: str) -> str:
    """Validate HH:MM (24h) scan time."""
    normalized = (scan_time or "").strip()
    if not SCAN_TIME_PATTERN.match(normalized):
        raise UserPreferencesServiceError(
            "Invalid scan_time. Use 24-hour format HH:MM (e.g. 08:00)."
        )
    hour, minute = normalized.split(":")
    return f"{int(hour):02d}:{minute}"


def validate_digest_frequency(frequency: str) -> str:
    normalized = (frequency or "daily").strip().lower()
    if normalized not in ALLOWED_DIGEST_FREQUENCIES:
        raise UserPreferencesServiceError(
            f"Unsupported digest_frequency '{frequency}'. Supported: daily, weekly"
        )
    return normalized


def validate_min_match_threshold(value: int) -> int:
    if value < 0 or value > 100:
        raise UserPreferencesServiceError("min_match_threshold must be between 0 and 100")
    return value


def validate_frequency(frequency: str) -> str:
    normalized = (frequency or "daily").strip().lower()
    if normalized not in ALLOWED_FREQUENCIES:
        raise UserPreferencesServiceError(
            f"Unsupported frequency '{frequency}'. Supported: daily, weekly"
        )
    return normalized


async def save_preferences(
    payload: UserPreferencesCreate,
    *,
    user_id: str,
    workspace_id: str = "",
) -> UserPreferencesDocument:
    """Create preferences for a user (one record per user_id)."""
    scan_time = validate_scan_time(payload.scan_time)
    frequency = validate_frequency(payload.frequency)
    email = str(payload.email).strip().lower()

    try:
        collection = _get_collection()
        existing = await collection.find_one({"user_id": user_id})
        if existing:
            raise UserPreferencesServiceError(
                "Preferences already exist for this account. Use PUT /preferences to update."
            )

        now = _utc_now_iso()
        document: dict[str, Any] = {
            "user_id": user_id,
            "workspace_id": workspace_id,
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
            "email_notifications": payload.email_notifications,
            "in_app_notifications": payload.in_app_notifications,
            "min_match_threshold": validate_min_match_threshold(payload.min_match_threshold),
            "remote_only": payload.remote_only,
            "preferred_locations": list(payload.preferred_locations or []),
            "digest_frequency": validate_digest_frequency(payload.digest_frequency),
            "high_match_alerts": payload.high_match_alerts,
            "follow_up_reminders": payload.follow_up_reminders,
            "notice_period_days": payload.notice_period_days,
            "willing_to_relocate": payload.willing_to_relocate,
            "work_authorization": payload.work_authorization.strip(),
            "expected_salary": payload.expected_salary.strip(),
            **_extended_preference_fields(payload),
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


async def get_preferences(user_id: str | None = None) -> UserPreferencesDocument | None:
    """Return preferences for the given or request-scoped user."""
    uid = user_id or get_request_user_id()
    if not uid:
        return None
    try:
        collection = _get_collection()
        document = await collection.find_one({"user_id": uid})
        if not document:
            return None
        return UserPreferencesDocument.from_mongo(document)
    except RuntimeError as exc:
        raise UserPreferencesServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to fetch preferences")
        raise UserPreferencesServiceError("Failed to fetch preferences") from exc


async def get_preferences_by_id(
    preference_id: str,
    *,
    user_id: str | None = None,
) -> UserPreferencesDocument:
    try:
        object_id = ObjectId(preference_id)
    except InvalidId as exc:
        raise UserPreferencesNotFoundError(f"Invalid preference id: {preference_id}") from exc

    try:
        collection = _get_collection()
        query: dict[str, Any] = {"_id": object_id}
        if user_id:
            query["user_id"] = user_id
        document = await collection.find_one(query)
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
    *,
    user_id: str | None = None,
) -> UserPreferencesDocument:
    """Update preferences by MongoDB id."""
    try:
        object_id = ObjectId(preference_id)
    except InvalidId as exc:
        raise UserPreferencesNotFoundError(f"Invalid preference id: {preference_id}") from exc

    if user_id:
        await get_preferences_by_id(preference_id, user_id=user_id)

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
    if payload.email_notifications is not None:
        updates["email_notifications"] = payload.email_notifications
    if payload.in_app_notifications is not None:
        updates["in_app_notifications"] = payload.in_app_notifications
    if payload.min_match_threshold is not None:
        updates["min_match_threshold"] = validate_min_match_threshold(payload.min_match_threshold)
    if payload.remote_only is not None:
        updates["remote_only"] = payload.remote_only
    if payload.preferred_locations is not None:
        updates["preferred_locations"] = list(payload.preferred_locations)
    if payload.digest_frequency is not None:
        updates["digest_frequency"] = validate_digest_frequency(payload.digest_frequency)
    if payload.high_match_alerts is not None:
        updates["high_match_alerts"] = payload.high_match_alerts
    if payload.follow_up_reminders is not None:
        updates["follow_up_reminders"] = payload.follow_up_reminders
    if payload.notice_period_days is not None:
        updates["notice_period_days"] = payload.notice_period_days
    if payload.willing_to_relocate is not None:
        updates["willing_to_relocate"] = payload.willing_to_relocate
    if payload.work_authorization is not None:
        updates["work_authorization"] = payload.work_authorization.strip()
    if payload.expected_salary is not None:
        updates["expected_salary"] = payload.expected_salary.strip()
    updates.update(_extended_preference_fields(payload))

    if not updates:
        return await get_preferences_by_id(preference_id, user_id=user_id)

    updates["updated_at"] = _utc_now_iso()

    try:
        collection = _get_collection()
        query: dict[str, Any] = {"_id": object_id}
        if user_id:
            query["user_id"] = user_id
        result = await collection.find_one_and_update(
            query,
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

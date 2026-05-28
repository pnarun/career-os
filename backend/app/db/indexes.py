"""Centralized MongoDB index definitions and safe startup initialization."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database

logger = logging.getLogger(__name__)

_INDEX_ENSURED = False


@dataclass(frozen=True)
class IndexSpec:
    keys: list[tuple[str, int] | str]
    name: str
    unique: bool = False
    sparse: bool = False
    expire_after_seconds: int | None = None


def _idx(
    keys: list[tuple[str, int] | str],
    name: str,
    *,
    unique: bool = False,
    sparse: bool = False,
    expire_after_seconds: int | None = None,
) -> IndexSpec:
    return IndexSpec(
        keys=keys,
        name=name,
        unique=unique,
        sparse=sparse,
        expire_after_seconds=expire_after_seconds,
    )


# --- Collection index registry (high-traffic paths first) ---

JOBS_INDEXES: list[IndexSpec] = [
    _idx([("user_id", 1), ("created_at", -1)], "jobs_user_created"),
    _idx([("user_id", 1), ("source", 1)], "jobs_user_source"),
    _idx([("user_id", 1), ("scan_id", 1)], "jobs_user_scan"),
    _idx([("user_id", 1), ("location", 1)], "jobs_user_location"),
    _idx([("user_id", 1), ("title", 1)], "jobs_user_title"),
    _idx([("source", 1), ("created_at", -1)], "jobs_source_created"),
    _idx([("user_id", 1), ("is_latest_scan", 1)], "jobs_user_latest_scan"),
    _idx([("user_id", 1), ("apply_url", 1)], "jobs_user_apply_url"),
    _idx([("user_id", 1), ("title", 1), ("company", 1)], "jobs_user_title_company"),
    _idx([("user_id", 1), ("match_percentage", -1)], "jobs_user_match"),
    _idx([("user_id", 1), ("status", 1)], "jobs_user_status"),
]

SCAN_SESSIONS_INDEXES: list[IndexSpec] = [
    _idx([("user_id", 1), ("created_at", -1)], "scan_sessions_user_created"),
    _idx([("scan_id", 1)], "scan_sessions_scan_id", unique=True),
    _idx([("user_id", 1), ("scan_id", 1)], "scan_sessions_user_scan"),
]

BROWSER_SESSIONS_INDEXES: list[IndexSpec] = [
    _idx([("user_id", 1), ("platform", 1)], "browser_sessions_user_platform", unique=True),
    _idx([("updated_at", -1)], "browser_sessions_updated"),
]

USERS_INDEXES: list[IndexSpec] = [
    _idx([("email", 1)], "users_email", unique=True),
    _idx([("workspace_id", 1)], "users_workspace"),
]

CAREER_INSIGHTS_INDEXES: list[IndexSpec] = [
    _idx([("user_id", 1)], "career_insights_user", sparse=True),
    _idx([("created_at", -1)], "career_insights_created"),
    _idx([("preference_id", 1)], "career_insights_preference"),
    _idx([("insight_type", 1)], "career_insights_type"),
]

APPLICATIONS_INDEXES: list[IndexSpec] = [
    _idx([("user_id", 1), ("updated_at", -1)], "applications_user_updated"),
    _idx([("user_id", 1), ("status", 1)], "applications_user_status"),
    _idx([("user_id", 1), ("applied_at", -1)], "applications_user_applied"),
    _idx([("job_id", 1)], "applications_job_id"),
    _idx([("apply_url", 1)], "applications_apply_url", sparse=True),
]

RESUMES_INDEXES: list[IndexSpec] = [
    _idx([("user_id", 1), ("created_at", -1)], "resumes_user_created"),
    _idx([("user_id", 1), ("uploaded_at", -1)], "resumes_user_uploaded"),
]

USER_PREFERENCES_INDEXES: list[IndexSpec] = [
    _idx([("user_id", 1)], "preferences_user", unique=True),
    _idx([("email", 1)], "preferences_email"),
]

NOTIFICATIONS_INDEXES: list[IndexSpec] = [
    _idx([("user_id", 1), ("created_at", -1)], "notifications_user_created", sparse=True),
    _idx([("created_at", -1)], "notifications_created"),
    _idx([("read", 1)], "notifications_read"),
    _idx([("type", 1)], "notifications_type"),
    _idx([("preference_id", 1)], "notifications_preference"),
]

AUTOMATION_RUNS_INDEXES: list[IndexSpec] = [
    _idx([("user_id", 1), ("started_at", -1)], "automation_runs_user_started", sparse=True),
    _idx([("started_at", -1)], "automation_runs_started"),
    _idx([("run_type", 1)], "automation_runs_type"),
    _idx([("preference_id", 1)], "automation_runs_preference"),
    _idx([("status", 1)], "automation_runs_status", sparse=True),
]

COLLECTION_INDEX_REGISTRY: dict[str, list[IndexSpec]] = {
    "jobs": JOBS_INDEXES,
    "scan_sessions": SCAN_SESSIONS_INDEXES,
    "browser_sessions": BROWSER_SESSIONS_INDEXES,
    "users": USERS_INDEXES,
    "career_insights": CAREER_INSIGHTS_INDEXES,
    "applications": APPLICATIONS_INDEXES,
    "resumes": RESUMES_INDEXES,
    "user_preferences": USER_PREFERENCES_INDEXES,
    "notifications": NOTIFICATIONS_INDEXES,
    "automation_runs": AUTOMATION_RUNS_INDEXES,
    # Auth & auxiliary (kept for single startup path)
    "auth_refresh_tokens": [
        _idx([("token_hash", 1)], "refresh_tokens_hash", unique=True),
        _idx([("user_id", 1)], "refresh_tokens_user"),
        _idx([("expires_at", 1)], "refresh_tokens_expires"),
    ],
    "password_reset_otps": [
        _idx([("email", 1)], "password_resets_email"),
        _idx([("expires_at", 1)], "password_resets_expires", expire_after_seconds=0),
    ],
    "workspaces": [
        _idx([("owner_id", 1)], "workspaces_owner"),
    ],
    "linkedin_pairing_sessions": [
        _idx([("pairing_code", 1)], "linkedin_pairing_code"),
        _idx([("user_id", 1), ("used", 1), ("expires_at", 1)], "linkedin_pairing_user"),
        _idx([("expires_at", 1)], "linkedin_pairing_expires"),
    ],
    "copilot_insights": [
        _idx([("created_at", -1)], "copilot_insights_created"),
        _idx([("session_id", 1)], "copilot_insights_session"),
    ],
    "copilot_sessions": [
        _idx([("session_id", 1)], "copilot_sessions_id", unique=True),
        _idx([("updated_at", -1)], "copilot_sessions_updated"),
    ],
    "interview_prep_progress": [
        _idx([("updated_at", -1)], "interview_prep_updated"),
        _idx([("job_id", 1)], "interview_prep_job"),
    ],
    "interview_web_questions_cache": [
        _idx([("cache_key", 1)], "web_question_cache_key", unique=True),
        _idx([("expires_at", 1)], "web_question_expires", expire_after_seconds=0),
    ],
    "apply_sessions": [
        _idx([("session_id", 1)], "apply_sessions_id", unique=True),
        _idx([("created_at", -1)], "apply_sessions_created"),
    ],
    "apply_history": [
        _idx([("created_at", -1)], "apply_history_created"),
        _idx([("session_id", 1)], "apply_history_session"),
    ],
    "apply_errors": [
        _idx([("created_at", -1)], "apply_errors_created"),
    ],
}


def _normalize_keys(keys: list[tuple[str, int] | str]) -> list[tuple[str, int]]:
    normalized: list[tuple[str, int]] = []
    for item in keys:
        if isinstance(item, str):
            normalized.append((item, 1))
        else:
            normalized.append(item)
    return normalized


async def ensure_collection_indexes(
    collection_name: str,
    specs: list[IndexSpec] | None = None,
    *,
    database: AsyncIOMotorDatabase | None = None,
) -> list[str]:
    """Create indexes idempotently; returns names ensured this call."""
    db = get_database() if database is None else database
    collection = db[collection_name]
    index_specs = specs or COLLECTION_INDEX_REGISTRY.get(collection_name, [])
    created: list[str] = []

    for spec in index_specs:
        kwargs: dict[str, Any] = {"name": spec.name, "unique": spec.unique}
        if spec.sparse:
            kwargs["sparse"] = True
        if spec.expire_after_seconds is not None:
            kwargs["expireAfterSeconds"] = spec.expire_after_seconds

        try:
            await collection.create_index(_normalize_keys(spec.keys), **kwargs)
            created.append(spec.name)
            logger.info(
                "INDEX_CREATED collection=%s index=%s",
                collection_name,
                spec.name,
                extra={
                    "event": "index_created",
                    "collection": collection_name,
                    "index": spec.name,
                },
            )
        except Exception as exc:
            # Index already exists with same/different options — safe to continue
            logger.debug(
                "Index ensure skipped collection=%s index=%s: %s",
                collection_name,
                spec.name,
                exc,
            )

    return created


async def ensure_all_mongo_indexes(*, force: bool = False) -> dict[str, list[str]]:
    """
    Ensure all registered indexes once per process (unless force=True).
    Called from application startup.
    """
    global _INDEX_ENSURED
    if _INDEX_ENSURED and not force:
        return {}

    db = get_database()
    summary: dict[str, list[str]] = {}

    for collection_name in COLLECTION_INDEX_REGISTRY:
        summary[collection_name] = await ensure_collection_indexes(
            collection_name,
            database=db,
        )

    _INDEX_ENSURED = True
    logger.info(
        "Mongo index initialization complete collections=%d",
        len(summary),
        extra={"event": "mongo_indexes_ready", "collections": len(summary)},
    )
    return summary

"""Application lifecycle tracking — save, apply, status, notes, analytics."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database
from app.core.user_context import get_request_user_id
from app.models.application import (
    APPLICATION_STATUSES,
    ApplicationAnalytics,
    ApplicationCreatePayload,
    ApplicationDocument,
    TimelineEvent,
)
from app.services.resume_service import get_all_resumes

logger = logging.getLogger(__name__)

APPLICATIONS_COLLECTION = "applications"

ACTIVE_STATUSES = frozenset(APPLICATION_STATUSES)
INTERVIEW_STATUSES = frozenset({"interview", "assessment"})
REJECTION_STATUSES = frozenset({"rejected", "ghosted"})


class ApplicationServiceError(Exception):
    """Raised when an application database operation fails."""


class ApplicationNotFoundError(ApplicationServiceError):
    """Raised when an application document cannot be found."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_collection() -> AsyncIOMotorCollection:
    return get_database()[APPLICATIONS_COLLECTION]


async def ensure_application_indexes() -> None:
    """Create indexes for application queries."""
    collection = _get_collection()
    await collection.create_index("status")
    await collection.create_index("applied_at")
    await collection.create_index("company")
    await collection.create_index("source")
    await collection.create_index("job_id")
    await collection.create_index([("updated_at", -1)])
    await collection.create_index("user_id")
    logger.info("Application collection indexes ensured")


def _scoped_query(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    query: dict[str, Any] = dict(extra or {})
    user_id = get_request_user_id()
    if user_id:
        query["user_id"] = user_id
    return query


def _append_status_history(
    document: dict[str, Any],
    status: str,
    timestamp: str | None = None,
) -> list[dict[str, str]]:
    history = list(document.get("status_history") or [])
    ts = timestamp or _utc_now_iso()
    if history and history[-1].get("status") == status:
        return history
    history.append({"status": status, "timestamp": ts})
    return history


def _job_lookup_key(payload: ApplicationCreatePayload) -> dict[str, Any]:
    base: dict[str, Any] = {}
    if payload.job_id.strip():
        base["job_id"] = payload.job_id.strip()
    elif payload.apply_url.strip():
        base["apply_url"] = payload.apply_url.strip()
    else:
        base["title"] = payload.title.strip()
        base["company"] = payload.company.strip()
    return _scoped_query(base)


def _base_document(payload: ApplicationCreatePayload, resume_id: str = "") -> dict[str, Any]:
    now = _utc_now_iso()
    doc = {
        "job_id": payload.job_id.strip(),
        "title": payload.title.strip(),
        "company": payload.company.strip(),
        "source": payload.source.strip(),
        "apply_url": payload.apply_url.strip(),
        "match_score": int(payload.match_score or 0),
        "resume_id": resume_id or payload.resume_id.strip(),
        "remote": bool(payload.remote),
        "easy_apply": bool(payload.easy_apply),
        "location": payload.location.strip(),
        "matched_skills": list(payload.matched_skills or []),
        "notes": payload.notes.strip(),
        "updated_at": now,
    }
    user_id = get_request_user_id()
    if user_id:
        doc["user_id"] = user_id
    return doc


async def _resolve_latest_resume_id() -> str:
    resumes = await get_all_resumes()
    return resumes[0].id if resumes else ""


async def _find_existing(payload: ApplicationCreatePayload) -> dict[str, Any] | None:
    collection = _get_collection()
    lookup = _job_lookup_key(payload)
    return await collection.find_one(lookup)


async def save_job(payload: ApplicationCreatePayload) -> ApplicationDocument:
    """Bookmark a job with status=saved."""
    collection = _get_collection()
    resume_id = payload.resume_id.strip() or await _resolve_latest_resume_id()
    now = _utc_now_iso()
    lookup = _job_lookup_key(payload)
    existing = await collection.find_one(lookup)

    if existing:
        history = _append_status_history(existing, "saved", now)
        update = {
            **_base_document(payload, resume_id),
            "status": "saved",
            "status_history": history,
        }
        await collection.update_one({"_id": existing["_id"]}, {"$set": update})
        existing.update(update)
        return ApplicationDocument.from_mongo(existing)

    document = {
        **_base_document(payload, resume_id),
        "status": "saved",
        "applied_at": "",
        "created_at": now,
        "status_history": [{"status": "saved", "timestamp": now}],
    }
    result = await collection.insert_one(document)
    document["_id"] = result.inserted_id
    logger.info("Application saved: id=%s title=%s", result.inserted_id, payload.title)
    return ApplicationDocument.from_mongo(document)


async def mark_applied(payload: ApplicationCreatePayload) -> ApplicationDocument:
    """Track that the user applied; does NOT auto-submit applications."""
    collection = _get_collection()
    resume_id = payload.resume_id.strip() or await _resolve_latest_resume_id()
    now = _utc_now_iso()
    lookup = _job_lookup_key(payload)
    existing = await collection.find_one(lookup)

    if existing:
        history = _append_status_history(existing, "applied", now)
        update = {
            **_base_document(payload, resume_id),
            "status": "applied",
            "applied_at": existing.get("applied_at") or now,
            "status_history": history,
        }
        await collection.update_one({"_id": existing["_id"]}, {"$set": update})
        existing.update(update)
        return ApplicationDocument.from_mongo(existing)

    document = {
        **_base_document(payload, resume_id),
        "status": "applied",
        "applied_at": now,
        "created_at": now,
        "status_history": [
            {"status": "saved", "timestamp": now},
            {"status": "applied", "timestamp": now},
        ],
    }
    result = await collection.insert_one(document)
    document["_id"] = result.inserted_id
    logger.info("Application marked applied: id=%s title=%s", result.inserted_id, payload.title)
    return ApplicationDocument.from_mongo(document)


async def update_application_status(
    application_id: str,
    status: str,
) -> ApplicationDocument:
    if status not in ACTIVE_STATUSES:
        raise ApplicationServiceError(f"Invalid status: {status}")

    collection = _get_collection()
    try:
        oid = ObjectId(application_id)
    except InvalidId as exc:
        raise ApplicationNotFoundError("Application not found") from exc

    existing = await collection.find_one(_scoped_query({"_id": oid}))
    if not existing:
        raise ApplicationNotFoundError("Application not found")

    now = _utc_now_iso()
    history = _append_status_history(existing, status, now)
    update: dict[str, Any] = {
        "status": status,
        "updated_at": now,
        "status_history": history,
    }
    if status == "applied" and not existing.get("applied_at"):
        update["applied_at"] = now

    await collection.update_one(_scoped_query({"_id": oid}), {"$set": update})
    existing.update(update)
    return ApplicationDocument.from_mongo(existing)


async def update_application_notes(
    application_id: str,
    notes: str,
) -> ApplicationDocument:
    collection = _get_collection()
    try:
        oid = ObjectId(application_id)
    except InvalidId as exc:
        raise ApplicationNotFoundError("Application not found") from exc

    existing = await collection.find_one(_scoped_query({"_id": oid}))
    if not existing:
        raise ApplicationNotFoundError("Application not found")

    now = _utc_now_iso()
    await collection.update_one(
        _scoped_query({"_id": oid}),
        {"$set": {"notes": notes.strip(), "updated_at": now}},
    )
    existing["notes"] = notes.strip()
    existing["updated_at"] = now
    return ApplicationDocument.from_mongo(existing)


async def delete_application(application_id: str) -> None:
    collection = _get_collection()
    try:
        oid = ObjectId(application_id)
    except InvalidId as exc:
        raise ApplicationNotFoundError("Application not found") from exc

    result = await collection.delete_one(_scoped_query({"_id": oid}))
    if result.deleted_count == 0:
        raise ApplicationNotFoundError("Application not found")


async def list_applications(
    *,
    status: str | None = None,
    source: str | None = None,
    remote: bool | None = None,
    min_match: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    page: int | None = None,
    limit: int | None = None,
) -> list[ApplicationDocument]:
    collection = _get_collection()
    query: dict[str, Any] = _scoped_query()

    if status:
        query["status"] = status.strip().lower()
    if source:
        query["source"] = source.strip().lower()
    if remote is not None:
        query["remote"] = remote
    if min_match is not None and min_match > 0:
        query["match_score"] = {"$gte": min_match}
    if date_from or date_to:
        applied_filter: dict[str, str] = {}
        if date_from:
            applied_filter["$gte"] = date_from
        if date_to:
            applied_filter["$lte"] = date_to
        query["applied_at"] = applied_filter

    max_limit = 500
    effective_limit = min(max(1, limit or max_limit), max_limit)
    skip = 0
    if page is not None and page > 1:
        skip = (page - 1) * effective_limit
    cursor = collection.find(query).sort("updated_at", -1).skip(skip).limit(effective_limit)
    documents = await cursor.to_list(length=effective_limit)
    return [ApplicationDocument.from_mongo(doc) for doc in documents]


async def build_job_application_map() -> dict[str, ApplicationDocument]:
    """Return applications keyed by job_id for bulk UI lookups."""
    applications = await list_applications(limit=500)
    mapping: dict[str, ApplicationDocument] = {}
    for app in applications:
        job_key = (app.job_id or "").strip()
        if job_key and job_key not in mapping:
            mapping[job_key] = app
    return mapping


async def get_application_by_job_id(job_id: str) -> ApplicationDocument | None:
    if not job_id.strip():
        return None
    collection = _get_collection()
    document = await collection.find_one({"job_id": job_id.strip()})
    if not document:
        return None
    return ApplicationDocument.from_mongo(document)


async def build_application_analytics() -> ApplicationAnalytics:
    collection = _get_collection()
    documents = await collection.find(_scoped_query()).to_list(length=1000)

    total_saved = sum(1 for doc in documents if doc.get("status") == "saved")
    total_applied = sum(1 for doc in documents if doc.get("status") == "applied")
    interviews = sum(
        1 for doc in documents if doc.get("status") in INTERVIEW_STATUSES
    )
    offers = sum(1 for doc in documents if doc.get("status") == "offer")
    rejections = sum(
        1 for doc in documents if doc.get("status") in REJECTION_STATUSES
    )

    applied_or_beyond = [
        doc
        for doc in documents
        if doc.get("status") not in ("saved", "withdrawn")
        and doc.get("applied_at")
    ]
    responded = sum(
        1
        for doc in applied_or_beyond
        if doc.get("status")
        in INTERVIEW_STATUSES | {"offer"} | REJECTION_STATUSES
    )
    response_rate = (
        round((responded / len(applied_or_beyond)) * 100, 1)
        if applied_or_beyond
        else 0.0
    )

    source_counter: Counter[str] = Counter()
    skill_counter: Counter[str] = Counter()
    for doc in documents:
        source = str(doc.get("source") or "unknown").lower()
        if source:
            source_counter[source] += 1
        for skill in doc.get("matched_skills") or []:
            skill_counter[str(skill)] += 1

    top_sources = [
        {"source": name, "count": count}
        for name, count in source_counter.most_common(5)
    ]
    top_skills = [
        {"skill": name, "count": count}
        for name, count in skill_counter.most_common(8)
    ]

    return ApplicationAnalytics(
        total_saved=total_saved,
        total_applied=total_applied,
        interviews=interviews,
        offers=offers,
        rejections=rejections,
        response_rate=response_rate,
        top_sources=top_sources,
        top_skills=top_skills,
    )


async def get_application_timeline(
    application_id: str | None = None,
) -> list[TimelineEvent]:
    collection = _get_collection()
    events: list[TimelineEvent] = []

    if application_id:
        try:
            oid = ObjectId(application_id)
        except InvalidId as exc:
            raise ApplicationNotFoundError("Application not found") from exc
        document = await collection.find_one({"_id": oid})
        if not document:
            raise ApplicationNotFoundError("Application not found")
        documents = [document]
    else:
        documents = await collection.find({}).sort("updated_at", -1).to_list(length=200)

    for doc in documents:
        app_id = str(doc["_id"])
        title = doc.get("title", "")
        company = doc.get("company", "")
        for entry in doc.get("status_history") or []:
            events.append(
                TimelineEvent(
                    application_id=app_id,
                    title=title,
                    company=company,
                    status=str(entry.get("status", "")),
                    timestamp=str(entry.get("timestamp", "")),
                )
            )

    events.sort(key=lambda event: event.timestamp, reverse=True)
    return events

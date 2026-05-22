import logging
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database
from app.models.job import JobCreate, JobDocument, JobHistoryItem, ScanFetchResponse
from app.services.job_fetch_service import fetch_public_jobs_async
from app.services.job_quality_service import filter_jobs_by_quality
from app.services.match_engine_service import match_resume_to_job
from app.services.resume_service import (
    ResumeNotFoundError,
    get_all_resumes,
    get_resume_by_id,
)

logger = logging.getLogger(__name__)

JOBS_COLLECTION = "jobs"
SCAN_BATCH_LIMIT = 50
HISTORY_DEBUG_LIMIT = 500

# Sort: match % → quality score → remote priority → recency
JOB_SORT_ORDER = [
    ("match_percentage", -1),
    ("job_quality_score", -1),
    ("remote_priority", -1),
    ("created_at", -1),
]


class JobServiceError(Exception):
    """Raised when a job database operation fails."""


class JobDiscoveryError(JobServiceError):
    """Raised when job discovery cannot complete."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_scan_id() -> str:
    """Generate scan id e.g. scan_2026_05_22_18_45 (UTC)."""
    now = datetime.now(timezone.utc)
    return now.strftime("scan_%Y_%m_%d_%H_%M")


def _get_jobs_collection() -> AsyncIOMotorCollection:
    return get_database()[JOBS_COLLECTION]


def _document_from_create(job_data: JobCreate) -> dict[str, Any]:
    return {
        "title": job_data.title,
        "company": job_data.company,
        "location": job_data.location,
        "apply_url": job_data.apply_url,
        "source": job_data.source,
        "description": job_data.description,
        "easy_apply": job_data.easy_apply,
        "job_type": job_data.job_type,
        "remote_priority": job_data.remote_priority,
        "india_focused": job_data.india_focused,
        "matched_skills": job_data.matched_skills,
        "missing_skills": job_data.missing_skills,
        "match_percentage": job_data.match_percentage,
        "recommendation": job_data.recommendation,
        "scan_id": job_data.scan_id,
        "scan_timestamp": job_data.scan_timestamp,
        "is_latest_scan": job_data.is_latest_scan,
        "already_seen": job_data.already_seen,
        "has_apply_url": job_data.has_apply_url,
        "is_easy_apply_possible": job_data.is_easy_apply_possible,
        "job_quality_score": job_data.job_quality_score,
        "is_suspicious": job_data.is_suspicious,
        "quality_flags": job_data.quality_flags,
        "created_at": _utc_now_iso(),
    }


def build_job_create(
    normalized_job: dict[str, Any],
    match_analysis: dict[str, Any],
    scan_id: str,
    scan_timestamp: str,
) -> JobCreate:
    return JobCreate(
        title=normalized_job["title"],
        company=normalized_job["company"],
        location=normalized_job["location"],
        apply_url=normalized_job["apply_url"],
        source=normalized_job["source"],
        description=normalized_job["description"],
        easy_apply=normalized_job["easy_apply"],
        job_type=normalized_job["job_type"],
        remote_priority=normalized_job.get("remote_priority", False),
        india_focused=normalized_job.get("india_focused", False),
        matched_skills=match_analysis["matched_skills"],
        missing_skills=match_analysis["missing_skills"],
        match_percentage=match_analysis["match_percentage"],
        recommendation=match_analysis["recommendation"],
        scan_id=scan_id,
        scan_timestamp=scan_timestamp,
        is_latest_scan=True,
        already_seen=True,
        has_apply_url=normalized_job.get("has_apply_url", False),
        is_easy_apply_possible=normalized_job.get("is_easy_apply_possible", False),
        job_quality_score=normalized_job.get("job_quality_score", 0),
        is_suspicious=normalized_job.get("is_suspicious", False),
        quality_flags=normalized_job.get("quality_flags", []),
    )


def sort_job_documents(jobs: list[JobDocument]) -> list[JobDocument]:
    """Sort jobs by match %, quality score, remote priority, then recency."""
    return sorted(
        jobs,
        key=lambda job: (
            job.match_percentage,
            job.job_quality_score,
            int(job.remote_priority),
            job.created_at,
        ),
        reverse=True,
    )


def rank_job_candidate(
    normalized_job: dict[str, Any],
    match_analysis: dict[str, Any],
) -> dict[str, Any]:
    """Attach match scores for in-memory ranking before persistence."""
    return {
        **normalized_job,
        "matched_skills": match_analysis["matched_skills"],
        "missing_skills": match_analysis["missing_skills"],
        "match_percentage": match_analysis["match_percentage"],
        "recommendation": match_analysis["recommendation"],
    }


async def start_new_scan_session() -> None:
    """Archive the previous latest scan batch; mark those jobs as already seen."""
    try:
        collection = _get_jobs_collection()
        result = await collection.update_many(
            {"is_latest_scan": True},
            {"$set": {"is_latest_scan": False, "already_seen": True}},
        )
        if result.modified_count:
            logger.info(
                "Archived previous scan batch: %d jobs marked already_seen",
                result.modified_count,
            )
    except RuntimeError as exc:
        raise JobServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to start new scan session")
        raise JobServiceError("Failed to start scan session") from exc


async def was_job_already_shown(
    apply_url: str,
    title: str,
    company: str,
) -> bool:
    """True if this job was stored in any prior scan (apply_url or title+company)."""
    try:
        collection = _get_jobs_collection()
        if apply_url.strip():
            existing = await collection.find_one({"apply_url": apply_url.strip()})
            if existing:
                return True

        existing = await collection.find_one(
            {
                "title": title.strip(),
                "company": company.strip(),
            }
        )
        return existing is not None
    except RuntimeError as exc:
        raise JobServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to check if job was already shown")
        raise JobServiceError("Failed to check job history") from exc


async def save_job(job_data: JobCreate) -> JobDocument:
    """Persist a job document to MongoDB."""
    document = _document_from_create(job_data)

    try:
        collection = _get_jobs_collection()
        result = await collection.insert_one(document)
        document["_id"] = result.inserted_id
        logger.info(
            "Job saved: id=%s scan=%s title=%s",
            result.inserted_id,
            job_data.scan_id,
            job_data.title,
        )
        return JobDocument.from_mongo(document)
    except RuntimeError as exc:
        raise JobServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to save job")
        raise JobServiceError("Failed to save job") from exc


async def get_latest_scan_jobs() -> list[JobDocument]:
    """Return only the current latest scan batch (max 50), prioritized."""
    try:
        collection = _get_jobs_collection()
        cursor = (
            collection.find({"is_latest_scan": True})
            .sort(JOB_SORT_ORDER)
            .limit(SCAN_BATCH_LIMIT)
        )
        documents = await cursor.to_list(length=SCAN_BATCH_LIMIT)
        jobs = [JobDocument.from_mongo(doc) for doc in documents]
        return sort_job_documents(jobs)
    except RuntimeError as exc:
        raise JobServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to fetch latest scan jobs")
        raise JobServiceError("Failed to fetch latest scan jobs") from exc


async def get_job_history(limit: int = HISTORY_DEBUG_LIMIT) -> list[JobHistoryItem]:
    """Return recent job history for debug (ignores scan session flags)."""
    try:
        collection = _get_jobs_collection()
        cursor = collection.find({}).sort("created_at", -1).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [JobHistoryItem.from_mongo(doc) for doc in documents]
    except RuntimeError as exc:
        raise JobServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to fetch job history")
        raise JobServiceError("Failed to fetch job history") from exc


async def get_all_jobs() -> list[JobDocument]:
    """Return full job history (admin/debug use)."""
    try:
        collection = _get_jobs_collection()
        cursor = collection.find({}).sort(JOB_SORT_ORDER)
        documents = await cursor.to_list(length=None)
        jobs = [JobDocument.from_mongo(doc) for doc in documents]
        return sort_job_documents(jobs)
    except RuntimeError as exc:
        raise JobServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to list jobs")
        raise JobServiceError("Failed to list jobs") from exc


async def _resolve_resume_for_scan(resume_id: str | None):
    """Pick resume by id or fall back to newest upload."""
    if resume_id:
        try:
            return await get_resume_by_id(resume_id)
        except ResumeNotFoundError as exc:
            raise JobDiscoveryError(str(exc)) from exc

    resumes = await get_all_resumes()
    if not resumes:
        raise JobDiscoveryError(
            "No resume found. Upload a resume before fetching jobs."
        )
    return resumes[0]


async def discover_and_store_jobs(resume_id: str | None = None) -> ScanFetchResponse:
    """
    Run a new scan session: fetch, filter, match, rank, store top 50 fresh jobs.
    Previous MongoDB history is preserved; only latest scan is active in the feed.
    """
    scan_id = generate_scan_id()
    scan_timestamp = _utc_now_iso()

    await start_new_scan_session()

    normalized_jobs, filtered_out = await fetch_public_jobs_async()
    raw_fetched = len(normalized_jobs) + filtered_out

    latest_resume = await _resolve_resume_for_scan(resume_id)
    skipped_already_shown = 0
    quality_rejected = 0
    matched_candidates: list[dict[str, Any]] = []

    for job in normalized_jobs:
        if await was_job_already_shown(
            job["apply_url"],
            job["title"],
            job["company"],
        ):
            skipped_already_shown += 1
            continue

        description = job["description"] or f"{job['title']} at {job['company']}"
        analysis = match_resume_to_job(latest_resume.skills, description)
        matched_candidates.append(rank_job_candidate(job, analysis))

    ranked_candidates, quality_rejected = filter_jobs_by_quality(matched_candidates)

    ranked_candidates = sorted(
        ranked_candidates,
        key=lambda item: (
            item["match_percentage"],
            item.get("job_quality_score", 0),
            int(item.get("remote_priority", False)),
            item.get("title", ""),
        ),
        reverse=True,
    )
    top_candidates = ranked_candidates[:SCAN_BATCH_LIMIT]

    stored_count = 0
    for candidate in top_candidates:
        job_payload = build_job_create(
            candidate,
            {
                "matched_skills": candidate["matched_skills"],
                "missing_skills": candidate["missing_skills"],
                "match_percentage": candidate["match_percentage"],
                "recommendation": candidate["recommendation"],
            },
            scan_id,
            scan_timestamp,
        )
        await save_job(job_payload)
        stored_count += 1

    logger.info(
        "Scan %s complete: stored=%d skipped_history=%d",
        scan_id,
        stored_count,
        skipped_already_shown,
    )

    return ScanFetchResponse(
        scan_id=scan_id,
        scan_timestamp=scan_timestamp,
        fetched=raw_fetched,
        filtered=filtered_out,
        accepted=len(normalized_jobs),
        stored=stored_count,
        skipped_already_shown=skipped_already_shown,
        top_jobs_returned=stored_count,
        quality_rejected=quality_rejected,
        resume_id=latest_resume.id,
    )

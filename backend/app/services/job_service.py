import asyncio
import logging
from collections.abc import Callable
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.config import settings
from app.db.mongo_perf import explain_find_if_debug, timed_to_list

from app.realtime.provider_status_stream import emit_provider_batch, emit_provider_status
from app.realtime.scan_event_service import emit_ai_scoring_complete, emit_jobs_fetched
from app.core.database import get_database
from app.core.user_context import get_request_user_id, get_request_workspace_id
from app.automation.browser.session_status_service import is_session_ready
from app.models.job import JobCreate, JobDocument, JobHistoryItem, ScanFetchResponse
from app.models.unified_feed import UnifiedFeedResponse
from app.models.linkedin_fetch import LinkedInFetchResponse
from app.services.unified_feed_service import (
    SortOption,
    build_unified_feed_from_documents,
    get_feed_metadata_from_latest_scan,
)
from app.services.job_fetch_service import fetch_public_jobs_async
from app.services.job_filter_service import filter_normalized_jobs
from app.services.job_sources.linkedin_playwright_source import (
    LinkedInPlaywrightJobSource,
)
from app.services.job_sources.linkedin_search_context import build_search_keywords
from app.services.scan_analytics_service import build_scan_summary
from app.services.scan_session_service import save_scan_session
from app.services.job_quality_service import score_jobs_with_quality
from app.services.match_engine_service import match_resume_to_job
from app.services.job_match_scoring_service import ResumeProfile
from app.services.resume_service import (
    ResumeNotFoundError,
    get_all_resumes,
    get_resume_by_id,
)

logger = logging.getLogger(__name__)

JOBS_COLLECTION = "jobs"
SCAN_BATCH_LIMIT = 200
HISTORY_DEBUG_LIMIT = 500
ANALYTICS_HISTORY_LIMIT = 1500

_latest_scan_jobs_cache: ContextVar[list[JobDocument] | None] = ContextVar(
    "latest_scan_jobs_cache",
    default=None,
)
_latest_scan_jobs_lock = asyncio.Lock()

_analytics_jobs_cache: ContextVar[tuple[int, list[JobDocument]] | None] = ContextVar(
    "analytics_jobs_cache",
    default=None,
)
_analytics_jobs_lock = asyncio.Lock()

# Fields required for feed, dashboard previews, and analytics (excludes unused blobs).
JOB_READ_PROJECTION: dict[str, int] = {
    "_id": 1,
    "user_id": 1,
    "title": 1,
    "company": 1,
    "company_tag": 1,
    "location": 1,
    "apply_url": 1,
    "source": 1,
    "description": 1,
    "easy_apply": 1,
    "job_type": 1,
    "remote_priority": 1,
    "india_focused": 1,
    "actionable_in_india": 1,
    "matched_skills": 1,
    "missing_skills": 1,
    "match_percentage": 1,
    "recommendation": 1,
    "created_at": 1,
    "scan_id": 1,
    "scan_timestamp": 1,
    "is_latest_scan": 1,
    "already_seen": 1,
    "has_apply_url": 1,
    "is_easy_apply_possible": 1,
    "job_quality_score": 1,
    "is_suspicious": 1,
    "quality_flags": 1,
    "status": 1,
}


def clear_latest_scan_jobs_cache() -> None:
    _latest_scan_jobs_cache.set(None)
    _analytics_jobs_cache.set(None)


async def prime_analytics_job_caches() -> None:
    """Warm per-request job caches before parallel analytics sections run."""
    from app.services.career_analytics._constants import ANALYTICS_HISTORY_SAMPLE

    await get_latest_scan_jobs()
    await get_all_jobs(limit=ANALYTICS_HISTORY_SAMPLE)

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


def _scoped_query(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    query: dict[str, Any] = dict(extra or {})
    user_id = get_request_user_id()
    if user_id:
        query["user_id"] = user_id
    return query


async def ensure_job_indexes() -> None:
    from app.db.indexes import ensure_collection_indexes

    await ensure_collection_indexes(JOBS_COLLECTION)


def _document_from_create(job_data: JobCreate) -> dict[str, Any]:
    document: dict[str, Any] = {
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
    user_id = get_request_user_id()
    if user_id:
        document["user_id"] = user_id
        workspace_id = get_request_workspace_id()
        if workspace_id:
            document["workspace_id"] = workspace_id
    return document


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
        actionable_in_india=normalized_job.get("actionable_in_india", True),
        company_tag=normalized_job.get("company_tag", ""),
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
    """Sort jobs by match %, India-actionable, quality, remote, then recency."""
    return sorted(
        jobs,
        key=lambda job: (
            job.match_percentage,
            int(getattr(job, "actionable_in_india", True)),
            job.job_quality_score,
            int(job.remote_priority),
            int(job.india_focused),
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
        "match_score": match_analysis["match_percentage"],
        "recommendation": match_analysis["recommendation"],
        "strengths": match_analysis.get("strengths", []),
        "recommendations": match_analysis.get("recommendations", []),
        "experience_alignment": match_analysis.get("experience_alignment", ""),
        "career_fit": match_analysis.get("career_fit", ""),
        "why_match": match_analysis.get("why_match", []),
        "match_breakdown": match_analysis.get("match_breakdown", {}),
    }


async def start_new_scan_session() -> None:
    """Archive the previous latest scan batch; mark those jobs as already seen."""
    clear_latest_scan_jobs_cache()
    try:
        collection = _get_jobs_collection()
        result = await collection.update_many(
            _scoped_query({"is_latest_scan": True}),
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


class ShownJobCache:
    """In-memory set of known jobs for the current scan (batch-loaded)."""

    __slots__ = ("apply_urls", "title_company")

    def __init__(self) -> None:
        self.apply_urls: set[str] = set()
        self.title_company: set[tuple[str, str]] = set()

    def contains(self, apply_url: str, title: str, company: str) -> bool:
        url = apply_url.strip()
        if url and url in self.apply_urls:
            return True
        key = (title.strip().lower(), company.strip().lower())
        return key in self.title_company


async def load_shown_job_cache() -> ShownJobCache:
    """Batch-load prior job keys to avoid N+1 find_one during scans."""
    cache = ShownJobCache()
    try:
        collection = _get_jobs_collection()
        cursor = collection.find(
            _scoped_query(),
            {"apply_url": 1, "title": 1, "company": 1},
        )
        async for doc in cursor:
            url = (doc.get("apply_url") or "").strip()
            if url:
                cache.apply_urls.add(url)
            title = (doc.get("title") or "").strip().lower()
            company = (doc.get("company") or "").strip().lower()
            if title and company:
                cache.title_company.add((title, company))
    except RuntimeError as exc:
        raise JobServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to preload shown job cache")
        raise JobServiceError("Failed to preload job history") from exc
    return cache


async def was_job_already_shown(
    apply_url: str,
    title: str,
    company: str,
    *,
    cache: ShownJobCache | None = None,
) -> bool:
    """True if this job was stored in any prior scan (apply_url or title+company)."""
    if cache is not None:
        return cache.contains(apply_url, title, company)
    try:
        collection = _get_jobs_collection()
        if apply_url.strip():
            existing = await collection.find_one(
                _scoped_query({"apply_url": apply_url.strip()}),
                {"_id": 1},
            )
            if existing:
                return True

        existing = await collection.find_one(
            _scoped_query(
                {
                    "title": title.strip(),
                    "company": company.strip(),
                }
            ),
            {"_id": 1},
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


async def get_unified_jobs_feed(
    *,
    providers: list[str] | None = None,
    remote_only: bool = False,
    easy_apply_only: bool = False,
    min_match: int | None = None,
    keyword: str | None = None,
    sort_by: str = "default",
    strong_matches_only: bool = False,
    remote_high_match: bool = False,
    easy_apply_high_match: bool = False,
    company: str | None = None,
) -> UnifiedFeedResponse:
    """Build unified feed from the latest stored scan batch."""
    jobs = await get_latest_scan_jobs()
    provider_counts, duplicates_removed, scan_id, scan_timestamp = (
        await get_feed_metadata_from_latest_scan()
    )
    sort_key: SortOption = sort_by if sort_by in {
        "match",
        "quality",
        "source_priority",
        "newest",
        "default",
    } else "default"

    resume_profile: ResumeProfile | None = None
    resumes = await get_all_resumes()
    if resumes:
        latest = resumes[0]
        resume_profile = ResumeProfile(
            skills=latest.skills,
            experience_keywords=latest.experience_keywords,
            links=latest.links,
            raw_text=latest.raw_text,
        )

    return await build_unified_feed_from_documents(
        jobs,
        provider_raw_counts=provider_counts,
        duplicates_removed=duplicates_removed,
        scan_id=scan_id,
        scan_timestamp=scan_timestamp,
        resume_profile=resume_profile,
        providers=providers,
        remote_only=remote_only,
        easy_apply_only=easy_apply_only,
        min_match=min_match,
        keyword=keyword,
        sort_by=sort_key,
        strong_matches_only=strong_matches_only,
        remote_high_match=remote_high_match,
        easy_apply_high_match=easy_apply_high_match,
        company=company,
    )


async def get_latest_scan_jobs() -> list[JobDocument]:
    """Return only the current latest scan batch (max 200), prioritized."""
    cached = _latest_scan_jobs_cache.get()
    if cached is not None:
        return cached

    async with _latest_scan_jobs_lock:
        cached = _latest_scan_jobs_cache.get()
        if cached is not None:
            return cached

        try:
            collection = _get_jobs_collection()
            query = _scoped_query({"is_latest_scan": True})
            await explain_find_if_debug(collection, query, sort=list(JOB_SORT_ORDER))
            cursor = (
                collection.find(query, JOB_READ_PROJECTION)
                .sort(JOB_SORT_ORDER)
                .limit(SCAN_BATCH_LIMIT)
            )
            documents = await timed_to_list(
                cursor,
                operation="find_latest_scan_jobs",
                collection=JOBS_COLLECTION,
                max_length=SCAN_BATCH_LIMIT,
            )
            jobs = sort_job_documents([JobDocument.from_mongo(doc) for doc in documents])
            _latest_scan_jobs_cache.set(jobs)
            return jobs
        except RuntimeError as exc:
            raise JobServiceError("Database is not available") from exc
        except Exception as exc:
            logger.exception("Failed to fetch latest scan jobs")
            raise JobServiceError("Failed to fetch latest scan jobs") from exc


async def get_job_history(
    *,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[JobHistoryItem], int]:
    """Return paginated job history (ignores scan session flags)."""
    page = max(1, page)
    limit = min(max(1, limit), HISTORY_DEBUG_LIMIT)
    skip = (page - 1) * limit
    try:
        collection = _get_jobs_collection()
        query = _scoped_query()
        total = await collection.count_documents(query)
        cursor = (
            collection.find(query, JOB_READ_PROJECTION)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        documents = await timed_to_list(
            cursor,
            operation="find_job_history",
            collection=JOBS_COLLECTION,
            max_length=limit,
        )
        items = [JobHistoryItem.from_mongo(doc) for doc in documents]
        return items, total
    except RuntimeError as exc:
        raise JobServiceError("Database is not available") from exc
    except Exception as exc:
        logger.exception("Failed to fetch job history")
        raise JobServiceError("Failed to fetch job history") from exc


async def get_all_jobs(*, limit: int | None = None) -> list[JobDocument]:
    """Return job history for analytics (optional cap to avoid full collection scans)."""
    cap = limit
    if cap is None:
        cap = int(getattr(settings, "MONGO_ANALYTICS_HISTORY_LIMIT", ANALYTICS_HISTORY_LIMIT))

    cached_entry = _analytics_jobs_cache.get()
    if cached_entry is not None and cached_entry[0] == cap:
        return cached_entry[1]

    async with _analytics_jobs_lock:
        cached_entry = _analytics_jobs_cache.get()
        if cached_entry is not None and cached_entry[0] == cap:
            return cached_entry[1]

        try:
            collection = _get_jobs_collection()
            query = _scoped_query()
            await explain_find_if_debug(collection, query, sort=list(JOB_SORT_ORDER))
            cursor = (
                collection.find(query, JOB_READ_PROJECTION)
                .sort(JOB_SORT_ORDER)
                .limit(cap)
            )
            documents = await timed_to_list(
                cursor,
                operation="find_all_jobs",
                collection=JOBS_COLLECTION,
                max_length=cap,
            )
            jobs = sort_job_documents([JobDocument.from_mongo(doc) for doc in documents])
            _analytics_jobs_cache.set((cap, jobs))
            return jobs
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


ProviderCompleteCallback = Callable[[str, str, int, str], None]
PhaseCallback = Callable[[str, int], None]


async def discover_and_store_jobs(
    resume_id: str | None = None,
    *,
    scan_id: str | None = None,
    on_provider_complete: ProviderCompleteCallback | None = None,
    on_phase: PhaseCallback | None = None,
) -> ScanFetchResponse:
    """
    Run a new scan session: fetch, score, match, rank, store up to 200 fresh jobs.
    Previous MongoDB history is preserved; only latest scan is active in the feed.
    """
    scan_id = scan_id or generate_scan_id()
    scan_timestamp = _utc_now_iso()

    await start_new_scan_session()

    if on_phase:
        on_phase("fetching", 10)

    fetch_result = await fetch_public_jobs_async(on_provider_complete=on_provider_complete)
    normalized_jobs = fetch_result.jobs
    filtered_out = fetch_result.filtered_rejected
    aggregation = fetch_result.aggregation
    pre_filter_jobs = fetch_result.pre_filter_jobs
    raw_fetched = aggregation.total_fetched

    user_id = get_request_user_id() or ""
    if user_id:
        provider_batch: list[dict[str, Any]] = []
        for provider, count in (aggregation.sources or {}).items():
            status = "failed" if provider in aggregation.failed_sources else "success"
            provider_batch.append(
                {
                    "provider": provider,
                    "status": status,
                    "count": int(count or 0),
                    "error": aggregation.source_errors.get(provider, ""),
                }
            )
        if "linkedin" not in aggregation.sources:
            linkedin_meta = fetch_result.linkedin_fetch or {}
            linkedin_status = linkedin_meta.get("status", "")
            linkedin_count = int(linkedin_meta.get("count") or linkedin_meta.get("jobs_count") or 0)
            if linkedin_status:
                provider_batch.append(
                    {
                        "provider": "linkedin",
                        "status": "success" if linkedin_status == "success" and linkedin_count else "failed",
                        "count": linkedin_count,
                        "error": str(linkedin_meta.get("error") or "LinkedIn fetch failed"),
                    }
                )
        if provider_batch:
            await emit_provider_batch(user_id, providers=provider_batch, scan_id=scan_id)

    if on_phase:
        on_phase("processing", 65)

    latest_resume = await _resolve_resume_for_scan(resume_id)
    from app.services.application_service import was_job_already_applied
    from app.services.user_preferences_service import get_preferences

    prefs = await get_preferences()
    target_companies = list(getattr(prefs, "target_companies", None) or []) if prefs else []

    skipped_already_applied = 0
    quality_rejected = 0
    matched_candidates: list[dict[str, Any]] = []

    for job in normalized_jobs:
        if await was_job_already_applied(
            job["apply_url"],
            job["title"],
            job["company"],
        ):
            skipped_already_applied += 1
            continue

        company_lower = (job.get("company") or "").lower()
        for tc in target_companies:
            if tc and tc.lower() in company_lower:
                job["company_tag"] = tc
                break

        description = job["description"] or f"{job['title']} at {job['company']}"
        analysis = match_resume_to_job(
            latest_resume.skills,
            description,
            job_title=job["title"],
            job_location=job.get("location", ""),
            job_remote=bool(
                job.get("remote_priority") or (job.get("job_type") or "").lower() == "remote"
            ),
            resume_keywords=latest_resume.experience_keywords,
            resume_raw_text=latest_resume.raw_text,
        )
        matched_candidates.append(rank_job_candidate(job, analysis))

    ranked_candidates, quality_rejected = score_jobs_with_quality(matched_candidates)

    ranked_candidates = sorted(
        ranked_candidates,
        key=lambda item: (
            item["match_percentage"],
            int(item.get("actionable_in_india", True)),
            item.get("job_quality_score", 0),
            int(item.get("remote_priority", False)),
            int(item.get("india_focused", False)),
            item.get("title", ""),
        ),
        reverse=True,
    )
    top_candidates = ranked_candidates[:SCAN_BATCH_LIMIT]

    if on_phase:
        on_phase("storing", 85)

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

    scan_summary = build_scan_summary(
        aggregation=aggregation,
        pre_filter_jobs=pre_filter_jobs,
        qualified_jobs=stored_count,
        filtered_rejected=filtered_out,
        quality_rejected=quality_rejected,
    )

    try:
        await save_scan_session(
            scan_id,
            scan_timestamp,
            scan_summary,
            resume_id=latest_resume.id,
            user_id=get_request_user_id() or "",
            workspace_id=get_request_workspace_id() or "",
        )
    except Exception:
        logger.exception("Failed to persist scan session analytics (scan continues)")

    logger.info(
        "Scan %s complete: stored=%d skipped_applied=%d",
        scan_id,
        stored_count,
        skipped_already_applied,
    )

    if user_id:
        await emit_ai_scoring_complete(
            user_id,
            scan_id=scan_id,
            stored=stored_count,
            matched=len(matched_candidates),
        )
        from app.services.cache_invalidation import invalidate_after_scan_complete

        invalidate_after_scan_complete(user_id)

    clear_latest_scan_jobs_cache()

    return ScanFetchResponse(
        scan_id=scan_id,
        scan_timestamp=scan_timestamp,
        fetched=raw_fetched,
        filtered=filtered_out,
        accepted=len(normalized_jobs),
        stored=stored_count,
        skipped_already_shown=skipped_already_applied,
        top_jobs_returned=stored_count,
        quality_rejected=quality_rejected,
        resume_id=latest_resume.id,
        sources=aggregation.sources,
        failed_sources=aggregation.failed_sources,
        source_errors=dict(aggregation.source_errors),
        provider_status=list(scan_summary.provider_status),
        scan_summary=scan_summary,
    )


async def fetch_and_merge_linkedin_jobs(
    resume_id: str | None = None,
) -> LinkedInFetchResponse:
    """
    Headless LinkedIn discovery using saved session; merge into the latest scan feed.
    """
    if not is_session_ready("linkedin"):
        return LinkedInFetchResponse(
            status="session_invalid",
            message=(
                "LinkedIn isn't connected yet. Open Scans & Automation → Automation "
                "and complete the one-time Career Lens setup."
            ),
            session_valid=False,
        )

    resume = await _resolve_resume_for_scan(resume_id)
    search_keywords = build_search_keywords(resume)
    from app.services.application_service import was_job_already_applied

    adapter = LinkedInPlaywrightJobSource()
    try:
        result = await adapter.fetch_jobs(resume_id=resume.id)
    except Exception as exc:
        logger.exception("LinkedIn fetch failed")
        return LinkedInFetchResponse(
            status="error",
            message=str(exc),
            session_valid=True,
            search_keywords=search_keywords,
        )

    if result.error:
        session_invalid = "session" in result.error.lower()
        return LinkedInFetchResponse(
            status="session_invalid" if session_invalid else "error",
            message=result.error,
            session_valid=not session_invalid,
            search_keywords=search_keywords,
        )

    pipeline = [job.to_pipeline_dict() for job in result.jobs]
    filtered_jobs, filtered_out = filter_normalized_jobs(pipeline)

    latest_batch = await get_latest_scan_jobs()
    if latest_batch:
        scan_id = latest_batch[0].scan_id or generate_scan_id()
        scan_timestamp = latest_batch[0].scan_timestamp or _utc_now_iso()
    else:
        scan_id = generate_scan_id()
        scan_timestamp = _utc_now_iso()

    skipped = 0
    matched_candidates: list[dict[str, Any]] = []
    for job in filtered_jobs:
        if await was_job_already_applied(
            job["apply_url"],
            job["title"],
            job["company"],
        ):
            skipped += 1
            continue

        description = job["description"] or f"{job['title']} at {job['company']}"
        analysis = match_resume_to_job(
            resume.skills,
            description,
            job_title=job["title"],
            job_location=job.get("location", ""),
            job_remote=bool(
                job.get("remote_priority") or (job.get("job_type") or "").lower() == "remote"
            ),
            resume_keywords=resume.experience_keywords,
            resume_raw_text=resume.raw_text,
        )
        matched_candidates.append(rank_job_candidate(job, analysis))

    ranked_candidates, quality_rejected = score_jobs_with_quality(matched_candidates)

    stored_jobs: list[JobDocument] = []
    for candidate in ranked_candidates:
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
        stored_jobs.append(await save_job(job_payload))

    easy_apply = sum(1 for j in result.jobs if j.easy_apply)
    status = "ok" if stored_jobs or result.jobs else "empty"
    message = (
        f"Stored {len(stored_jobs)} LinkedIn jobs in the latest scan."
        if stored_jobs
        else "No new LinkedIn jobs to store."
        if result.jobs
        else "No LinkedIn jobs returned."
    )

    logger.info(
        "LinkedIn merge scan=%s fetched=%d filtered=%d stored=%d skipped=%d quality_rejected=%d",
        scan_id,
        len(result.jobs),
        filtered_out,
        len(stored_jobs),
        skipped,
        quality_rejected,
    )

    user_id = get_request_user_id() or ""
    if user_id and stored_jobs:
        from app.services.cache_invalidation import invalidate_after_jobs_mutated

        invalidate_after_jobs_mutated(user_id)

    return LinkedInFetchResponse(
        status=status,
        message=message,
        session_valid=True,
        jobs_fetched=len(result.jobs),
        jobs_filtered=filtered_out,
        jobs_stored=len(stored_jobs),
        jobs_skipped=skipped,
        easy_apply_count=easy_apply,
        search_keywords=search_keywords,
        scan_id=scan_id,
        jobs=sort_job_documents(stored_jobs),
    )

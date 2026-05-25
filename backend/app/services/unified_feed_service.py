"""Unified multi-provider jobs feed pipeline."""

from __future__ import annotations

import logging
from typing import Any, Literal

from app.models.job import JobDocument
from app.models.unified_feed import UnifiedFeedJob, UnifiedFeedResponse
from app.services.job_dedupe_service import get_source_priority
from app.services.job_match_scoring_service import JobMatchResult, ResumeProfile, score_resume_against_job
from app.services.scan_session_service import get_latest_scan_session

logger = logging.getLogger(__name__)

SortOption = Literal[
    "match",
    "quality",
    "source_priority",
    "newest",
    "default",
]

KNOWN_PROVIDERS = (
    "linkedin",
    "instahyre",
    "naukri",
    "indeed",
    "remoteok",
    "arbeitnow",
)


STRONG_MATCH_MIN = 75
HIGH_MATCH_MIN = 60
FEED_DESCRIPTION_MAX = 400


def _truncate_description(text: str, max_len: int = FEED_DESCRIPTION_MAX) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[:max_len].rstrip() + "…"


def apply_match_result_to_feed_job(
    feed_job: UnifiedFeedJob,
    match: JobMatchResult,
) -> UnifiedFeedJob:
    skills = list(dict.fromkeys([*match["matched_skills"], *match["missing_skills"]]))
    return feed_job.model_copy(
        update={
            "match_score": match["match_score"],
            "matched_skills": match["matched_skills"],
            "missing_skills": match["missing_skills"],
            "skills": skills,
            "recommendation": match["recommendation"],
            "strengths": match["strengths"],
            "recommendations": match["recommendations"],
            "experience_alignment": match["experience_alignment"],
            "career_fit": match["career_fit"],
            "why_match": match["why_match"],
            "match_breakdown": match["match_breakdown"],
        }
    )


def score_feed_job_from_resume(
    feed_job: UnifiedFeedJob,
    resume: ResumeProfile,
) -> UnifiedFeedJob:
    match = score_resume_against_job(
        resume,
        {
            "title": feed_job.title,
            "description": feed_job.description or f"{feed_job.title} at {feed_job.company}",
            "location": feed_job.location,
            "remote": feed_job.remote,
            "experience_level": feed_job.experience_level,
        },
    )
    return apply_match_result_to_feed_job(feed_job, match)


def document_to_feed_job(job: JobDocument) -> UnifiedFeedJob:
    """Map stored job document to unified feed schema."""
    remote = bool(job.remote_priority or (job.job_type or "").lower() == "remote")
    skills = list(dict.fromkeys([*job.matched_skills, *job.missing_skills]))
    return UnifiedFeedJob(
        job_id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        description=_truncate_description(job.description),
        apply_url=job.apply_url,
        source=job.source,
        source_priority=get_source_priority(job.source),
        easy_apply=bool(job.easy_apply or job.is_easy_apply_possible),
        remote=remote,
        salary="",
        posted_at=job.scan_timestamp or job.created_at,
        match_score=job.match_percentage,
        job_quality_score=job.job_quality_score,
        skills=skills,
        experience_level="",
        recommendation=job.recommendation,
        matched_skills=job.matched_skills,
        missing_skills=job.missing_skills,
        scan_id=job.scan_id,
        scan_timestamp=job.scan_timestamp,
        has_apply_url=job.has_apply_url,
        is_suspicious=job.is_suspicious,
        quality_flags=job.quality_flags,
    )


def dict_to_feed_job(job: dict[str, Any]) -> UnifiedFeedJob:
    """Map in-memory pipeline dict to unified feed schema."""
    source = str(job.get("source", ""))
    remote = bool(
        job.get("remote")
        or job.get("remote_priority")
        or (job.get("job_type") or "").lower() == "remote"
    )
    matched = list(job.get("matched_skills") or [])
    missing = list(job.get("missing_skills") or [])
    skills = list(dict.fromkeys([*matched, *missing, *(job.get("tags") or [])]))
    return UnifiedFeedJob(
        job_id=str(job.get("job_id") or job.get("source_job_id") or ""),
        title=str(job.get("title", "")),
        company=str(job.get("company", "")),
        location=str(job.get("location", "")),
        description=str(job.get("description", "")),
        apply_url=str(job.get("apply_url", "")),
        source=source,
        source_priority=get_source_priority(source),
        easy_apply=bool(job.get("easy_apply") or job.get("is_easy_apply_possible")),
        remote=remote,
        salary=str(job.get("salary") or ""),
        posted_at=str(job.get("posted_at") or job.get("fetch_timestamp") or ""),
        match_score=int(job.get("match_score") or job.get("match_percentage") or 0),
        job_quality_score=int(job.get("job_quality_score") or 0),
        skills=skills,
        experience_level=str(job.get("experience_level") or ""),
        recommendation=str(job.get("recommendation") or ""),
        matched_skills=matched,
        missing_skills=missing,
        strengths=list(job.get("strengths") or []),
        recommendations=list(job.get("recommendations") or []),
        experience_alignment=str(job.get("experience_alignment") or ""),
        career_fit=str(job.get("career_fit") or ""),
        why_match=list(job.get("why_match") or []),
        match_breakdown=dict(job.get("match_breakdown") or {}),
        has_apply_url=bool(job.get("has_apply_url")),
        is_suspicious=bool(job.get("is_suspicious")),
        quality_flags=list(job.get("quality_flags") or []),
        metadata=dict(job.get("metadata") or {}),
    )


def sort_feed_jobs(
    jobs: list[UnifiedFeedJob],
    sort_by: SortOption = "default",
) -> list[UnifiedFeedJob]:
    if sort_by == "match":
        return sorted(jobs, key=lambda j: j.match_score, reverse=True)
    if sort_by == "quality":
        return sorted(jobs, key=lambda j: j.job_quality_score, reverse=True)
    if sort_by == "source_priority":
        return sorted(jobs, key=lambda j: j.source_priority, reverse=True)
    if sort_by == "newest":
        return sorted(jobs, key=lambda j: j.posted_at, reverse=True)

    return sorted(
        jobs,
        key=lambda j: (
            j.match_score,
            j.job_quality_score,
            j.source_priority,
            j.posted_at,
        ),
        reverse=True,
    )


def apply_feed_filters(
    jobs: list[UnifiedFeedJob],
    *,
    providers: list[str] | None = None,
    remote_only: bool = False,
    easy_apply_only: bool = False,
    min_match: int | None = None,
    keyword: str | None = None,
    sort_by: SortOption = "default",
    strong_matches_only: bool = False,
    remote_high_match: bool = False,
    easy_apply_high_match: bool = False,
) -> list[UnifiedFeedJob]:
    filtered = jobs

    if strong_matches_only:
        min_match = max(min_match or 0, STRONG_MATCH_MIN)

    if remote_high_match:
        remote_only = True
        min_match = max(min_match or 0, HIGH_MATCH_MIN)

    if easy_apply_high_match:
        easy_apply_only = True
        min_match = max(min_match or 0, HIGH_MATCH_MIN)

    if providers:
        allowed = {p.strip().lower().replace(" ", "") for p in providers if p.strip()}
        filtered = [
            j
            for j in filtered
            if j.source.strip().lower().replace(" ", "") in allowed
        ]

    if remote_only:
        filtered = [j for j in filtered if j.remote]

    if easy_apply_only:
        filtered = [j for j in filtered if j.easy_apply]

    if min_match is not None and min_match > 0:
        filtered = [j for j in filtered if j.match_score >= min_match]

    if keyword and keyword.strip():
        needle = keyword.strip().lower()
        filtered = [
            j
            for j in filtered
            if needle in j.title.lower()
            or needle in j.company.lower()
            or needle in j.location.lower()
            or needle in j.description.lower()
            or any(needle in skill.lower() for skill in j.skills)
        ]

    return sort_feed_jobs(filtered, sort_by)


def build_provider_counts(
    provider_raw_counts: dict[str, int] | None,
) -> dict[str, int]:
    counts = {name: 0 for name in KNOWN_PROVIDERS}
    if not provider_raw_counts:
        return counts
    for name, count in provider_raw_counts.items():
        key = name.strip().lower().replace(" ", "")
        counts[key] = int(count)
    return counts


async def build_unified_feed_from_documents(
    jobs: list[JobDocument],
    *,
    provider_raw_counts: dict[str, int] | None = None,
    duplicates_removed: int = 0,
    scan_id: str = "",
    scan_timestamp: str = "",
    resume_profile: ResumeProfile | None = None,
    providers: list[str] | None = None,
    remote_only: bool = False,
    easy_apply_only: bool = False,
    min_match: int | None = None,
    keyword: str | None = None,
    sort_by: SortOption = "default",
    strong_matches_only: bool = False,
    remote_high_match: bool = False,
    easy_apply_high_match: bool = False,
) -> UnifiedFeedResponse:
    feed_jobs: list[UnifiedFeedJob] = []
    for job in jobs:
        feed_job = document_to_feed_job(job)
        if resume_profile:
            feed_job = score_feed_job_from_resume(feed_job, resume_profile)
        feed_jobs.append(feed_job)

    filtered = apply_feed_filters(
        feed_jobs,
        providers=providers,
        remote_only=remote_only,
        easy_apply_only=easy_apply_only,
        min_match=min_match,
        keyword=keyword,
        sort_by=sort_by,
        strong_matches_only=strong_matches_only,
        remote_high_match=remote_high_match,
        easy_apply_high_match=easy_apply_high_match,
    )
    provider_counts = build_provider_counts(provider_raw_counts)

    return UnifiedFeedResponse(
        total_jobs=len(filtered),
        duplicates_removed=duplicates_removed,
        providers=provider_counts,
        jobs=filtered,
        scan_id=scan_id,
        scan_timestamp=scan_timestamp,
    )


async def run_unified_fetch_pipeline(resume_skills: list[str]) -> dict[str, Any]:
    """
    Fetch → normalize → dedupe → filter → score → sort.
    Returns pipeline metadata plus ranked feed job dicts (not persisted).
    """
    from app.services.job_fetch_service import fetch_public_jobs_async
    from app.services.job_quality_service import filter_jobs_by_quality
    from app.services.job_service import rank_job_candidate
    from app.services.job_match_scoring_service import ResumeProfile, score_resume_against_job

    fetch_result = await fetch_public_jobs_async()
    aggregation = fetch_result.aggregation

    duplicates_removed = max(0, aggregation.total_fetched - aggregation.total_after_dedupe)

    resume_profile = ResumeProfile(skills=resume_skills, experience_keywords=[], raw_text="")

    scored: list[dict[str, Any]] = []
    for job in fetch_result.jobs:
        description = job.get("description") or f"{job['title']} at {job['company']}"
        match = score_resume_against_job(
            resume_profile,
            {
                "title": job.get("title", ""),
                "description": description,
                "location": job.get("location", ""),
                "remote": bool(job.get("remote") or job.get("remote_priority")),
            },
        )
        analysis = {
            "match_percentage": match["match_score"],
            "matched_skills": match["matched_skills"],
            "missing_skills": match["missing_skills"],
            "recommendation": match["recommendation"],
            "strengths": match["strengths"],
            "recommendations": match["recommendations"],
            "experience_alignment": match["experience_alignment"],
            "career_fit": match["career_fit"],
            "why_match": match["why_match"],
            "match_breakdown": match["match_breakdown"],
            "job_skills": match["job_skills"],
        }
        scored.append(rank_job_candidate(job, analysis))

    ranked, quality_rejected = filter_jobs_by_quality(scored)
    feed_jobs = [dict_to_feed_job(job) for job in ranked]
    sorted_jobs = sort_feed_jobs(feed_jobs, "default")

    return {
        "jobs": sorted_jobs,
        "duplicates_removed": duplicates_removed,
        "providers": build_provider_counts(aggregation.sources),
        "aggregation": aggregation,
        "filtered_rejected": fetch_result.filtered_rejected,
        "quality_rejected": quality_rejected,
        "pre_filter_count": len(fetch_result.pre_filter_jobs),
    }


async def get_feed_metadata_from_latest_scan() -> tuple[dict[str, int], int, str, str]:
    """Load provider counts and dedupe stats from the latest scan session."""
    from app.core.user_context import get_request_user_id

    user_id = get_request_user_id() or ""
    session = await get_latest_scan_session(user_id) if user_id else None
    if not session:
        return {}, 0, "", ""

    return (
        dict(session.source_breakdown),
        int(session.duplicates_removed or 0),
        session.scan_id,
        session.scan_timestamp,
    )

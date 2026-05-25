import logging
from typing import Any

from app.models.scan_session import ScanSummaryDetail
from app.services.job_filter_service import is_india_location_job, is_remote_job
from app.services.job_sources.aggregator.aggregator_service import get_registered_sources
from app.services.job_sources.base.provider_diagnostics import (
    ProviderFetchDiagnostic,
    classify_message,
    diagnostic_failure,
    diagnostic_success,
)
from app.services.job_sources.base.source_result import AggregatorFetchResult

logger = logging.getLogger(__name__)

KNOWN_PLATFORM_SOURCES = (
    "linkedin",
    "naukri",
    "indeed",
    "instahyre",
    "remoteok",
    "arbeitnow",
)


def _is_international_job(job: dict[str, Any]) -> bool:
    if is_india_location_job(job) or is_remote_job(job):
        return False
    location = (job.get("location") or "").lower()
    if location and location not in ("remote", "unknown"):
        return True
    return False


def build_location_breakdown(jobs: list[dict[str, Any]]) -> dict[str, int]:
    india = remote = international = 0
    for job in jobs:
        if is_india_location_job(job):
            india += 1
        if is_remote_job(job):
            remote += 1
        if _is_international_job(job):
            international += 1
    return {
        "india": india,
        "remote": remote,
        "international": international,
    }


def build_source_breakdown(
    aggregation: AggregatorFetchResult,
) -> dict[str, int]:
    """Merge fetch counts with known platforms (0 if absent)."""
    breakdown: dict[str, int] = {name: 0 for name in KNOWN_PLATFORM_SOURCES}
    for name, count in aggregation.sources.items():
        breakdown[name] = count
    return breakdown


def build_provider_status_list(
    aggregation: AggregatorFetchResult,
) -> list[ProviderFetchDiagnostic]:
    """One diagnostic per known platform (success or explicit failure)."""
    by_source = {d.source: d for d in aggregation.provider_diagnostics}
    ordered: list[ProviderFetchDiagnostic] = []

    for name in KNOWN_PLATFORM_SOURCES:
        if name in by_source:
            ordered.append(by_source[name])
            continue

        count = aggregation.sources.get(name, 0)
        error_message = aggregation.source_errors.get(name, "")

        if count > 0:
            ordered.append(
                diagnostic_success(name, jobs_fetched=count, duration_ms=0)
            )
            continue

        if name in aggregation.failed_sources or error_message:
            error_type, requires_auth, session_valid = classify_message(
                error_message or f"{name} fetch failed"
            )
            ordered.append(
                diagnostic_failure(
                    name,
                    error_type=error_type,
                    error_message=error_message or f"{name} fetch failed",
                    requires_auth=requires_auth,
                    session_valid=session_valid,
                )
            )
            continue

        ordered.append(
            diagnostic_failure(
                name,
                error_type="unknown",
                error_message=f"{name} was not included in this scan run",
            )
        )

    for diagnostic in aggregation.provider_diagnostics:
        if diagnostic.source not in KNOWN_PLATFORM_SOURCES:
            ordered.append(diagnostic)

    return ordered


def resolve_top_source(sources: dict[str, int]) -> tuple[str, int]:
    if not sources:
        return "", 0
    top_name = max(sources, key=lambda k: sources[k])
    return top_name, sources[top_name]


def build_scan_summary(
    *,
    aggregation: AggregatorFetchResult,
    pre_filter_jobs: list[dict[str, Any]],
    qualified_jobs: int,
    filtered_rejected: int,
    quality_rejected: int = 0,
) -> ScanSummaryDetail:
    """
    Build scan_summary analytics from aggregator + pipeline outcomes.
    """
    total_fetched = aggregation.total_fetched
    sources = build_source_breakdown(aggregation)
    failed_sources = list(aggregation.failed_sources)
    provider_status = build_provider_status_list(aggregation)
    top_source, top_source_count = resolve_top_source(sources)
    locations = build_location_breakdown(pre_filter_jobs)

    rejected_jobs = max(
        0,
        total_fetched - qualified_jobs,
    )
    duplicates_removed = max(0, total_fetched - aggregation.total_after_dedupe)
    platforms_scanned = len(get_registered_sources())

    summary = ScanSummaryDetail(
        total_fetched=total_fetched,
        qualified_jobs=qualified_jobs,
        rejected_jobs=rejected_jobs,
        duplicates_removed=duplicates_removed,
        sources=sources,
        failed_sources=failed_sources,
        top_source=top_source,
        top_source_count=top_source_count,
        locations=locations,
        platforms_scanned=platforms_scanned,
        provider_status=[d.model_dump() for d in provider_status],
        source_errors=dict(aggregation.source_errors),
    )

    logger.info(
        "[SCAN][SUMMARY] total_fetched=%d qualified=%d rejected=%d filtered=%d quality_rejected=%d",
        summary.total_fetched,
        summary.qualified_jobs,
        summary.rejected_jobs,
        filtered_rejected,
        quality_rejected,
    )
    for diagnostic in provider_status:
        if diagnostic.status == "success":
            logger.info(
                "[SCAN][SOURCE] source=%s status=success jobs=%d duration_ms=%d",
                diagnostic.source,
                diagnostic.jobs_fetched,
                diagnostic.duration_ms,
            )
        else:
            logger.warning(
                "[SCAN][SOURCE] source=%s status=%s error_type=%s message=%s",
                diagnostic.source,
                diagnostic.status,
                diagnostic.error_type,
                diagnostic.error_message,
            )

    if top_source:
        logger.info(
            "[SCAN][SUMMARY] top_source=%s count=%d",
            top_source,
            top_source_count,
        )

    return summary

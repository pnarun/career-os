import asyncio
import logging
from dataclasses import dataclass, field

from app.services.job_filter_service import filter_normalized_jobs
from app.services.job_dedupe_service import dedupe_jobs
from app.services.job_sources.aggregator.aggregator_service import aggregate_jobs
from app.services.job_sources.base.provider_diagnostics import (
    classify_message,
    diagnostic_failure,
    diagnostic_from_exception,
)
from app.services.job_sources.base.source_result import (
    AggregatorFetchResult,
    NormalizedSourceJob,
    SourceFetchResult,
)
from app.services.job_sources.linkedin_playwright_source import (
    LinkedInPlaywrightJobSource,
)

logger = logging.getLogger(__name__)


class JobFetchError(Exception):
    """Raised when job aggregation fails catastrophically."""


@dataclass
class PublicJobsFetchResult:
    """Jobs ready for match pipeline plus aggregation metadata."""

    jobs: list[dict]
    filtered_rejected: int
    aggregation: AggregatorFetchResult
    pre_filter_jobs: list[dict]
    linkedin_fetch: dict = field(default_factory=dict)


def _pipeline_dicts_to_normalized(jobs: list[dict]) -> list[NormalizedSourceJob]:
    normalized: list[NormalizedSourceJob] = []
    for job in jobs:
        try:
            normalized.append(
                NormalizedSourceJob(
                    source=str(job.get("source", "unknown")),
                    source_job_id=str(job.get("source_job_id", "")),
                    title=str(job.get("title", "")),
                    company=str(job.get("company", "")),
                    location=str(job.get("location", "")),
                    remote=bool(job.get("remote") or job.get("job_type") == "remote"),
                    apply_url=str(job.get("apply_url", "")),
                    description=str(job.get("description", "")),
                    posted_at=str(job.get("posted_at", "")),
                    fetch_timestamp=str(job.get("fetch_timestamp", "")),
                    metadata=dict(job.get("metadata") or {}),
                    easy_apply=bool(job.get("easy_apply")),
                    job_type=str(job.get("job_type", "")),
                    tags=list(job.get("tags") or []),
                )
            )
        except Exception:
            continue
    return normalized


def merge_and_dedupe_pipeline_jobs(
    existing: list[dict],
    supplemental: list[dict],
) -> list[dict]:
    combined = _pipeline_dicts_to_normalized(existing) + _pipeline_dicts_to_normalized(
        supplemental
    )
    dedupe_result = dedupe_jobs(combined)
    return [job.to_pipeline_dict() for job in dedupe_result.jobs]


def _upsert_provider_diagnostic(aggregation: AggregatorFetchResult, diagnostic) -> None:
    for index, existing in enumerate(aggregation.provider_diagnostics):
        if existing.source == diagnostic.source:
            aggregation.provider_diagnostics[index] = diagnostic
            break
    else:
        aggregation.provider_diagnostics.append(diagnostic)


def _record_linkedin_failure(aggregation: AggregatorFetchResult, message: str) -> None:
    aggregation.failed_sources = list(aggregation.failed_sources)
    if "linkedin" not in aggregation.failed_sources:
        aggregation.failed_sources.append("linkedin")
    aggregation.source_errors["linkedin"] = message


def _merge_linkedin_result(
    jobs: list[dict],
    aggregation: AggregatorFetchResult,
    linkedin_result: SourceFetchResult | BaseException,
) -> tuple[list[dict], dict]:
    """Always merge LinkedIn fetch outcome into aggregation diagnostics."""
    fetch_meta: dict = {"triggered": True}

    if isinstance(linkedin_result, BaseException):
        diagnostic = diagnostic_from_exception("linkedin", linkedin_result)
        _upsert_provider_diagnostic(aggregation, diagnostic)
        _record_linkedin_failure(aggregation, diagnostic.error_message)
        fetch_meta.update(
            {
                "status": "error",
                "message": diagnostic.error_message,
                "diagnostic": diagnostic.model_dump(),
            }
        )
        return jobs, fetch_meta

    if linkedin_result.diagnostic:
        _upsert_provider_diagnostic(aggregation, linkedin_result.diagnostic)

    if linkedin_result.error or (
        linkedin_result.diagnostic and linkedin_result.diagnostic.status != "success"
    ):
        message = linkedin_result.error or (
            linkedin_result.diagnostic.error_message if linkedin_result.diagnostic else ""
        )
        fetch_meta.update(
            {
                "status": (
                    "session_invalid"
                    if linkedin_result.diagnostic
                    and linkedin_result.diagnostic.error_type == "auth_required"
                    else "error"
                ),
                "message": message,
                "diagnostic": (
                    linkedin_result.diagnostic.model_dump()
                    if linkedin_result.diagnostic
                    else {}
                ),
            }
        )
        _record_linkedin_failure(aggregation, message)
        return jobs, fetch_meta

    if not linkedin_result.jobs:
        message = "LinkedIn returned no jobs"
        diagnostic = diagnostic_failure(
            "linkedin",
            error_type="selector_mismatch",
            error_message=message,
        )
        _upsert_provider_diagnostic(aggregation, diagnostic)
        _record_linkedin_failure(aggregation, message)
        fetch_meta.update(
            {
                "status": "empty",
                "message": message,
                "diagnostic": diagnostic.model_dump(),
            }
        )
        return jobs, fetch_meta

    linkedin_pipeline = [job.to_pipeline_dict() for job in linkedin_result.jobs]
    merged = merge_and_dedupe_pipeline_jobs(jobs, linkedin_pipeline)

    aggregation.sources["linkedin"] = len(linkedin_result.jobs)
    aggregation.total_fetched += len(linkedin_result.jobs)
    aggregation.total_after_dedupe = len(merged)

    easy_apply = sum(1 for j in linkedin_result.jobs if j.easy_apply)
    fetch_meta.update(
        {
            "status": "ok",
            "jobs_added": len(linkedin_result.jobs),
            "easy_apply_count": easy_apply,
            "merged_total": len(merged),
            "diagnostic": (
                linkedin_result.diagnostic.model_dump()
                if linkedin_result.diagnostic
                else {}
            ),
        }
    )
    logger.info(
        "[LINKEDIN] Merged into scan added=%d total=%d",
        len(linkedin_result.jobs),
        len(merged),
    )
    return merged, fetch_meta


async def fetch_public_jobs_async() -> PublicJobsFetchResult:
    """
    Fetch all platforms concurrently:
    HTTP/RSS sources (aggregator) + LinkedIn (Playwright session).
    """
    logger.info("[FETCH] Starting full-platform scan (HTTP sources + LinkedIn)")

    async def _fetch_linkedin() -> SourceFetchResult | BaseException:
        try:
            return await asyncio.wait_for(
                LinkedInPlaywrightJobSource().run_fetch(),
                timeout=120.0,
            )
        except asyncio.TimeoutError:
            return TimeoutError("LinkedIn discovery timed out after 120 seconds")
        except Exception as exc:
            return exc

    aggregation_result, linkedin_result = await asyncio.gather(
        aggregate_jobs(),
        _fetch_linkedin(),
        return_exceptions=True,
    )

    if isinstance(aggregation_result, BaseException):
        logger.exception("Job aggregator failed")
        raise JobFetchError("Failed to aggregate jobs from sources") from aggregation_result

    aggregation: AggregatorFetchResult = aggregation_result

    pre_filter_jobs = list(aggregation.jobs)
    pre_filter_jobs, linkedin_meta = _merge_linkedin_result(
        pre_filter_jobs,
        aggregation,
        linkedin_result,
    )

    filtered_jobs, rejected_count = filter_normalized_jobs(pre_filter_jobs)

    logger.info(
        "[FETCH] Pipeline complete aggregated=%d deduped=%d filtered_in=%d rejected=%d "
        "sources=%s failed=%s linkedin=%s",
        aggregation.total_fetched,
        aggregation.total_after_dedupe,
        len(filtered_jobs),
        rejected_count,
        aggregation.sources,
        aggregation.failed_sources,
        linkedin_meta.get("status"),
    )

    return PublicJobsFetchResult(
        jobs=filtered_jobs,
        filtered_rejected=rejected_count,
        aggregation=aggregation,
        pre_filter_jobs=pre_filter_jobs,
        linkedin_fetch=linkedin_meta,
    )


def fetch_public_jobs() -> PublicJobsFetchResult:
    """Sync wrapper for scripts and tests."""
    return asyncio.run(fetch_public_jobs_async())

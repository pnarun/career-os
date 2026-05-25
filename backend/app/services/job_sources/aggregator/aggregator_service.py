import asyncio
import logging

from app.core.circuit_breaker import is_provider_circuit_open, record_provider_failure, record_provider_success
from app.services.job_sources.arbeitnow_source import ArbeitnowJobSource
from app.services.job_sources.base.base_source import BaseJobSource
from app.services.job_sources.base.provider_diagnostics import (
    ProviderFetchDiagnostic,
    diagnostic_failure,
    diagnostic_from_exception,
)
from app.services.job_dedupe_service import dedupe_jobs
from app.services.job_sources.base.source_result import AggregatorFetchResult, NormalizedSourceJob
from app.services.job_sources.indeed_source import IndeedJobSource
from app.services.job_sources.instahyre_source import InstahyreJobSource
from app.services.job_sources.naukri_source import NaukriJobSource
from app.services.job_sources.remoteok_source import RemoteOKJobSource

logger = logging.getLogger(__name__)


def get_registered_sources() -> list[BaseJobSource]:
    """All active source adapters (extend here as new providers are added)."""
    return [
        RemoteOKJobSource(),
        ArbeitnowJobSource(),
        IndeedJobSource(),
        NaukriJobSource(),
        InstahyreJobSource(),
    ]


def _apply_diagnostic(
    diagnostics: list[ProviderFetchDiagnostic],
    failed_sources: list[str],
    source_errors: dict[str, str],
    source_counts: dict[str, int],
    diagnostic: ProviderFetchDiagnostic,
    job_count: int,
) -> None:
    diagnostics.append(diagnostic)
    source_counts[diagnostic.source] = job_count
    if diagnostic.status != "success":
        if diagnostic.source not in failed_sources:
            failed_sources.append(diagnostic.source)
        source_errors[diagnostic.source] = diagnostic.error_message or diagnostic.error_type


async def aggregate_jobs(
    sources: list[BaseJobSource] | None = None,
) -> AggregatorFetchResult:
    """
    Fetch all sources concurrently, isolate failures, merge and deduplicate.
    """
    adapters = sources or get_registered_sources()
    active_adapters: list[BaseJobSource] = []
    skipped_diagnostics: list[ProviderFetchDiagnostic] = []

    for adapter in adapters:
        name = adapter.source_name
        if is_provider_circuit_open(name):
            skipped_diagnostics.append(
                diagnostic_failure(
                    name,
                    error_type="rate_limit",
                    error_message="Provider temporarily disabled (circuit open)",
                )
            )
            logger.warning("[AGGREGATOR_CIRCUIT_OPEN] source=%s", name)
            continue
        active_adapters.append(adapter)

    logger.info("[AGGREGATOR_START] sources=%s", [s.source_name for s in active_adapters])

    results = await asyncio.gather(
        *[adapter.run_fetch() for adapter in active_adapters],
        return_exceptions=True,
    )

    all_jobs: list[NormalizedSourceJob] = []
    source_counts: dict[str, int] = {}
    failed_sources: list[str] = []
    source_errors: dict[str, str] = {}
    provider_diagnostics: list[ProviderFetchDiagnostic] = list(skipped_diagnostics)
    total_fetched = 0

    for skipped in skipped_diagnostics:
        _apply_diagnostic(
            provider_diagnostics,
            failed_sources,
            source_errors,
            source_counts,
            skipped,
            0,
        )
        if skipped.source not in failed_sources:
            failed_sources.append(skipped.source)

    for adapter, result in zip(active_adapters, results):
        name = adapter.source_name

        if isinstance(result, Exception):
            diagnostic = diagnostic_from_exception(name, result)
            record_provider_failure(name)
            _apply_diagnostic(
                provider_diagnostics,
                failed_sources,
                source_errors,
                source_counts,
                diagnostic,
                0,
            )
            logger.warning(
                "[AGGREGATOR_SOURCE_FAILED] source=%s error_type=%s message=%s",
                name,
                diagnostic.error_type,
                diagnostic.error_message,
            )
            continue

        diagnostic = result.diagnostic
        if diagnostic is None:
            from app.services.job_sources.base.provider_diagnostics import finalize_diagnostic

            diagnostic = finalize_diagnostic(
                name,
                jobs=result.jobs,
                duration_ms=result.duration_ms,
                error=result.error,
            )

        count = len(result.jobs)
        total_fetched += count
        all_jobs.extend(result.jobs)
        _apply_diagnostic(
            provider_diagnostics,
            failed_sources,
            source_errors,
            source_counts,
            diagnostic,
            count,
        )

        if diagnostic.status == "success":
            record_provider_success(name)
            logger.info(
                "[AGGREGATOR_SOURCE_OK] source=%s jobs=%d duration_ms=%d",
                name,
                count,
                diagnostic.duration_ms,
            )
        else:
            record_provider_failure(name)
            logger.warning(
                "[AGGREGATOR_SOURCE_FAILED] source=%s status=%s error_type=%s message=%s",
                name,
                diagnostic.status,
                diagnostic.error_type,
                diagnostic.error_message,
            )

    dedupe_result = dedupe_jobs(all_jobs)
    deduped = dedupe_result.jobs
    pipeline_jobs = [job.to_pipeline_dict() for job in deduped]

    logger.info(
        "[AGGREGATOR_COMPLETE] total_fetched=%d after_dedupe=%d duplicates_removed=%d sources=%s failed=%s",
        total_fetched,
        len(deduped),
        dedupe_result.duplicates_removed,
        source_counts,
        failed_sources,
    )

    return AggregatorFetchResult(
        jobs=pipeline_jobs,
        total_fetched=total_fetched,
        total_after_dedupe=len(deduped),
        sources=source_counts,
        failed_sources=failed_sources,
        source_errors=source_errors,
        provider_diagnostics=provider_diagnostics,
    )

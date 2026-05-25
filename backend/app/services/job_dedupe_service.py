"""Deduplication engine for the unified jobs feed."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.job_sources.base.source_result import NormalizedSourceJob

logger = logging.getLogger(__name__)

SOURCE_PRIORITY: dict[str, int] = {
    "linkedin": 100,
    "instahyre": 90,
    "naukri": 80,
    "indeed": 70,
    "remoteok": 60,
    "arbeitnow": 50,
}

DEFAULT_SOURCE_PRIORITY = 10
FUZZY_SIMILARITY_THRESHOLD = 0.82

_DEDUPE_SUFFIXES = re.compile(
    r"\b(inc|llc|ltd|limited|pvt|private|corp|corporation|technologies|technology|tech|labs|solutions|services)\b",
    re.I,
)


def get_source_priority(source: str) -> int:
    key = (source or "").strip().lower().replace(" ", "")
    return SOURCE_PRIORITY.get(key, DEFAULT_SOURCE_PRIORITY)


def _normalize_text(value: str) -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = _DEDUPE_SUFFIXES.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_location(value: str) -> str:
    text = _normalize_text(value)
    for token in ("remote", "hybrid", "onsite", "on site"):
        text = text.replace(token, "")
    return re.sub(r"\s+", " ", text).strip()


def _fuzzy_ratio(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def _job_as_dict(job: Any) -> dict[str, Any]:
    if hasattr(job, "model_dump"):
        return job.model_dump()
    return dict(job)


def _merge_metadata(winner: dict[str, Any], loser: dict[str, Any]) -> dict[str, Any]:
    merged = dict(winner)
    if not merged.get("description") and loser.get("description"):
        merged["description"] = loser["description"]
    if not merged.get("apply_url") and loser.get("apply_url"):
        merged["apply_url"] = loser["apply_url"]
    if not merged.get("posted_at") and loser.get("posted_at"):
        merged["posted_at"] = loser["posted_at"]
    if not merged.get("easy_apply") and loser.get("easy_apply"):
        merged["easy_apply"] = loser["easy_apply"]
    loser_tags = list(loser.get("tags") or [])
    winner_tags = list(merged.get("tags") or [])
    for tag in loser_tags:
        if tag not in winner_tags:
            winner_tags.append(tag)
    merged["tags"] = winner_tags
    return merged


@dataclass
class DedupeResult:
    jobs: list[Any]
    duplicates_removed: int = 0
    dedupe_reasons: list[dict[str, str]] = field(default_factory=list)


def dedupe_jobs(jobs: list[Any]) -> DedupeResult:
    """
    Deduplicate jobs by URL, normalized title+company+location, and fuzzy similarity.
    Keeps the highest source_priority entry and merges useful metadata.
    """
    raw_jobs = [_job_as_dict(job) for job in jobs]
    kept: list[dict[str, Any]] = []
    reasons: list[dict[str, str]] = []

    seen_urls: set[str] = set()
    seen_source_ids: set[tuple[str, str]] = set()
    seen_triples: set[tuple[str, str, str]] = set()

    for candidate in raw_jobs:
        url_key = (candidate.get("apply_url") or "").strip().lower()
        title_key = _normalize_text(candidate.get("title", ""))
        company_key = _normalize_text(candidate.get("company", ""))
        location_key = _normalize_location(candidate.get("location", ""))
        source_key = (
            (candidate.get("source") or "").strip().lower(),
            (candidate.get("source_job_id") or "").strip().lower(),
        )
        triple_key = (title_key, company_key, location_key)
        candidate_priority = get_source_priority(candidate.get("source", ""))

        duplicate_index: int | None = None
        dedupe_reason = ""

        if url_key and url_key in seen_urls:
            for index, existing in enumerate(kept):
                if (existing.get("apply_url") or "").strip().lower() == url_key:
                    duplicate_index = index
                    dedupe_reason = "exact_url"
                    break

        if duplicate_index is None and source_key[1] and source_key in seen_source_ids:
            for index, existing in enumerate(kept):
                existing_source = (
                    (existing.get("source") or "").strip().lower(),
                    (existing.get("source_job_id") or "").strip().lower(),
                )
                if existing_source == source_key:
                    duplicate_index = index
                    dedupe_reason = "source_job_id"
                    break

        if duplicate_index is None and title_key and company_key and triple_key in seen_triples:
            for index, existing in enumerate(kept):
                existing_triple = (
                    _normalize_text(existing.get("title", "")),
                    _normalize_text(existing.get("company", "")),
                    _normalize_location(existing.get("location", "")),
                )
                if existing_triple == triple_key:
                    duplicate_index = index
                    dedupe_reason = "normalized_title_company_location"
                    break

        if duplicate_index is None and title_key and company_key:
            for index, existing in enumerate(kept):
                existing_title = _normalize_text(existing.get("title", ""))
                existing_company = _normalize_text(existing.get("company", ""))
                title_sim = _fuzzy_ratio(title_key, existing_title)
                company_sim = _fuzzy_ratio(company_key, existing_company)
                if title_sim >= FUZZY_SIMILARITY_THRESHOLD and company_sim >= FUZZY_SIMILARITY_THRESHOLD:
                    duplicate_index = index
                    dedupe_reason = "fuzzy_company_role"
                    break

        if duplicate_index is None:
            kept.append(candidate)
            if url_key:
                seen_urls.add(url_key)
            if source_key[1]:
                seen_source_ids.add(source_key)
            if title_key and company_key:
                seen_triples.add(triple_key)
            continue

        existing = kept[duplicate_index]
        existing_priority = get_source_priority(existing.get("source", ""))

        if candidate_priority > existing_priority:
            merged = _merge_metadata(candidate, existing)
            kept[duplicate_index] = merged
            discarded_source = existing.get("source", "")
            kept_source = candidate.get("source", "")
        else:
            merged = _merge_metadata(existing, candidate)
            kept[duplicate_index] = merged
            discarded_source = candidate.get("source", "")
            kept_source = existing.get("source", "")

        reasons.append(
            {
                "dedupe_reason": dedupe_reason,
                "kept_source": str(kept_source),
                "discarded_source": str(discarded_source),
                "title": candidate.get("title", ""),
                "company": candidate.get("company", ""),
            }
        )

    from app.services.job_sources.base.source_result import NormalizedSourceJob

    normalized: list[NormalizedSourceJob] = []
    for job in kept:
        try:
            normalized.append(NormalizedSourceJob(**job))
        except Exception:
            continue

    duplicates_removed = len(raw_jobs) - len(normalized)
    if duplicates_removed:
        logger.info(
            "[DEDUPE] removed=%d kept=%d reasons_sample=%s",
            duplicates_removed,
            len(normalized),
            reasons[:3],
        )

    return DedupeResult(
        jobs=normalized,
        duplicates_removed=duplicates_removed,
        dedupe_reasons=reasons,
    )


def dedupe_pipeline_dicts(jobs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Dedupe legacy pipeline dicts; returns (jobs, duplicates_removed)."""
    result = dedupe_jobs(jobs)
    return [job.to_pipeline_dict() for job in result.jobs], result.duplicates_removed

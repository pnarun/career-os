import asyncio
import logging
import re
from html import unescape
from typing import Any, TypedDict

import requests

from app.services.job_filter_service import filter_normalized_jobs
from app.services.job_quality_service import is_valid_apply_url

logger = logging.getLogger(__name__)

REMOTEOK_API_URL = "https://remoteok.com/api"
ARBEITNOW_API_URL = "https://arbeitnow.com/api/job-board-api"
REQUEST_TIMEOUT = 25
REQUEST_HEADERS = {
    "User-Agent": "CareerOS/1.0 (job-discovery; +https://github.com/career-os)",
    "Accept": "application/json",
}


class JobFetchError(Exception):
    """Raised when fetching jobs from external APIs fails."""


class NormalizedJob(TypedDict):
    title: str
    company: str
    location: str
    apply_url: str
    source: str
    description: str
    easy_apply: bool
    job_type: str
    tags: list[str]
    remote_priority: bool
    india_focused: bool


def _strip_html(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    return unescape(re.sub(r"\s+", " ", cleaned)).strip()


def _normalize_apply_url(url: str, source: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("/") and source == "remoteok":
        return f"https://remoteok.com{url}"
    return url


def _parse_tags(raw_tags: Any) -> list[str]:
    if isinstance(raw_tags, list):
        return [str(tag) for tag in raw_tags if tag]
    if raw_tags:
        return [str(raw_tags)]
    return []


def _parse_remoteok_jobs(payload: list[dict[str, Any]]) -> list[NormalizedJob]:
    jobs: list[NormalizedJob] = []

    for item in payload:
        if not isinstance(item, dict):
            continue
        if "position" not in item and "company" not in item:
            continue

        title = (item.get("position") or item.get("title") or "").strip()
        company = (item.get("company") or "").strip()
        if not title or not company:
            continue

        tags = _parse_tags(item.get("tags"))
        description = _strip_html(item.get("description") or "")
        location = (item.get("location") or "Remote").strip()
        apply_url = _normalize_apply_url(
            item.get("url") or item.get("apply_url") or "",
            "remoteok",
        )
        if not apply_url:
            continue

        jobs.append(
            NormalizedJob(
                title=title,
                company=company,
                location=location,
                apply_url=apply_url,
                source="remoteok",
                description=description,
                easy_apply=False,
                job_type="remote",
                tags=tags,
                remote_priority=False,
                india_focused=False,
            )
        )

    return jobs


def _parse_arbeitnow_jobs(payload: dict[str, Any]) -> list[NormalizedJob]:
    jobs: list[NormalizedJob] = []
    items = payload.get("data") or []

    for item in items:
        if not isinstance(item, dict):
            continue

        title = (item.get("title") or "").strip()
        company = (item.get("company_name") or item.get("company") or "").strip()
        if not title or not company:
            continue

        tags = _parse_tags(item.get("tags"))
        description = _strip_html(item.get("description") or "")
        location = (item.get("location") or "Remote").strip()
        apply_url = _normalize_apply_url(item.get("url") or "", "arbeitnow")
        if not apply_url or not is_valid_apply_url(apply_url):
            continue

        job_types = item.get("job_types") or []
        job_type = ", ".join(job_types) if isinstance(job_types, list) else str(job_types)
        if item.get("remote"):
            job_type = f"remote{', ' + job_type if job_type else ''}".strip(", ")

        jobs.append(
            NormalizedJob(
                title=title,
                company=company,
                location=location,
                apply_url=apply_url,
                source="arbeitnow",
                description=description,
                easy_apply=False,
                job_type=job_type or "unknown",
                tags=tags,
                remote_priority=False,
                india_focused=False,
            )
        )

    return jobs


def _fetch_remoteok_jobs() -> list[NormalizedJob]:
    try:
        response = requests.get(
            REMOTEOK_API_URL,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            logger.warning("RemoteOK returned unexpected payload type")
            return []
        return _parse_remoteok_jobs(payload)
    except requests.RequestException as exc:
        logger.exception("RemoteOK fetch failed")
        raise JobFetchError("Failed to fetch jobs from RemoteOK") from exc


def _fetch_arbeitnow_jobs() -> list[NormalizedJob]:
    try:
        response = requests.get(
            ARBEITNOW_API_URL,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            logger.warning("Arbeitnow returned unexpected payload type")
            return []
        return _parse_arbeitnow_jobs(payload)
    except requests.RequestException as exc:
        logger.warning("Arbeitnow fetch failed, continuing with other sources: %s", exc)
        return []


def _dedupe_normalized_jobs(jobs: list[dict]) -> list[dict]:
    """Deduplicate within a single fetch batch by apply_url or title+company."""
    seen_urls: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    unique: list[dict] = []

    for job in jobs:
        url_key = job["apply_url"].strip().lower()
        pair_key = (job["title"].strip().lower(), job["company"].strip().lower())

        if url_key and url_key in seen_urls:
            continue
        if pair_key in seen_pairs:
            continue

        if url_key:
            seen_urls.add(url_key)
        seen_pairs.add(pair_key)
        unique.append(job)

    return unique


def fetch_public_jobs() -> tuple[list[dict], int]:
    """
    Fetch, normalize, and filter jobs from active public APIs.
    Quality scoring runs after matching in job_service (post-filter pipeline).
    """
    remoteok_jobs = _fetch_remoteok_jobs()
    arbeitnow_jobs = _fetch_arbeitnow_jobs()
    combined = remoteok_jobs + arbeitnow_jobs
    deduped = _dedupe_normalized_jobs(combined)
    filtered, rejected_count = filter_normalized_jobs(deduped)

    logger.info(
        "Fetched jobs: remoteok=%d arbeitnow=%d deduped=%d accepted=%d rejected=%d",
        len(remoteok_jobs),
        len(arbeitnow_jobs),
        len(deduped),
        len(filtered),
        rejected_count,
    )
    return filtered, rejected_count


async def fetch_public_jobs_async() -> tuple[list[dict], int]:
    """Async wrapper for public job fetching."""
    return await asyncio.to_thread(fetch_public_jobs)

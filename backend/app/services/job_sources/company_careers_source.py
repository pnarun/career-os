"""
Fetch jobs for target companies via Indeed India company-focused search.

Results are tagged with company_tag and source careers:{slug} for feed filtering.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.services.job_filter_service import enrich_job_filter_metadata
from app.services.job_sources.base.source_result import SourceFetchResult
from app.services.job_sources.indeed_source import IndeedJobSource

logger = logging.getLogger(__name__)

COMPANY_SEARCH: dict[str, dict[str, str]] = {
    "amazon": {"label": "Amazon", "query": "Amazon"},
    "flipkart": {"label": "Flipkart", "query": "Flipkart"},
    "google": {"label": "Google", "query": "Google"},
    "microsoft": {"label": "Microsoft", "query": "Microsoft"},
    "infosys": {"label": "Infosys", "query": "Infosys"},
    "tcs": {"label": "TCS", "query": "TCS"},
    "wipro": {"label": "Wipro", "query": "Wipro"},
    "accenture": {"label": "Accenture", "query": "Accenture"},
    "phonepe": {"label": "PhonePe", "query": "PhonePe"},
    "razorpay": {"label": "Razorpay", "query": "Razorpay"},
    "swiggy": {"label": "Swiggy", "query": "Swiggy"},
    "zomato": {"label": "Zomato", "query": "Zomato"},
    "freshworks": {"label": "Freshworks", "query": "Freshworks"},
    "adobe": {"label": "Adobe", "query": "Adobe"},
    "uber": {"label": "Uber", "query": "Uber"},
    "myntra": {"label": "Myntra", "query": "Myntra"},
}


def _slug(company: str) -> str:
    return "".join(ch for ch in company.lower() if ch.isalnum())


def _company_matches(job_company: str, job_title: str, label: str, slug: str) -> bool:
    company_lower = job_company.lower()
    title_lower = job_title.lower()
    label_lower = label.lower()
    if label_lower in company_lower or label_lower in title_lower:
        return True
    return slug in company_lower.replace(" ", "")


async def fetch_company_portal_jobs(
    company: str,
    *,
    role: str = "software engineer",
    location: str = "India",
) -> list[dict[str, Any]]:
    slug = _slug(company)
    meta = COMPANY_SEARCH.get(slug, {"label": company.strip(), "query": company.strip()})
    label = meta["label"]
    query = f"{meta['query']} {role}".strip()
    source_key = f"careers:{slug or 'company'}"

    logger.info("[COMPANY_CAREERS] Fetch company=%s query=%s", label, query)

    indeed = IndeedJobSource(role=query, location=location, remote=False)
    result: SourceFetchResult = await indeed.fetch_jobs()

    pipeline_jobs: list[dict[str, Any]] = []
    for job in result.jobs:
        if not _company_matches(job.company, job.title, label, slug):
            continue
        pipeline = job.to_pipeline_dict()
        pipeline["source"] = source_key
        pipeline["company_tag"] = label
        pipeline["metadata"] = {
            **(pipeline.get("metadata") or {}),
            "company_portal": label,
            "search_query": query,
        }
        pipeline_jobs.append(enrich_job_filter_metadata(pipeline))

    logger.info("[COMPANY_CAREERS] company=%s matched=%d", label, len(pipeline_jobs))
    return pipeline_jobs


async def fetch_all_target_company_jobs(
    companies: list[str],
    *,
    roles: list[str] | None = None,
    location: str = "India",
) -> list[dict[str, Any]]:
    if not companies:
        return []

    primary_role = (roles or ["software engineer"])[0] if roles else "software engineer"
    unique: list[str] = []
    seen: set[str] = set()
    for c in companies:
        key = _slug(c)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(c.strip())
        if len(unique) >= 5:
            break

    tasks = [
        fetch_company_portal_jobs(company, role=primary_role, location=location)
        for company in unique
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged: list[dict[str, Any]] = []
    for company, result in zip(unique, results):
        if isinstance(result, Exception):
            logger.warning("[COMPANY_CAREERS] Failed company=%s: %s", company, result)
            continue
        merged.extend(result)
    return merged

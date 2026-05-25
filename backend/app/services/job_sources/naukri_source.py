"""Naukri job source — public v2 search API (key + location)."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, quote_plus

from app.services.job_quality_service import is_valid_apply_url
from app.services.job_sources.base.base_source import BaseJobSource
from app.services.job_sources.base.http_client import fetch_http
from app.services.job_sources.base.provider_diagnostics import (
    ProviderFetchLogger,
    classify_message,
    diagnostic_failure,
    merge_http_status_message,
)
from app.services.job_sources.base.source_result import RawSourceJob, SourceFetchResult

DEFAULT_ROLE = "software engineer"
DEFAULT_LOCATION = "india"

_NAUKRI_HEADERS = {
    "Accept": "application/json",
    "appid": "109",
    "systemid": "109",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s-]", "", value.lower())
    return re.sub(r"\s+", "-", cleaned.strip())


def build_naukri_search_url(
    role: str = DEFAULT_ROLE,
    location: str = DEFAULT_LOCATION,
    *,
    remote: bool = False,
) -> str:
    """
    Official Naukri SEO search URL.

    Example: https://www.naukri.com/software-engineer-jobs-in-india
    """
    keyword = f"{role} remote" if remote else role
    slug_keyword = _slugify(keyword)
    slug_location = _slugify(location)
    return f"https://www.naukri.com/{slug_keyword}-jobs-in-{slug_location}"


def build_naukri_api_url(
    role: str = DEFAULT_ROLE,
    location: str = DEFAULT_LOCATION,
    *,
    remote: bool = False,
) -> str:
    """
    Naukri jobapi v2 search — requires search_by_key_loc when keyword and location are set.

    v3 returns 406 (recaptcha); v2 works without nkparam for public search.
    """
    keyword = f"{role} remote" if remote else role
    encoded_keyword = quote(keyword)
    encoded_location = quote(location.lower())
    return (
        "https://www.naukri.com/jobapi/v2/search"
        f"?noOfResults=25&pageNo=1&urlType=search_by_key_loc&searchType=adv"
        f"&keyword={encoded_keyword}&location={encoded_location}"
    )


def _log_search_context(
    log: ProviderFetchLogger,
    *,
    role: str,
    location: str,
    remote: bool,
    encoded_query: str,
    encoded_location: str,
    search_url: str,
    fetch_url: str,
) -> None:
    log.step(
        "Search context "
        f"role={role!r} location={location!r} remote={remote} "
        f"encoded_query={encoded_query!r} encoded_location={encoded_location!r}"
    )
    log.step(f"Final search URL (web): {search_url}")
    log.step(f"Final fetch URL (api): {fetch_url}")


class NaukriJobSource(BaseJobSource):
    """HTTP Naukri job API adapter."""

    source_name = "naukri"

    def __init__(
        self,
        *,
        role: str = DEFAULT_ROLE,
        location: str = DEFAULT_LOCATION,
        remote: bool = False,
    ) -> None:
        self.role = role.strip() or DEFAULT_ROLE
        self.location = location.strip() or DEFAULT_LOCATION
        self.remote = remote

    async def fetch_jobs(self) -> SourceFetchResult:
        log = ProviderFetchLogger(self.source_name)

        keyword = f"{self.role} remote" if self.remote else self.role
        encoded_query = quote_plus(keyword)
        encoded_location = quote_plus(self.location.lower())
        search_url = build_naukri_search_url(
            self.role, self.location, remote=self.remote
        )
        fetch_url = build_naukri_api_url(
            self.role, self.location, remote=self.remote
        )
        _log_search_context(
            log,
            role=self.role,
            location=self.location,
            remote=self.remote,
            encoded_query=encoded_query,
            encoded_location=encoded_location,
            search_url=search_url,
            fetch_url=fetch_url,
        )

        try:
            response = await fetch_http(
                fetch_url,
                headers={
                    **_NAUKRI_HEADERS,
                    "Referer": search_url,
                },
                timeout=25,
                max_retries=1,
            )
        except Exception as exc:
            raise RuntimeError(f"Naukri API request failed: {exc}") from exc

        log.step(f"API response HTTP {response.status_code}")

        if response.status_code != 200:
            message = merge_http_status_message(
                response.status_code,
                "Naukri job API requires login cookies or recaptcha for this endpoint",
            )
            error_type, requires_auth, session_valid = classify_message(
                message, http_status=response.status_code
            )
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type=error_type,
                error_message=message,
                requires_auth=requires_auth or response.status_code in (401, 403, 406),
                session_valid=session_valid,
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=message,
                diagnostic=diagnostic,
            )

        try:
            payload = response.json()
        except ValueError as exc:
            message = f"Naukri API returned non-JSON body: {exc}"
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="parsing_failure",
                error_message=message,
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=message,
                diagnostic=diagnostic,
            )

        listings = self._iter_job_listings(payload)
        log.step(f"JSON payload listings={len(listings)}")

        normalized = []
        for item in listings:
            raw = self._item_to_raw(item)
            if not raw.apply_url or not is_valid_apply_url(raw.apply_url):
                continue
            job = self.normalize_job(raw)
            if job:
                normalized.append(job)

        log.parsed(len(normalized), raw_count=len(listings))

        if not listings:
            message = "Naukri API JSON has no job list (schema mismatch or empty search)"
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="selector_mismatch",
                error_message=message,
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=message,
                diagnostic=diagnostic,
            )

        if not normalized:
            message = (
                f"Naukri returned {len(listings)} listings but none had valid apply URLs"
            )
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="parsing_failure",
                error_message=message,
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=message,
                diagnostic=diagnostic,
            )

        return SourceFetchResult(source=self.source_name, jobs=normalized)

    def _iter_job_listings(self, payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            return []
        jobs = (
            payload.get("list")
            or payload.get("jobDetails")
            or payload.get("jobs")
            or []
        )
        if isinstance(jobs, dict):
            return list(jobs.values()) if jobs else []
        if isinstance(jobs, list):
            return [j for j in jobs if isinstance(j, dict)]
        return []

    def _item_to_raw(self, item: dict[str, Any]) -> RawSourceJob:
        title = (
            item.get("post")
            or item.get("title")
            or item.get("designation")
            or item.get("jobTitle")
            or ""
        ).strip()
        company = (
            item.get("companyName")
            or item.get("company")
            or item.get("companyDetail", {}).get("name")
            or item.get("CONTCOM")
            or ""
        )
        if isinstance(company, dict):
            company = company.get("name", "")
        company = str(company).strip()

        location_parts = item.get("placeholders") or item.get("locations") or []
        location = self.location.title()
        if isinstance(location_parts, list) and location_parts:
            location = ", ".join(str(p) for p in location_parts[:3])
        elif item.get("location"):
            location = str(item.get("location"))
        elif item.get("cityfield"):
            location = " ".join(str(item.get("cityfield")).split())

        job_id = str(item.get("jobId") or item.get("jdId") or item.get("id") or "")
        apply_url = (
            item.get("urlStr")
            or item.get("jdURL")
            or item.get("applyUrl")
            or item.get("staticUrl")
            or ""
        )
        if apply_url and not str(apply_url).startswith("http"):
            apply_url = f"https://www.naukri.com{apply_url}"

        description = item.get("jobDesc") or item.get("jobDescription") or item.get("description") or ""

        return RawSourceJob(
            source=self.source_name,
            source_job_id=job_id or self.build_job_hash(title, company, str(apply_url)),
            title=title,
            company=company,
            location=location,
            remote=self.remote
            or "remote" in title.lower()
            or "wfh" in title.lower()
            or item.get("wfhType") is not None,
            apply_url=str(apply_url).strip(),
            description=str(description),
            posted_at=str(item.get("addDate") or item.get("createdDate") or item.get("footer") or ""),
            metadata={
                "provider": "naukri_jobapi_v2",
                "search_url": build_naukri_search_url(
                    self.role, self.location, remote=self.remote
                ),
            },
            raw_payload=item,
        )

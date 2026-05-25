"""Instahyre job source — public search page + /api/v1/job_search."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus, urlencode

from app.services.job_quality_service import is_valid_apply_url
from app.services.job_sources.base.base_source import BaseJobSource
from app.services.job_sources.base.http_client import fetch_http
from app.services.job_sources.base.provider_diagnostics import (
    ProviderFetchLogger,
    diagnostic_failure,
)
from app.services.job_sources.base.source_result import RawSourceJob, SourceFetchResult

DEFAULT_ROLE = "software engineer"
DEFAULT_LOCATION = "India"

_INSTAHYRE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def build_instahyre_search_url(
    role: str = DEFAULT_ROLE,
    location: str = DEFAULT_LOCATION,
    *,
    remote: bool = False,
) -> str:
    """
    Official Instahyre search URL (parseUrl reads skills + location, not q/loc).

    Example: https://www.instahyre.com/search-jobs/?skills=software+engineer&location=India
    """
    effective_location = "Work From Home" if remote else location
    query = urlencode(
        {"skills": role, "location": effective_location},
        quote_via=quote_plus,
    )
    return f"https://www.instahyre.com/search-jobs/?{query}"


def build_instahyre_api_url(
    role: str = DEFAULT_ROLE,
    location: str = DEFAULT_LOCATION,
    *,
    remote: bool = False,
    offset: int = 0,
) -> str:
    """Public JSON endpoint used by the search-jobs Angular page."""
    effective_location = "Work From Home" if remote else location
    query = urlencode(
        {
            "skills": role,
            "location": effective_location,
            "source": "opportunities",
            "offset": str(offset),
        },
        quote_via=quote_plus,
    )
    return f"https://www.instahyre.com/api/v1/job_search?{query}"


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


class InstahyreJobSource(BaseJobSource):
    """Instahyre public job search via /api/v1/job_search."""

    source_name = "instahyre"

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

        effective_location = "Work From Home" if self.remote else self.location
        encoded_query = quote_plus(self.role)
        encoded_location = quote_plus(effective_location)
        search_url = build_instahyre_search_url(
            self.role, self.location, remote=self.remote
        )
        fetch_url = build_instahyre_api_url(
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
                headers={**_INSTAHYRE_HEADERS, "Referer": search_url},
                timeout=20,
                max_retries=1,
            )
        except Exception as exc:
            raise RuntimeError(f"Instahyre API request failed: {exc}") from exc

        log.step(f"API response HTTP {response.status_code}")

        if response.status_code != 200:
            message = f"Instahyre job_search API returned HTTP {response.status_code}"
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="network_failure",
                error_message=message,
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
            message = f"Instahyre API returned non-JSON body: {exc}"
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

        listings = payload.get("objects") if isinstance(payload, dict) else []
        if not isinstance(listings, list):
            listings = []
        log.step(f"JSON payload listings={len(listings)}")

        normalized = []
        for item in listings:
            if not isinstance(item, dict):
                continue
            raw = self._item_to_raw(item)
            if not raw.apply_url or not is_valid_apply_url(raw.apply_url):
                continue
            job = self.normalize_job(raw)
            if job:
                normalized.append(job)

        log.parsed(len(normalized), raw_count=len(listings))

        if not listings:
            message = "Instahyre job_search API returned no job objects"
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
                f"Instahyre returned {len(listings)} listings but none had valid apply URLs"
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

    def _item_to_raw(self, item: dict[str, Any]) -> RawSourceJob:
        title = str(item.get("title") or item.get("candidate_title") or "").strip()
        employer = item.get("employer") or {}
        company = ""
        if isinstance(employer, dict):
            company = str(employer.get("company_name") or "").strip()

        location = str(item.get("locations") or self.location).strip()
        apply_url = str(item.get("public_url") or "").strip()
        if apply_url and not apply_url.startswith("http"):
            apply_url = f"https://www.instahyre.com{apply_url}"

        job_id = str(item.get("id") or "")

        return RawSourceJob(
            source=self.source_name,
            source_job_id=job_id or self.build_job_hash(title, company, apply_url),
            title=title,
            company=company or "Unknown Company",
            location=location or self.location,
            remote=self.remote
            or "remote" in title.lower()
            or "work from home" in location.lower(),
            apply_url=apply_url,
            description="",
            posted_at="",
            metadata={
                "parser": "job_search_api",
                "search_url": build_instahyre_search_url(
                    self.role, self.location, remote=self.remote
                ),
            },
            raw_payload=item,
        )

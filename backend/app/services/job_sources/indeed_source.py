"""Indeed job source — India search page (HTML) with optional saved session cookies."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any
from urllib.parse import quote_plus

from app.services.job_quality_service import is_valid_apply_url
from app.services.job_sources.base.base_source import BaseJobSource
from app.services.job_sources.base.provider_diagnostics import (
    ProviderFetchLogger,
    diagnostic_failure,
)
from app.services.job_sources.base.source_result import RawSourceJob, SourceFetchResult

DEFAULT_ROLE = "software engineer"
DEFAULT_LOCATION = "India"

_INDEED_IMPERSONATE = "chrome120"
_JOB_CARD_PATTERN = re.compile(
    r'"jobKey":"(?P<job_key>[a-f0-9]+)"'
    r'.*?"jobTitle":"(?P<title>(?:\\.|[^"\\])*)"'
    r'.*?"subtitle":"(?P<subtitle>(?:\\.|[^"\\])*)"',
    re.DOTALL,
)


def build_indeed_search_url(
    role: str = DEFAULT_ROLE,
    location: str = DEFAULT_LOCATION,
    *,
    remote: bool = False,
) -> str:
    """Official Indeed India web search URL."""
    query = f"{role} remote" if remote else role
    encoded_query = quote_plus(query)
    encoded_location = quote_plus(location)
    url = f"https://in.indeed.com/jobs?q={encoded_query}&l={encoded_location}"
    if remote:
        url += "&remotejob=1"
    return url


def _log_search_context(
    log: ProviderFetchLogger,
    *,
    role: str,
    location: str,
    remote: bool,
    encoded_query: str,
    encoded_location: str,
    search_url: str,
) -> None:
    log.step(
        "Search context "
        f"role={role!r} location={location!r} remote={remote} "
        f"encoded_query={encoded_query!r} encoded_location={encoded_location!r}"
    )
    log.step(f"Final search URL: {search_url}")


def _load_indeed_cookies() -> dict[str, str]:
    try:
        from app.automation.browser.session_manager import load_session

        storage = load_session("indeed") or {}
    except Exception:
        return {}

    cookies: dict[str, str] = {}
    for item in storage.get("cookies") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        value = str(item.get("value") or "")
        if name:
            cookies[name] = value
    return cookies


def _decode_json_string(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value.replace("\\u002F", "/").replace('\\"', '"')


def _fetch_indeed_html(url: str, cookies: dict[str, str]) -> tuple[int, str]:
    from curl_cffi import requests as curl_requests

    response = curl_requests.get(
        url,
        impersonate=_INDEED_IMPERSONATE,
        cookies=cookies or None,
        timeout=30,
        headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    return response.status_code, response.text or ""


def _parse_search_html(html: str, *, search_url: str, location: str, remote: bool) -> list[RawSourceJob]:
    if not html.strip():
        return []

    if "Security Check" in html[:2000] or "security check" in html[:2000].lower():
        return []

    seen_keys: set[str] = set()
    jobs: list[RawSourceJob] = []

    for match in _JOB_CARD_PATTERN.finditer(html):
        job_key = match.group("job_key")
        if job_key in seen_keys:
            continue
        seen_keys.add(job_key)

        title = _decode_json_string(match.group("title")).strip()
        subtitle = _decode_json_string(match.group("subtitle")).strip()
        if not title:
            continue

        company = "Unknown Company"
        job_location = location
        if " - " in subtitle:
            company, _, loc_part = subtitle.partition(" - ")
            company = company.strip() or company
            job_location = loc_part.strip() or location
        elif subtitle:
            company = subtitle.strip()

        apply_url = f"https://in.indeed.com/viewjob?jk={job_key}"
        jobs.append(
            RawSourceJob(
                source="indeed",
                source_job_id=job_key,
                title=title,
                company=company,
                location=job_location,
                remote=remote or "remote" in title.lower() or "remote" in subtitle.lower(),
                apply_url=apply_url,
                description="",
                posted_at="",
                metadata={"parser": "indeed_html", "search_url": search_url},
                raw_payload={"job_key": job_key, "subtitle": subtitle},
            )
        )

    if jobs:
        return jobs

    # Fallback: pair job keys with nearby titles when card JSON layout shifts.
    keys = re.findall(r'"jobKey":"([a-f0-9]+)"', html)
    titles = [_decode_json_string(t) for t in re.findall(r'"jobTitle":"((?:\\.|[^"\\])*)"', html)]
    subtitles = [_decode_json_string(s) for s in re.findall(r'"subtitle":"((?:\\.|[^"\\])*)"', html)]

    for job_key, title, subtitle in zip(keys, titles, subtitles):
        if job_key in seen_keys or not title.strip():
            continue
        seen_keys.add(job_key)
        company = subtitle.split(" - ")[0].strip() if subtitle else "Unknown Company"
        job_location = subtitle.split(" - ", 1)[1].strip() if " - " in subtitle else location
        jobs.append(
            RawSourceJob(
                source="indeed",
                source_job_id=job_key,
                title=title.strip(),
                company=company or "Unknown Company",
                location=job_location or location,
                remote=remote,
                apply_url=f"https://in.indeed.com/viewjob?jk={job_key}",
                description="",
                posted_at="",
                metadata={"parser": "indeed_html_fallback", "search_url": search_url},
                raw_payload={"job_key": job_key, "subtitle": subtitle},
            )
        )

    return jobs


class IndeedJobSource(BaseJobSource):
    """Indeed India integration via search results HTML."""

    source_name = "indeed"

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

        query = f"{self.role} remote" if self.remote else self.role
        encoded_query = quote_plus(query)
        encoded_location = quote_plus(self.location)
        search_url = build_indeed_search_url(
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
        )

        cookies = _load_indeed_cookies()
        if cookies:
            log.step(f"Using saved Indeed session cookies count={len(cookies)}")

        try:
            status_code, html = await asyncio.to_thread(
                _fetch_indeed_html, search_url, cookies
            )
        except ImportError:
            message = (
                "Indeed fetch requires curl_cffi (install curl_cffi in backend requirements)"
            )
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
        except Exception as exc:
            raise RuntimeError(f"Indeed search request failed: {exc}") from exc

        log.step(f"Search page HTTP {status_code} bytes={len(html)}")

        if status_code != 200:
            message = (
                f"Indeed search returned HTTP {status_code}. "
                "Refresh the Indeed session on the Automation page or retry later."
            )
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="rate_limit" if status_code == 403 else "network_failure",
                error_message=message,
                requires_auth=status_code in (401, 403),
                session_valid=False if status_code == 403 and cookies else None,
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=message,
                diagnostic=diagnostic,
            )

        raw_jobs = _parse_search_html(
            html,
            search_url=search_url,
            location=self.location,
            remote=self.remote,
        )
        log.parsed(len(raw_jobs), raw_count=len(raw_jobs))

        normalized = []
        for raw in raw_jobs:
            if not raw.apply_url or not is_valid_apply_url(raw.apply_url):
                continue
            job = self.normalize_job(raw)
            if job:
                normalized.append(job)

        if not raw_jobs:
            blocked = "Security Check" in html[:3000]
            message = (
                "Indeed returned a bot/security challenge page — refresh Indeed session "
                "via Automation and retry"
                if blocked
                else "Indeed search page had no parseable job cards"
            )
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="rate_limit" if blocked else "selector_mismatch",
                error_message=message,
                requires_auth=blocked,
                session_valid=False if blocked else None,
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=message,
                diagnostic=diagnostic,
            )

        if not normalized:
            message = (
                f"Indeed parsed {len(raw_jobs)} cards but none had valid apply URLs"
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

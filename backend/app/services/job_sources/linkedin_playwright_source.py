"""
LinkedIn job discovery via saved Playwright session (read-only).

No auto-apply, login automation, captcha bypass, or scroll/pagination loops.
"""

from __future__ import annotations

import logging
import random
import re
import time
from typing import Any
from urllib.parse import quote_plus, urljoin

from app.automation.browser.screenshot_service import (
    capture_error_state_sync,
    capture_page_sync,
    screenshot_relative_path,
)
from app.automation.browser.session_status_service import is_session_ready
from app.automation.browser.sync_runner import (
    close_browser_sync,
    create_context_sync,
)
from app.automation.browser.session_status_service import is_session_ready
from app.services.job_quality_service import is_valid_apply_url
from app.services.job_sources.base.provider_diagnostics import (
    ProviderFetchLogger,
    diagnostic_failure,
)
from app.services.job_sources.linkedin_search_context import (
    DEFAULT_KEYWORDS,
    DEFAULT_LOCATION,
    resolve_linkedin_discovery_payload,
)
from app.services.job_sources.base.base_source import BaseJobSource
from app.services.job_sources.base.source_result import (
    NormalizedSourceJob,
    RawSourceJob,
    SourceFetchResult,
)

logger = logging.getLogger(__name__)

PLATFORM = "linkedin"
SOURCE_NAME = "linkedin"
LINKEDIN_JOBS_HOME = "https://www.linkedin.com/jobs/"

LOCATION_FILTERS = (
    "India",
    "Remote",
    "Hybrid",
    "Bengaluru",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Bangalore",
)

MAX_VISIBLE_CARDS = 25
MIN_CARDS_TARGET = 20

JOB_CARD_SELECTORS = (
    "li.jobs-search-results__list-item",
    "div.job-card-container",
    "ul.scaffold-layout__list-container > li",
    "div[data-job-id]",
)

CAPTCHA_HINTS = (
    "captcha",
    "security verification",
    "let's do a quick security check",
    "unusual activity",
)


def _build_search_url(keywords: list[str], location: str = DEFAULT_LOCATION) -> str:
    terms = [k.strip() for k in keywords if k and k.strip()] or list(DEFAULT_KEYWORDS)
    keyword_query = " OR ".join(f'"{k}"' if " " in k else k for k in terms)
    return (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={quote_plus(keyword_query)}"
        f"&location={quote_plus(location or DEFAULT_LOCATION)}"
        "&f_WT=2"
    )


def _human_delay(min_ms: float = 400, max_ms: float = 900) -> None:
    time.sleep(random.uniform(min_ms, max_ms) / 1000.0)


def _detect_session_invalid(page) -> str | None:
    url = (page.url or "").lower()
    if any(token in url for token in ("/login", "uas/login", "checkpoint")):
        return "LinkedIn session expired or login required."

    try:
        if page.locator('input[name="session_key"]').count() > 0:
            return "LinkedIn session expired or login required."
    except Exception:
        pass

    try:
        body_text = (page.locator("body").inner_text(timeout=5000) or "").lower()
    except Exception:
        body_text = ""

    for hint in CAPTCHA_HINTS:
        if hint in body_text:
            return "LinkedIn security check detected. Session cannot proceed."

    if "sign in" in body_text and "jobs-search" not in url:
        return "LinkedIn session expired or login required."

    return None


def _location_matches_filters(location: str) -> bool:
    text = location.lower()
    if not text:
        return True
    hints = tuple(k.lower() for k in LOCATION_FILTERS)
    if any(h in text for h in hints):
        return True
    if "india" in text or "remote" in text or "hybrid" in text:
        return True
    return False


def _extract_card_fields(card, page) -> dict[str, Any] | None:
    title = company = location = apply_url = snippet = ""
    easy_apply = False

    title_selectors = (
        ".job-card-list__title",
        ".job-card-container__link",
        "a[data-control-name='job_card_title']",
        "h3",
        "a[href*='/jobs/view/']",
    )
    for sel in title_selectors:
        loc = card.locator(sel).first
        if loc.count() > 0:
            try:
                title = (loc.inner_text(timeout=2000) or "").strip()
                href = loc.get_attribute("href") or ""
                if href and "/jobs/view/" in href:
                    apply_url = urljoin(page.url, href.split("?")[0])
                if title:
                    break
            except Exception:
                continue

    company_selectors = (
        ".job-card-container__company-name",
        ".artdeco-entity-lockup__subtitle",
        "h4",
    )
    for sel in company_selectors:
        loc = card.locator(sel).first
        if loc.count() > 0:
            try:
                company = (loc.inner_text(timeout=2000) or "").strip()
                if company:
                    break
            except Exception:
                continue

    location_selectors = (
        ".job-card-container__metadata-item",
        ".artdeco-entity-lockup__caption",
    )
    for sel in location_selectors:
        loc = card.locator(sel).first
        if loc.count() > 0:
            try:
                location = (loc.inner_text(timeout=2000) or "").strip()
                if location:
                    break
            except Exception:
                continue

    try:
        card_text = (card.inner_text(timeout=2000) or "").lower()
        easy_apply = "easy apply" in card_text
    except Exception:
        pass

    if not title or not company:
        return None

    if not apply_url:
        try:
            link = card.locator("a[href*='/jobs/view/']").first
            if link.count() > 0:
                href = link.get_attribute("href") or ""
                apply_url = urljoin(page.url, href.split("?")[0])
        except Exception:
            pass

    remote = any(
        token in (location or "").lower()
        for token in ("remote", "hybrid", "work from home", "wfh")
    )

    snippet_parts = [title, company, location]
    description_snippet = " · ".join(p for p in snippet_parts if p)[:500]

    return {
        "title": title,
        "company": company,
        "location": location or "India",
        "apply_url": apply_url,
        "description_snippet": description_snippet,
        "source": SOURCE_NAME,
        "remote": remote,
        "easy_apply": easy_apply,
    }


def discover_linkedin_jobs_sync(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Playwright worker entry: discover jobs using linkedin_session.json.

    Payload may include keywords, location, headless (default True), capture_screenshots.
    Returns status ok | session_invalid | blocked | error with jobs list.
    """
    options = payload or {}
    keywords = options.get("keywords") or []
    location = str(options.get("location") or DEFAULT_LOCATION)
    # Discovery always runs headless unless explicitly overridden (Prepare/Open use other commands).
    headless = bool(options.get("headless", True))
    capture_screenshots = bool(options.get("capture_screenshots", False))

    if not is_session_ready(PLATFORM):
        logger.warning("[LINKEDIN] Session invalid")
        return {
            "status": "session_invalid",
            "message": "LinkedIn session expired.",
            "jobs": [],
            "jobs_fetched": 0,
            "easy_apply_count": 0,
            "screenshot_path": "",
        }

    context = None
    page = None
    screenshot_path = ""

    try:
        logger.info(
            "[LINKEDIN] Session loaded headless=%s keywords=%s",
            headless,
            keywords,
        )

        context = create_context_sync(
            platform=PLATFORM,
            headless=headless,
            use_saved_session=True,
        )
        page = context.new_page()
        search_url = _build_search_url(keywords, location)

        _human_delay(300, 600)
        page.goto(search_url, wait_until="domcontentloaded", timeout=45_000)
        _human_delay(800, 1200)

        invalid_reason = _detect_session_invalid(page)
        if invalid_reason:
            logger.warning("[LINKEDIN] Session invalid page=%s", page.url)
            if capture_screenshots:
                shot = capture_error_state_sync(
                    page, platform=PLATFORM, error_label="session_invalid"
                )
                screenshot_path = screenshot_relative_path(shot)
            return {
                "status": "session_invalid",
                "message": invalid_reason,
                "jobs": [],
                "jobs_fetched": 0,
                "easy_apply_count": 0,
                "screenshot_path": screenshot_path,
            }

        cards = None
        for selector in JOB_CARD_SELECTORS:
            locator = page.locator(selector)
            if locator.count() > 0:
                cards = locator
                break

        extracted: list[dict[str, Any]] = []
        if cards is not None:
            count = min(cards.count(), MAX_VISIBLE_CARDS)
            for i in range(count):
                if len(extracted) >= MAX_VISIBLE_CARDS:
                    break
                try:
                    card = cards.nth(i)
                    fields = _extract_card_fields(card, page)
                    if not fields:
                        continue
                    if not _location_matches_filters(fields.get("location", "")):
                        continue
                    extracted.append(fields)
                    _human_delay(80, 180)
                except Exception:
                    logger.debug("[LINKEDIN] card extract skip index=%d", i)
                    continue

        easy_apply_count = sum(1 for j in extracted if j.get("easy_apply"))
        logger.info("[LINKEDIN] Jobs extracted: %d", len(extracted))
        logger.info("[LINKEDIN] Easy apply jobs: %d", easy_apply_count)

        if capture_screenshots:
            shot_done = capture_page_sync(page, platform=PLATFORM, label="extraction_done")
            screenshot_path = screenshot_relative_path(shot_done)

        if len(extracted) == 0:
            return {
                "status": "blocked",
                "message": "No job cards found on LinkedIn results page.",
                "jobs": [],
                "jobs_fetched": 0,
                "easy_apply_count": 0,
                "screenshot_path": screenshot_path,
            }

        return {
            "status": "ok",
            "message": f"Extracted {len(extracted)} LinkedIn jobs.",
            "jobs": extracted,
            "jobs_fetched": len(extracted),
            "easy_apply_count": easy_apply_count,
            "screenshot_path": screenshot_path,
        }
    except Exception as exc:
        logger.exception("[LINKEDIN] Discovery failed")
        rel = screenshot_path
        if capture_screenshots and page is not None:
            try:
                shot = capture_error_state_sync(page, platform=PLATFORM, error_label="failure")
                rel = screenshot_relative_path(shot)
            except Exception:
                pass
        return {
            "status": "error",
            "message": str(exc),
            "jobs": [],
            "jobs_fetched": 0,
            "easy_apply_count": 0,
            "screenshot_path": rel,
        }
    finally:
        if context is not None:
            context.close()
        close_browser_sync()


def raw_extracted_to_normalized(
    extracted: list[dict[str, Any]],
    *,
    adapter: BaseJobSource | None = None,
) -> list[NormalizedSourceJob]:
    source = adapter or LinkedInPlaywrightJobSource()
    normalized: list[NormalizedSourceJob] = []

    for item in extracted:
        apply_url = (item.get("apply_url") or "").strip()
        if apply_url and not is_valid_apply_url(apply_url):
            apply_url = ""

        raw = RawSourceJob(
            source=SOURCE_NAME,
            source_job_id=_job_id_from_url(apply_url),
            title=item.get("title", ""),
            company=item.get("company", ""),
            location=item.get("location", ""),
            remote=bool(item.get("remote")),
            apply_url=apply_url,
            description=item.get("description_snippet", ""),
            metadata={
                "easy_apply": bool(item.get("easy_apply")),
                "discovery": "playwright",
            },
        )
        job = source.normalize_job(raw)
        if job:
            job.source = SOURCE_NAME
            job.easy_apply = bool(item.get("easy_apply"))
            if job.remote:
                job.job_type = "remote"
            normalized.append(job)

    return normalized


def _job_id_from_url(apply_url: str) -> str:
    if not apply_url:
        return ""
    match = re.search(r"/jobs/view/(\d+)", apply_url)
    if match:
        return match.group(1)
    return ""


class LinkedInPlaywrightJobSource(BaseJobSource):
    """Authenticated LinkedIn discovery via Playwright worker subprocess."""

    source_name = "linkedin"

    async def fetch_jobs(self, resume_id: str | None = None) -> SourceFetchResult:
        from app.automation.browser.executor import run_playwright

        log = ProviderFetchLogger(self.source_name)

        if not is_session_ready(PLATFORM):
            message = "LinkedIn session not ready. Prepare a session on the Automation page."
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="auth_required",
                error_message=message,
                requires_auth=True,
                session_valid=False,
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=message,
                diagnostic=diagnostic,
            )

        payload = await resolve_linkedin_discovery_payload(
            resume_id,
            headless=True,
            capture_screenshots=False,
        )
        log.step(f"headless discovery keywords={payload.get('keywords', [])}")

        data = await run_playwright("linkedin-discover", timeout_sec=115, **payload)
        status = data.get("status", "error")
        message = data.get("message", "")

        if status == "session_invalid":
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="auth_required",
                error_message=message or "LinkedIn session expired.",
                requires_auth=True,
                session_valid=False,
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=diagnostic.error_message,
                diagnostic=diagnostic,
            )

        if status == "blocked":
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="selector_mismatch",
                error_message=message or "No job cards found on LinkedIn results page.",
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=diagnostic.error_message,
                diagnostic=diagnostic,
            )

        if status == "error":
            error_type = "timeout" if "timeout" in message.lower() else "unknown"
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type=error_type,
                error_message=message or "LinkedIn discovery failed.",
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=diagnostic.error_message,
                diagnostic=diagnostic,
            )

        extracted = data.get("jobs") or []
        jobs = raw_extracted_to_normalized(extracted, adapter=self)
        log.parsed(len(jobs), raw_count=len(extracted))

        if not jobs:
            fail_message = message or "LinkedIn returned no normalizable jobs"
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="selector_mismatch",
                error_message=fail_message,
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=fail_message,
                diagnostic=diagnostic,
            )

        return SourceFetchResult(source=self.source_name, jobs=jobs)


async def fetch_linkedin_discovery_debug(
    resume_id: str | None = None,
    *,
    capture_screenshots: bool = True,
) -> dict[str, Any]:
    """Debug API: run discovery with optional screenshots (headed settings ignored)."""
    from app.automation.browser.executor import run_playwright

    payload = await resolve_linkedin_discovery_payload(
        resume_id,
        headless=True,
        capture_screenshots=capture_screenshots,
    )
    return await run_playwright("linkedin-discover", timeout_sec=115, **payload)

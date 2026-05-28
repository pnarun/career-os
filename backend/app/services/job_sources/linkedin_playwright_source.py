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
    save_html_snapshot_sync,
    screenshot_relative_path,
)
from app.automation.browser.session_status_service import is_session_ready
from app.automation.browser.sync_runner import (
    close_browser_sync,
    create_context_sync,
)
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

MAX_VISIBLE_CARDS = 100
MIN_CARDS_TARGET = 60
SCROLL_MAX_ROUNDS = 18

JOBS_RESULTS_CONTAINER_SELECTORS = (
    ".jobs-search-results-list",
    "div.scaffold-layout__list",
    "ul.scaffold-layout__list-container",
    "div.jobs-search-two-pane__results",
    "div.jobs-search-results",
    "main.scaffold-layout__main",
    "ul.jobs-search__results-list",
    "div.jobs-search-results-list",
)

JOB_CARD_SELECTORS = (
    "li.jobs-search-results__list-item",
    "div.job-card-container[data-job-id]",
    "div.job-card-container",
    "li.scaffold-layout__list-item:has(a[href*='/jobs/view/'])",
    "div.scaffold-layout__list-item:has(a[href*='/jobs/view/'])",
    "div.base-search-card.job-search-card",
    "div.job-search-card",
    "div[data-job-id]",
    "li:has(a[data-control-name='job_card_title'])",
    "li:has(a[href*='/jobs/view/'])",
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
    )


def _debug_payload(
    page,
    *,
    page_type: str,
    matched_selector: str = "",
    screenshot_path: str = "",
    html_snapshot_path: str = "",
    extra_message: str = "",
) -> dict[str, str]:
    url = page.url if page else ""
    title = ""
    try:
        title = page.title() if page else ""
    except Exception:
        pass
    return {
        "page_type": page_type,
        "page_title": title,
        "current_url": url,
        "matched_selector": matched_selector,
        "screenshot_path": screenshot_path,
        "html_snapshot_path": html_snapshot_path,
        "debug_message": extra_message,
    }


def _save_debug_artifacts(page, label: str) -> tuple[str, str]:
    """Full-page screenshot + HTML snapshot; returns relative paths."""
    shot_rel = ""
    html_rel = ""
    try:
        shot = capture_page_sync(page, platform=PLATFORM, label=label)
        shot_rel = screenshot_relative_path(shot)
    except Exception as exc:
        logger.warning("[LINKEDIN] debug screenshot failed: %s", exc)
    try:
        html_path = save_html_snapshot_sync(page, platform=PLATFORM, label=label)
        html_rel = screenshot_relative_path(html_path)
    except Exception as exc:
        logger.warning("[LINKEDIN] debug html snapshot failed: %s", exc)
    return shot_rel, html_rel


def _classify_linkedin_page(page) -> str:
    url = (page.url or "").lower()
    title = ""
    try:
        title = (page.title() or "").lower()
    except Exception:
        pass

    if any(token in url for token in ("/login", "uas/login", "checkpoint")):
        return "login_or_checkpoint"
    if "/feed" in url and "/jobs/" not in url:
        return "feed"
    if "/jobs/search" in url or "keywords=" in url:
        return "jobs_search"
    if "/jobs/" in url:
        return "jobs_other"
    if any(hint in title for hint in ("security", "verification", "captcha")):
        return "security_interstitial"
    try:
        body = (page.locator("body").inner_text(timeout=3000) or "").lower()
        for hint in CAPTCHA_HINTS:
            if hint in body:
                return "security_interstitial"
        if "sign in" in body and "/jobs/" not in url:
            return "login_or_checkpoint"
    except Exception:
        pass
    return "unknown"


def _wait_for_jobs_results(page, *, timeout_ms: int = 25_000) -> str | None:
    """Wait for jobs results shell; return matched container selector if any."""
    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    except Exception:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=min(15_000, timeout_ms))
    except Exception:
        pass

    deadline = time.time() + (timeout_ms / 1000.0)
    while time.time() < deadline:
        for selector in JOBS_RESULTS_CONTAINER_SELECTORS + JOB_CARD_SELECTORS:
            try:
                loc = page.locator(selector)
                if loc.count() > 0 and loc.first.is_visible(timeout=800):
                    return selector
            except Exception:
                continue
        _human_delay(400, 700)

    return None


def _find_job_cards(page) -> tuple[Any | None, str]:
    """Return (locator, matched_selector) for job cards."""
    for selector in JOB_CARD_SELECTORS:
        try:
            locator = page.locator(selector)
            if locator.count() > 0:
                return locator, selector
        except Exception:
            continue
    return None, ""


def _extract_from_job_view_links(page) -> list[dict[str, Any]]:
    """Fallback: collect jobs from stable /jobs/view/ links when card DOM changed."""
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    links = page.locator("a[href*='/jobs/view/']")
    count = min(links.count(), MAX_VISIBLE_CARDS * 2)

    for i in range(count):
        try:
            link = links.nth(i)
            href = link.get_attribute("href") or ""
            if "/jobs/view/" not in href:
                continue
            apply_url = urljoin(page.url, href.split("?")[0])
            job_id = _job_id_from_url(apply_url)
            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title = (link.inner_text(timeout=1500) or "").strip()
            if not title or len(title) < 2:
                title = f"LinkedIn job {job_id}"

            company = ""
            location = "India"
            card_root = link.locator(
                "xpath=ancestor::li[1] | ancestor::div[@data-job-id][1]"
            ).first
            if card_root.count() > 0:
                try:
                    card_text_lines = [
                        ln.strip()
                        for ln in (card_root.inner_text(timeout=1500) or "").split("\n")
                        if ln.strip()
                    ]
                    if len(card_text_lines) >= 2:
                        if card_text_lines[0] == title and len(card_text_lines) > 1:
                            company = card_text_lines[1]
                        elif not company:
                            company = card_text_lines[0]
                    if len(card_text_lines) >= 3:
                        location = card_text_lines[2]
                except Exception:
                    pass

            if not company:
                company = "Unknown company"

            card_text_lower = title.lower()
            easy_apply = "easy apply" in card_text_lower
            remote = any(
                t in (location or "").lower()
                for t in ("remote", "hybrid", "work from home", "wfh")
            )

            results.append(
                {
                    "title": title[:200],
                    "company": company[:120],
                    "location": location[:120] or "India",
                    "apply_url": apply_url,
                    "description_snippet": f"{title} · {company} · {location}"[:500],
                    "source": SOURCE_NAME,
                    "remote": remote,
                    "easy_apply": easy_apply,
                }
            )
        except Exception:
            continue

    return results[:MAX_VISIBLE_CARDS]


def _navigate_to_jobs_search(page, search_url: str) -> str:
    """
    Navigate to LinkedIn jobs search; warm session via /jobs/ if redirected to feed.
    Returns final page_type after navigation.
    """
    logger.info("[LINKEDIN] Navigating search_url=%s", search_url)
    page.goto(LINKEDIN_JOBS_HOME, wait_until="domcontentloaded", timeout=45_000)
    _human_delay(500, 900)
    page.goto(search_url, wait_until="domcontentloaded", timeout=45_000)
    _human_delay(800, 1200)

    page_type = _classify_linkedin_page(page)
    logger.info(
        "[LINKEDIN] After navigation page_type=%s title=%r url=%s",
        page_type,
        page.title() if page else "",
        page.url,
    )

    if page_type == "feed":
        logger.info("[LINKEDIN] Landed on feed — retrying jobs search URL")
        page.goto(search_url, wait_until="domcontentloaded", timeout=45_000)
        _human_delay(1000, 1500)
        page_type = _classify_linkedin_page(page)

    if page_type not in ("jobs_search", "jobs_other"):
        return page_type

    container = _wait_for_jobs_results(page)
    if container:
        logger.info("[LINKEDIN] Jobs results container matched selector=%s", container)

    return _classify_linkedin_page(page)


def _human_delay(min_ms: float = 400, max_ms: float = 900) -> None:
    time.sleep(random.uniform(min_ms, max_ms) / 1000.0)


def _page_has_job_listings(page) -> bool:
    cards, _ = _find_job_cards(page)
    if cards is not None and cards.count() > 0:
        return True
    try:
        return page.locator("a[href*='/jobs/view/']").count() > 0
    except Exception:
        return False


def _detect_session_invalid(page) -> str | None:
    url = (page.url or "").lower()
    if any(token in url for token in ("/login", "uas/login", "checkpoint")):
        return "LinkedIn session expired or login required."

    # Guest jobs SERP includes a hidden sign-in modal — do not treat that as expired.
    if "/jobs/search" in url or ("/jobs/" in url and _page_has_job_listings(page)):
        return None

    try:
        visible_login = page.locator(
            'form:has(input[name="session_key"]):visible, '
            'input[name="session_key"]:visible'
        )
        if visible_login.count() > 0:
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

    if "sign in" in body_text and "/jobs/" not in url:
        return "LinkedIn session expired or login required."

    return None


def _scroll_job_results(page, cards, target: int) -> None:
    """Scroll the results list so LinkedIn loads more job cards."""
    prev_count = 0
    stable = 0
    for _ in range(SCROLL_MAX_ROUNDS):
        try:
            page.evaluate(
                """() => {
                  const list = document.querySelector(
                    '.jobs-search-results-list, .scaffold-layout__list, ul.scaffold-layout__list-container'
                  );
                  if (list) list.scrollTop = list.scrollHeight;
                  window.scrollBy(0, 600);
                }"""
            )
            _human_delay(350, 650)
            count = cards.count()
            if count >= target:
                break
            if count <= prev_count:
                stable += 1
                if stable >= 3:
                    break
            else:
                stable = 0
            prev_count = count
        except Exception:
            break


def _extract_card_fields(card, page) -> dict[str, Any] | None:
    title = company = location = apply_url = snippet = ""
    easy_apply = False

    title_selectors = (
        "a[data-control-name='job_card_title']",
        ".job-card-list__title",
        ".job-card-container__link",
        "a[aria-label*='job']",
        "h3.base-search-card__title",
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
        "h4.base-search-card__subtitle",
        "h4.base-search-card__subtitle a",
        "span.job-card-container__primary-description",
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
        "span.job-card-container__metadata-item",
        "div.job-card-container__metadata-wrapper",
        "span.base-search-card__metadata",
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

    if not title:
        return None
    if not company:
        company = "Unknown company"

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
    user_id = (options.get("user_id") or "").strip() or None
    keywords = options.get("keywords") or []
    location = str(options.get("location") or DEFAULT_LOCATION)
    # Discovery always runs headless unless explicitly overridden (Prepare/Open use other commands).
    headless = bool(options.get("headless", True))
    capture_screenshots = bool(options.get("capture_screenshots", False))

    if not is_session_ready(PLATFORM, user_id=user_id):
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
            user_id=user_id,
        )
        page = context.new_page()
        search_url = _build_search_url(keywords, location)

        page_type = _navigate_to_jobs_search(page, search_url)
        shot_after_load, html_after_load = _save_debug_artifacts(page, "after_jobs_load")
        logger.info(
            "[LINKEDIN] Debug artifacts screenshot=%s html=%s",
            shot_after_load,
            html_after_load,
        )

        invalid_reason = _detect_session_invalid(page)
        if invalid_reason:
            logger.warning("[LINKEDIN] Session invalid page=%s", page.url)
            shot_rel, html_rel = _save_debug_artifacts(page, "session_invalid")
            debug = _debug_payload(
                page,
                page_type=page_type,
                screenshot_path=shot_rel or shot_after_load,
                html_snapshot_path=html_rel or html_after_load,
                extra_message=invalid_reason,
            )
            return {
                "status": "session_invalid",
                "message": invalid_reason,
                "jobs": [],
                "jobs_fetched": 0,
                "easy_apply_count": 0,
                "screenshot_path": debug["screenshot_path"],
                **debug,
            }

        if page_type not in ("jobs_search", "jobs_other"):
            shot_rel, html_rel = _save_debug_artifacts(page, f"wrong_page_{page_type}")
            debug = _debug_payload(
                page,
                page_type=page_type,
                screenshot_path=shot_rel,
                html_snapshot_path=html_rel,
                extra_message=f"Expected jobs search, got {page_type}",
            )
            msg = (
                f"LinkedIn did not reach jobs search (page_type={page_type}). "
                f"url={debug['current_url']}"
            )
            return {
                "status": "blocked",
                "message": msg,
                "jobs": [],
                "jobs_fetched": 0,
                "easy_apply_count": 0,
                **debug,
            }

        cards, matched_selector = _find_job_cards(page)
        extracted: list[dict[str, Any]] = []
        extraction_mode = "cards"

        if cards is not None:
            _scroll_job_results(page, cards, MAX_VISIBLE_CARDS)
            count = min(cards.count(), MAX_VISIBLE_CARDS)
            for i in range(count):
                if len(extracted) >= MAX_VISIBLE_CARDS:
                    break
                try:
                    card = cards.nth(i)
                    fields = _extract_card_fields(card, page)
                    if not fields:
                        continue
                    extracted.append(fields)
                    _human_delay(80, 180)
                except Exception:
                    logger.debug("[LINKEDIN] card extract skip index=%d", i)
                    continue

        if len(extracted) == 0:
            extracted = _extract_from_job_view_links(page)
            extraction_mode = "job_view_links_fallback"
            if matched_selector:
                logger.info(
                    "[LINKEDIN] Card selector matched (%s) but 0 parsed — used link fallback (%d)",
                    matched_selector,
                    len(extracted),
                )

        easy_apply_count = sum(1 for j in extracted if j.get("easy_apply"))
        logger.info(
            "[LINKEDIN] Jobs extracted=%d mode=%s selector=%s page_type=%s url=%s",
            len(extracted),
            extraction_mode,
            matched_selector or "none",
            page_type,
            page.url,
        )
        logger.info("[LINKEDIN] Easy apply jobs: %d", easy_apply_count)

        if capture_screenshots and len(extracted) > 0:
            shot_done = capture_page_sync(page, platform=PLATFORM, label="extraction_done")
            screenshot_path = screenshot_relative_path(shot_done)

        if len(extracted) == 0:
            shot_rel, html_rel = _save_debug_artifacts(page, "zero_job_cards")
            debug = _debug_payload(
                page,
                page_type=page_type,
                matched_selector=matched_selector,
                screenshot_path=shot_rel or shot_after_load,
                html_snapshot_path=html_rel or html_after_load,
                extra_message="No job cards or /jobs/view/ links found",
            )
            msg = (
                "No job cards found on LinkedIn results page. "
                f"page_type={debug['page_type']} title={debug['page_title']!r} "
                f"url={debug['current_url']} selector={matched_selector or 'none'} "
                f"screenshot={debug['screenshot_path']}"
            )
            return {
                "status": "blocked",
                "message": msg,
                "jobs": [],
                "jobs_fetched": 0,
                "easy_apply_count": 0,
                **debug,
            }

        debug = _debug_payload(
            page,
            page_type=page_type,
            matched_selector=matched_selector,
            screenshot_path=screenshot_path or shot_after_load,
            html_snapshot_path=html_after_load,
        )
        return {
            "status": "ok",
            "message": f"Extracted {len(extracted)} LinkedIn jobs ({extraction_mode}).",
            "jobs": extracted,
            "jobs_fetched": len(extracted),
            "easy_apply_count": easy_apply_count,
            **debug,
        }
    except Exception as exc:
        logger.exception("[LINKEDIN] Discovery failed")
        rel = screenshot_path
        html_rel = ""
        debug: dict[str, str] = {}
        if page is not None:
            rel, html_rel = _save_debug_artifacts(page, "discovery_exception")
            debug = _debug_payload(
                page,
                page_type=_classify_linkedin_page(page),
                screenshot_path=rel,
                html_snapshot_path=html_rel,
                extra_message=str(exc)[:300],
            )
        return {
            "status": "error",
            "message": str(exc),
            "jobs": [],
            "jobs_fetched": 0,
            "easy_apply_count": 0,
            "screenshot_path": rel,
            **debug,
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


def _format_discovery_diagnostic_message(data: dict[str, Any], fallback: str) -> str:
    """Rich provider error from Playwright discovery debug fields."""
    base = (data.get("message") or fallback).strip()
    page_type = data.get("page_type") or "unknown"
    page_title = data.get("page_title") or ""
    current_url = data.get("current_url") or ""
    screenshot = data.get("screenshot_path") or ""
    html_path = data.get("html_snapshot_path") or ""
    selector = data.get("matched_selector") or ""
    return (
        f"{base} | page_type={page_type} | title={page_title!r} | url={current_url} | "
        f"selector={selector or 'none'} | screenshot={screenshot} | html={html_path}"
    )


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
            capture_screenshots=True,
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
            detailed = _format_discovery_diagnostic_message(
                data,
                message or "No job cards found on LinkedIn results page.",
            )
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="selector_mismatch",
                error_message=detailed,
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

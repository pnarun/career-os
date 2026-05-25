"""
Build LinkedIn job-search parameters from the active resume (scan preferences).

User preferences store resume_id; keywords come from parsed skills and
experience_keywords on that resume — same profile used for match scoring.
"""

from __future__ import annotations

import logging
from typing import Any

from app.models.resume import ResumeDocument

logger = logging.getLogger(__name__)

DEFAULT_KEYWORDS = ("Software Engineer", "Backend Engineer", "Full Stack Engineer")
DEFAULT_LOCATION = "India"
MAX_KEYWORD_TERMS = 6


def build_search_keywords(resume: ResumeDocument, *, max_terms: int = MAX_KEYWORD_TERMS) -> list[str]:
    """Derive LinkedIn OR-query terms from resume skills and experience keywords."""
    seen: set[str] = set()
    ordered: list[str] = []

    def add(term: str) -> None:
        cleaned = " ".join(str(term).split()).strip()
        if not cleaned or len(cleaned) < 2:
            return
        key = cleaned.lower()
        if key in seen:
            return
        seen.add(key)
        ordered.append(cleaned)

    for phrase in resume.experience_keywords:
        add(phrase)
        if len(ordered) >= max_terms:
            break

    for skill in resume.skills:
        add(skill)
        if len(ordered) >= max_terms:
            break

    if not ordered:
        for fallback in DEFAULT_KEYWORDS:
            add(fallback)
            if len(ordered) >= max_terms:
                break

    return ordered[:max_terms]


def build_linkedin_discovery_payload(
    resume: ResumeDocument,
    *,
    headless: bool = True,
    capture_screenshots: bool = False,
) -> dict[str, Any]:
    keywords = build_search_keywords(resume)
    logger.info(
        "[LINKEDIN] Search context resume=%s keywords=%s",
        resume.id,
        keywords,
    )
    return {
        "keywords": keywords,
        "location": DEFAULT_LOCATION,
        "headless": headless,
        "capture_screenshots": capture_screenshots,
    }


async def resolve_linkedin_discovery_payload(
    resume_id: str | None = None,
    *,
    headless: bool = True,
    capture_screenshots: bool = False,
) -> dict[str, Any]:
    """Load resume from preferences or fallback and build worker payload."""
    from app.services.job_service import _resolve_resume_for_scan
    from app.services.user_preferences_service import get_preferences

    effective_resume_id = resume_id
    if not effective_resume_id:
        preferences = await get_preferences()
        if preferences:
            effective_resume_id = preferences.resume_id

    resume = await _resolve_resume_for_scan(effective_resume_id)
    return build_linkedin_discovery_payload(
        resume,
        headless=headless,
        capture_screenshots=capture_screenshots,
    )

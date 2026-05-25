"""
Build LinkedIn job-search parameters from the active resume (scan preferences).

Keywords mirror how users search on LinkedIn (e.g. "Angular Developer"), not strict
skill filters. Target roles from scan preferences take priority when set.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.models.resume import ResumeDocument

logger = logging.getLogger(__name__)

DEFAULT_KEYWORDS = ("Software Developer", "Full Stack Developer")
DEFAULT_LOCATION = "India"
MAX_KEYWORD_TERMS = 8

ROLE_SUFFIXES = ("developer", "engineer", "consultant", "architect", "lead", "manager")
TECH_ROLE_WORDS = re.compile(
    r"\b(angular|react|vue|node|python|java|\.net|dotnet|aws|devops|full[\s-]?stack|"
    r"backend|frontend|mobile|ios|android|typescript|javascript|golang|go)\b",
    re.IGNORECASE,
)


def _title_case_phrase(text: str) -> str:
    cleaned = " ".join(str(text).split()).strip()
    if not cleaned:
        return ""
    return " ".join(part.capitalize() for part in cleaned.split())


def build_primary_role_query(
    resume: ResumeDocument,
    target_roles: list[str] | None = None,
) -> str:
    """Single LinkedIn-style query (e.g. Angular Developer) from prefs or resume."""
    for role in target_roles or []:
        phrase = _title_case_phrase(role)
        if len(phrase) >= 4:
            return phrase

    for phrase in resume.experience_keywords:
        cleaned = _title_case_phrase(phrase)
        if len(cleaned) >= 4:
            lower = cleaned.lower()
            if any(s in lower for s in ROLE_SUFFIXES) or TECH_ROLE_WORDS.search(cleaned):
                return cleaned

    for skill in resume.skills:
        raw = " ".join(str(skill).split()).strip()
        if len(raw) < 2:
            continue
        lower = raw.lower()
        if any(s in lower for s in ROLE_SUFFIXES):
            return _title_case_phrase(raw)
        if TECH_ROLE_WORDS.search(raw):
            return f"{_title_case_phrase(raw)} Developer"

    return DEFAULT_KEYWORDS[0]


def build_search_keywords(
    resume: ResumeDocument,
    *,
    target_roles: list[str] | None = None,
    max_terms: int = MAX_KEYWORD_TERMS,
) -> list[str]:
    """
    Derive LinkedIn search terms: primary role query first, then related skills.
    Does not act as a hard filter — all results are scored and sorted later.
    """
    seen: set[str] = set()
    ordered: list[str] = []

    def add(term: str) -> None:
        cleaned = _title_case_phrase(term) if term else ""
        if not cleaned or len(cleaned) < 2:
            return
        key = cleaned.lower()
        if key in seen:
            return
        seen.add(key)
        ordered.append(cleaned)

    add(build_primary_role_query(resume, target_roles=target_roles))

    for role in (target_roles or [])[1:4]:
        add(role)
        if len(ordered) >= max_terms:
            break

    for skill in resume.skills:
        add(skill)
        if len(ordered) >= max_terms:
            break

    for phrase in resume.experience_keywords:
        add(phrase)
        if len(ordered) >= max_terms:
            break

    if len(ordered) < 2:
        for fallback in DEFAULT_KEYWORDS:
            add(fallback)

    return ordered[:max_terms]


def build_linkedin_discovery_payload(
    resume: ResumeDocument,
    *,
    target_roles: list[str] | None = None,
    preferred_location: str | None = None,
    headless: bool = True,
    capture_screenshots: bool = False,
) -> dict[str, Any]:
    keywords = build_search_keywords(resume, target_roles=target_roles)
    location = (preferred_location or "").strip() or DEFAULT_LOCATION
    logger.info(
        "[LINKEDIN] Search context resume=%s keywords=%s location=%s",
        resume.id,
        keywords,
        location,
    )
    return {
        "keywords": keywords,
        "location": location,
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
    target_roles: list[str] = []
    preferred_location = DEFAULT_LOCATION
    try:
        preferences = await get_preferences()
        if preferences:
            if not effective_resume_id:
                effective_resume_id = preferences.resume_id
            target_roles = list(preferences.target_roles or [])
            if preferences.preferred_locations:
                preferred_location = preferences.preferred_locations[0]
    except Exception:
        preferences = None

    resume = await _resolve_resume_for_scan(effective_resume_id)
    return build_linkedin_discovery_payload(
        resume,
        target_roles=target_roles,
        preferred_location=preferred_location,
        headless=headless,
        capture_screenshots=capture_screenshots,
    )

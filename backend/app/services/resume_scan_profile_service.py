"""Derive scan targeting fields from a parsed resume profile."""

from __future__ import annotations

import re
from typing import Any

from app.models.resume import ResumeDocument

_ROLE_PATTERNS = (
    r"\b(software engineer|backend developer|full[\s-]?stack|devops|data engineer|"
    r"ml engineer|cloud engineer|sre|platform engineer|frontend developer)\b"
)
_YEARS_PATTERN = re.compile(
    r"(\d{1,2})\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
    re.IGNORECASE,
)
_LOCATION_HINTS = (
    "remote",
    "bangalore",
    "bengaluru",
    "hyderabad",
    "mumbai",
    "delhi",
    "pune",
    "chennai",
    "india",
    "germany",
    "uk",
    "usa",
)


def extract_scan_profile_from_resume(resume: ResumeDocument) -> dict[str, Any]:
    """Build roles, experience years, and location hints from resume text."""
    raw = (resume.raw_text or "").lower()
    skills = [s.strip() for s in (resume.skills or []) if s.strip()]

    roles: list[str] = []
    for match in re.finditer(_ROLE_PATTERNS, raw, re.IGNORECASE):
        role = match.group(1).strip().title()
        if role not in roles:
            roles.append(role)

    if not roles and skills:
        top = skills[:3]
        roles.append(f"{', '.join(top)} Engineer")

    years = 0
    year_match = _YEARS_PATTERN.search(raw)
    if year_match:
        years = int(year_match.group(1))

    locations: list[str] = []
    for hint in _LOCATION_HINTS:
        if hint in raw and hint.title() not in locations:
            locations.append(hint.title())

    if "remote" in raw.lower() and "Remote" not in locations:
        locations.append("Remote")

    return {
        "target_roles": roles[:10],
        "target_skills": skills[:50],
        "years_experience": years,
        "preferred_locations": locations[:10],
        "primary_skills": skills[:25],
    }

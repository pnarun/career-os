"""Map parsed resume data to application form fields."""

from __future__ import annotations

import re
from typing import Any

from app.models.auto_apply import FilledField


def _extract_name_from_text(raw_text: str, emails: list[str]) -> str:
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    if not lines:
        return ""
    first = lines[0]
    if "@" in first or len(first) > 60:
        return ""
    if re.match(r"^[A-Za-z][A-Za-z\s\.\-']{1,50}$", first):
        return first
    return ""


def _extract_phone(raw_text: str) -> str:
    patterns = (
        r"\+?\d{1,3}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{4}",
        r"\b\d{10}\b",
    )
    for pattern in patterns:
        match = re.search(pattern, raw_text)
        if match:
            return match.group(0).strip()
    return ""


def _extract_link(links: list[str], domain: str) -> str:
    domain = domain.lower()
    for link in links:
        if domain in link.lower():
            return link
    return ""


def _estimate_years(experience_keywords: list[str], raw_text: str) -> str:
    patterns = (
        r"(\d+)\+?\s*years?\s*(?:of\s*)?experience",
        r"experience\s*[:\-]?\s*(\d+)\+?\s*years?",
    )
    text = raw_text.lower()
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    if experience_keywords:
        return "3"
    return ""


def build_autofill_profile(resume: Any) -> dict[str, str]:
    """Build a flat autofill map from resume document."""
    raw_text = getattr(resume, "raw_text", "") or ""
    emails = list(getattr(resume, "emails", []) or [])
    links = list(getattr(resume, "links", []) or [])
    skills = list(getattr(resume, "skills", []) or [])
    experience_keywords = list(getattr(resume, "experience_keywords", []) or [])

    profile = {
        "name": _extract_name_from_text(raw_text, emails),
        "email": emails[0] if emails else "",
        "phone": _extract_phone(raw_text),
        "linkedin": _extract_link(links, "linkedin.com"),
        "github": _extract_link(links, "github.com"),
        "skills": ", ".join(skills[:15]),
        "years_of_experience": _estimate_years(experience_keywords, raw_text),
        "location": _extract_location(raw_text),
    }
    return {k: v for k, v in profile.items() if v}


def _extract_location(raw_text: str) -> str:
    for line in raw_text.splitlines()[:8]:
        line = line.strip()
        if any(k in line.lower() for k in ("india", "remote", "bangalore", "hyderabad", "city")):
            if len(line) < 80:
                return line
    return ""


def autofill_fields(
    detected_fields: list[Any],
    profile: dict[str, str],
) -> list[FilledField]:
    """Map detected fields to autofill values with confidence scores."""
    filled: list[FilledField] = []
    field_map = {
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "salary": "",
        "notice_period": "",
        "work_authorization": "",
        "relocation": "",
        "years_of_experience": profile.get("years_of_experience", ""),
        "text": profile.get("name", ""),
    }

    for detected in detected_fields:
        field_type = getattr(detected, "field_type", "text")
        label = getattr(detected, "label", "")
        value = field_map.get(field_type, "")

        if not value and field_type == "text" and label:
            label_lower = label.lower()
            if "name" in label_lower:
                value = profile.get("name", "")
            elif "linkedin" in label_lower:
                value = profile.get("linkedin", "")
            elif "github" in label_lower:
                value = profile.get("github", "")
            elif "skill" in label_lower:
                value = profile.get("skills", "")

        if value:
            confidence = 0.95 if field_type in ("email", "phone") else 0.75
            filled.append(
                FilledField(
                    label=label or field_type,
                    value=value,
                    confidence=confidence,
                    source="resume",
                )
            )
    return filled


def compute_confidence_score(
    filled_fields: list[FilledField],
    unknown_count: int,
) -> float:
    if not filled_fields and unknown_count > 0:
        return 0.0
    if not filled_fields:
        return 0.5
    avg = sum(f.confidence for f in filled_fields) / len(filled_fields)
    penalty = min(unknown_count * 0.15, 0.45)
    return max(0.0, min(1.0, avg - penalty))

"""Shared resume text analysis utilities — deterministic, no fabrication."""

from __future__ import annotations

import re
from typing import Any

from app.utils.skills_master import extract_skills_from_text

SECTION_HEADERS = (
    "summary",
    "professional summary",
    "objective",
    "profile",
    "skills",
    "technical skills",
    "core competencies",
    "experience",
    "work experience",
    "employment",
    "professional experience",
    "projects",
    "personal projects",
    "education",
    "certifications",
    "certificates",
    "achievements",
)

WEAK_VERB_PATTERNS: list[tuple[str, str]] = [
    (r"\bworked on\b", "Designed or built"),
    (r"\bresponsible for\b", "Led or delivered"),
    (r"\bhelped with\b", "Collaborated on"),
    (r"\binvolved in\b", "Contributed to"),
    (r"\bdid\b", "Implemented"),
    (r"\bhandled\b", "Managed"),
    (r"\bparticipated in\b", "Drove"),
    (r"\bassisted with\b", "Supported"),
    (r"\bwas part of\b", "Contributed to"),
]

STRONG_VERBS = (
    "designed",
    "built",
    "developed",
    "implemented",
    "architected",
    "led",
    "delivered",
    "optimized",
    "scaled",
    "automated",
    "reduced",
    "increased",
    "migrated",
    "deployed",
    "engineered",
)

METRIC_PATTERN = re.compile(
    r"\d+\s*%|\d+\s*k\+?|\d+\s*m\+?|\$\d+|\d+\s*(users|requests|transactions|clients|teams|engineers)",
    re.IGNORECASE,
)

BULLET_PATTERN = re.compile(r"^\s*[-•*]\s+", re.MULTILINE)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def detect_sections(raw_text: str) -> dict[str, str]:
    """Split resume raw text into named sections by common headers."""
    lines = raw_text.splitlines()
    sections: dict[str, list[str]] = {}
    current = "header"
    sections[current] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower().rstrip(":")
        header_match = None
        for header in SECTION_HEADERS:
            if lower == header or lower.startswith(f"{header}:"):
                header_match = header
                break
        if header_match:
            current = header_match
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(stripped)

    return {name: "\n".join(content) for name, content in sections.items() if content}


def section_completeness(sections: dict[str, str]) -> dict[str, bool]:
    has_skills = any(k for k in sections if "skill" in k.lower())
    has_experience = any(k for k in sections if "experience" in k.lower() or "employment" in k.lower())
    has_education = any(k for k in sections if "education" in k.lower())
    has_summary = any(k for k in sections if "summary" in k.lower() or "objective" in k.lower() or "profile" in k.lower())
    has_projects = any(k for k in sections if "project" in k.lower())
    has_certs = any(k for k in sections if "certif" in k.lower())
    return {
        "summary": has_summary,
        "skills": has_skills,
        "experience": has_experience,
        "projects": has_projects,
        "education": has_education,
        "certifications": has_certs,
    }


def extract_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    for line in split_lines(text):
        cleaned = BULLET_PATTERN.sub("", line).strip()
        if cleaned and (line.lstrip().startswith(("-", "•", "*")) or len(cleaned) > 20):
            bullets.append(cleaned)
    return bullets


def count_metrics(text: str) -> int:
    return len(METRIC_PATTERN.findall(text))


def analyze_action_verbs(text: str) -> dict[str, Any]:
    """Find weak phrasing and suggest stronger alternatives (truthful rewrites)."""
    weak_found: list[dict[str, str]] = []
    lower = text.lower()
    for pattern, suggestion in WEAK_VERB_PATTERNS:
        for match in re.finditer(pattern, lower):
            snippet_start = max(0, match.start() - 20)
            snippet_end = min(len(text), match.end() + 40)
            snippet = text[snippet_start:snippet_end].strip()
            weak_found.append({
                "weak_phrase": match.group(0),
                "context": snippet,
                "suggestion": f"Replace with action-led language, e.g. '{suggestion} …' using your actual work",
            })
    strong_count = sum(1 for verb in STRONG_VERBS if verb in lower)
    return {
        "weak_phrases": weak_found[:10],
        "strong_verb_count": strong_count,
        "has_measurable_impact": count_metrics(text) > 0,
        "metric_count": count_metrics(text),
    }


def readability_score(raw_text: str) -> int:
    """Simple readability heuristic (0-100)."""
    words = re.findall(r"\b\w+\b", raw_text)
    if not words:
        return 0
    sentences = max(1, len(re.findall(r"[.!?]+", raw_text)))
    avg_words = len(words) / sentences
    long_words = sum(1 for w in words if len(w) > 12)
    long_ratio = long_words / len(words)
    score = 100
    if avg_words > 28:
        score -= min(25, int((avg_words - 28) * 2))
    if long_ratio > 0.15:
        score -= min(20, int(long_ratio * 100))
    if len(words) < 150:
        score -= 15
    return max(0, min(100, score))


def format_score(raw_text: str, sections: dict[str, str]) -> int:
    completeness = section_completeness(sections)
    score = 50
    score += sum(8 for present in completeness.values() if present)
    if re.search(r"table|column", raw_text.lower()):
        score -= 10
    if len(raw_text) > 200:
        score += 10
    bullets = extract_bullets(raw_text)
    if len(bullets) >= 5:
        score += 10
    return max(0, min(100, score))


def resume_skill_set(raw_text: str, skills: list[str]) -> set[str]:
    extracted = extract_skills_from_text(raw_text)
    combined = {s.lower() for s in skills} | {s.lower() for s in extracted}
    return combined

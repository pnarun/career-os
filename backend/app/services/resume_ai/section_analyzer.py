"""Section-level resume analysis."""

from __future__ import annotations

from typing import Any

from app.models.resume import ResumeDocument
from app.services.resume_ai._resume_utils import (
    analyze_action_verbs,
    detect_sections,
    extract_bullets,
    section_completeness,
)


def analyze_sections(resume: ResumeDocument) -> dict[str, Any]:
    """Analyze each resume section for completeness and quality."""
    sections = detect_sections(resume.raw_text)
    completeness = section_completeness(sections)
    section_details: dict[str, Any] = {}

    for section_name, content in sections.items():
        bullets = extract_bullets(content)
        verbs = analyze_action_verbs(content)
        section_details[section_name] = {
            "present": True,
            "word_count": len(content.split()),
            "bullet_count": len(bullets),
            "weak_phrases": verbs["weak_phrases"][:3],
            "has_metrics": verbs["has_measurable_impact"],
            "quality": _section_quality(bullets, verbs, content),
        }

    for required, present in completeness.items():
        if not present and required not in section_details:
            section_details[required] = {
                "present": False,
                "word_count": 0,
                "bullet_count": 0,
                "weak_phrases": [],
                "has_metrics": False,
                "quality": "missing",
            }

    repetitive = _find_repetitive_phrases(resume.raw_text)
    low_impact = _low_impact_bullets(resume.raw_text)

    return {
        "sections": section_details,
        "completeness": completeness,
        "missing_sections": [k for k, v in completeness.items() if not v],
        "repetitive_content": repetitive,
        "low_impact_bullets": low_impact,
    }


def _section_quality(bullets: list[str], verbs: dict[str, Any], content: str) -> str:
    if not content.strip():
        return "missing"
    if len(bullets) >= 3 and verbs["has_measurable_impact"]:
        return "strong"
    if len(bullets) >= 2 and verbs["strong_verb_count"] >= 2:
        return "good"
    if verbs["weak_phrases"]:
        return "weak"
    return "fair"


def _find_repetitive_phrases(text: str) -> list[str]:
    words = text.lower().split()
    phrases: dict[str, int] = {}
    for i in range(len(words) - 2):
        phrase = " ".join(words[i : i + 3])
        if len(phrase) > 10:
            phrases[phrase] = phrases.get(phrase, 0) + 1
    return [p for p, count in sorted(phrases.items(), key=lambda x: -x[1]) if count >= 3][:5]


def _low_impact_bullets(text: str) -> list[str]:
    bullets = extract_bullets(text)
    low: list[str] = []
    for bullet in bullets:
        verbs = analyze_action_verbs(bullet)
        if not verbs["has_measurable_impact"] and verbs["weak_phrases"]:
            low.append(bullet[:120])
    return low[:8]

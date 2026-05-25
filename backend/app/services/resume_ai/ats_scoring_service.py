"""ATS scoring engine — deterministic analysis."""

from __future__ import annotations

from typing import Any

from app.models.resume import ResumeDocument
from app.services.resume_ai._resume_utils import (
    analyze_action_verbs,
    detect_sections,
    format_score,
    readability_score,
    resume_skill_set,
)
from app.services.resume_ai.section_analyzer import analyze_sections
from app.utils.skills_master import categorize_skills, extract_skills_from_text


def compute_ats_score(resume: ResumeDocument, *, job_description: str = "") -> dict[str, Any]:
    """Generate ATS score breakdown and factor analysis."""
    sections = detect_sections(resume.raw_text)
    section_analysis = analyze_sections(resume)
    verbs = analyze_action_verbs(resume.raw_text)
    completeness = section_analysis["completeness"]

    skills = list(resume_skill_set(resume.raw_text, resume.skills))
    skill_categories = categorize_skills([s for s in resume.skills] or extract_skills_from_text(resume.raw_text))

    keyword_score = _keyword_score(resume, job_description)
    format_sc = format_score(resume.raw_text, sections)
    skills_sc = _skills_score(skills, skill_categories)
    experience_sc = _experience_score(resume.raw_text, verbs)
    readability_sc = readability_score(resume.raw_text)

    ats_score = int(
        keyword_score * 0.25
        + format_sc * 0.20
        + skills_sc * 0.25
        + experience_sc * 0.20
        + readability_sc * 0.10
    )

    factors = {
        "keyword_coverage": keyword_score,
        "formatting_quality": format_sc,
        "section_completeness": int(sum(completeness.values()) / max(len(completeness), 1) * 100),
        "action_verbs": min(100, verbs["strong_verb_count"] * 8),
        "measurable_impact": min(100, verbs["metric_count"] * 15),
        "readability": readability_sc,
        "role_alignment": keyword_score,
    }

    return {
        "ats_score": ats_score,
        "keyword_score": keyword_score,
        "format_score": format_sc,
        "skills_score": skills_sc,
        "experience_score": experience_sc,
        "factors": factors,
        "section_analysis": section_analysis,
    }


def _keyword_score(resume: ResumeDocument, job_description: str) -> int:
    resume_skills = extract_skills_from_text(resume.raw_text) or resume.skills
    if not job_description:
        return min(100, 40 + len(resume_skills) * 3)

    job_skills = extract_skills_from_text(job_description)
    if not job_skills:
        return 60
    resume_set = {s.lower() for s in resume_skills}
    matched = sum(1 for s in job_skills if s.lower() in resume_set)
    return int(matched / len(job_skills) * 100)


def _skills_score(skills: list[str], categories: dict[str, list[str]]) -> int:
    if not skills:
        return 20
    score = 30 + min(40, len(skills) * 3)
    active_categories = sum(1 for group in categories.values() if group)
    score += active_categories * 5
    return min(100, score)


def _experience_score(raw_text: str, verbs: dict[str, Any]) -> int:
    score = 40
    if verbs["strong_verb_count"] >= 5:
        score += 25
    elif verbs["strong_verb_count"] >= 2:
        score += 15
    if verbs["has_measurable_impact"]:
        score += min(25, verbs["metric_count"] * 8)
    if len(raw_text) > 800:
        score += 10
    penalty = min(20, len(verbs["weak_phrases"]) * 4)
    return max(0, min(100, score - penalty))

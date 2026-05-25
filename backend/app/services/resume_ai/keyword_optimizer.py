"""Keyword optimization — missing and underrepresented terms."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.models.resume import ResumeDocument
from app.services.resume_ai._resume_utils import resume_skill_set
from app.utils.skills_master import SKILLS_MASTER, extract_skills_from_text


def analyze_keywords(
    resume: ResumeDocument,
    *,
    job_description: str = "",
    market_jobs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Detect missing, underrepresented, and weak terminology."""
    resume_text = resume.raw_text.lower()
    resume_skills = resume_skill_set(resume.raw_text, resume.skills)

    target_skills: list[str] = []
    if job_description:
        target_skills = extract_skills_from_text(job_description)
    elif market_jobs:
        counter: Counter[str] = Counter()
        for job in market_jobs:
            for skill in job.get("missing_skills") or []:
                counter[skill.strip()] += 1
            for skill in extract_skills_from_text(job.get("description", "")):
                counter[skill] += 1
        target_skills = [s for s, _ in counter.most_common(30)]

    if not target_skills:
        target_skills = SKILLS_MASTER[:25]

    missing: list[dict[str, str]] = []
    underrepresented: list[dict[str, str]] = []
    present: list[str] = []

    for skill in target_skills:
        key = skill.lower()
        in_skills = key in resume_skills
        in_text = key in resume_text or skill.lower() in resume_text
        if not in_skills and not in_text:
            missing.append({
                "keyword": skill,
                "status": "missing",
                "recommendation": f"Add '{skill}' to Skills or Experience if you genuinely have this experience",
            })
        elif in_skills and not in_text:
            underrepresented.append({
                "keyword": skill,
                "status": "underrepresented",
                "recommendation": f"'{skill}' is listed but not mentioned in experience — add a bullet demonstrating it",
            })
        else:
            present.append(skill)

    weak_terms = _weak_terminology(resume.raw_text)

    coverage = int(len(present) / max(len(target_skills), 1) * 100)

    return {
        "coverage_percent": coverage,
        "missing_keywords": missing[:15],
        "underrepresented_keywords": underrepresented[:10],
        "present_keywords": present[:20],
        "weak_terminology": weak_terms,
        "target_skill_count": len(target_skills),
    }


def _weak_terminology(text: str) -> list[dict[str, str]]:
    weak_patterns = [
        ("worked on", "Use specific verbs: Designed, Built, Implemented"),
        ("responsible for", "Lead with outcomes: Led delivery of…"),
        ("various", "Be specific about technologies and scope"),
        ("etc", "List concrete items instead of 'etc.'"),
        ("familiar with", "Use 'Proficient in' or demonstrate in a bullet"),
    ]
    found: list[dict[str, str]] = []
    lower = text.lower()
    for phrase, fix in weak_patterns:
        if phrase in lower:
            found.append({"phrase": phrase, "recommendation": fix})
    return found

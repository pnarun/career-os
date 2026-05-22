import logging
from typing import TypedDict

from app.utils.skills_master import extract_skills_from_text

logger = logging.getLogger(__name__)


class MatchAnalysis(TypedDict):
    match_percentage: int
    matched_skills: list[str]
    missing_skills: list[str]
    job_skills: list[str]
    recommendation: str


def _recommendation_for_score(match_percentage: int) -> str:
    if match_percentage >= 90:
        return "Excellent Match"
    if match_percentage >= 75:
        return "Strong Match"
    if match_percentage >= 50:
        return "Moderate Match"
    return "Weak Match"


def _normalize_skill_map(skills: list[str]) -> dict[str, str]:
    """Map lowercase skill name to canonical display value."""
    return {skill.lower(): skill for skill in skills}


def match_resume_to_job(
    resume_skills: list[str],
    job_description: str,
) -> MatchAnalysis:
    """Compare resume skills against skills extracted from a job description."""
    job_skills = extract_skills_from_text(job_description)

    resume_map = _normalize_skill_map(resume_skills)
    job_map = _normalize_skill_map(job_skills)

    matched_skills = sorted(
        [resume_map[key] for key in job_map if key in resume_map],
        key=str.lower,
    )
    missing_skills = sorted(
        [job_map[key] for key in job_map if key not in resume_map],
        key=str.lower,
    )

    if job_skills:
        match_percentage = round((len(matched_skills) / len(job_skills)) * 100)
    else:
        match_percentage = 0

    match_percentage = max(0, min(100, match_percentage))
    recommendation = _recommendation_for_score(match_percentage)

    logger.info(
        "Match analysis: score=%d matched=%d missing=%d job_skills=%d",
        match_percentage,
        len(matched_skills),
        len(missing_skills),
        len(job_skills),
    )

    return MatchAnalysis(
        match_percentage=match_percentage,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        job_skills=job_skills,
        recommendation=recommendation,
    )

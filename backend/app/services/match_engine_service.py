import logging
from typing import TypedDict

from app.services.job_match_scoring_service import JobMatchResult, ResumeProfile, score_resume_against_job

logger = logging.getLogger(__name__)


class MatchAnalysis(TypedDict):
    match_percentage: int
    matched_skills: list[str]
    missing_skills: list[str]
    job_skills: list[str]
    recommendation: str
    strengths: list[str]
    recommendations: list[str]
    experience_alignment: str
    career_fit: str
    why_match: list[str]
    match_breakdown: dict


def match_resume_to_job(
    resume_skills: list[str],
    job_description: str,
    *,
    job_title: str = "",
    job_location: str = "",
    job_remote: bool = False,
    resume_keywords: list[str] | None = None,
    resume_raw_text: str = "",
) -> MatchAnalysis:
    """Compare resume profile against a job using weighted match scoring v2."""
    result: JobMatchResult = score_resume_against_job(
        ResumeProfile(
            skills=resume_skills,
            experience_keywords=resume_keywords or [],
            raw_text=resume_raw_text,
            links=[],
        ),
        {
            "title": job_title,
            "description": job_description,
            "location": job_location,
            "remote": job_remote,
        },
    )

    return MatchAnalysis(
        match_percentage=result["match_score"],
        matched_skills=result["matched_skills"],
        missing_skills=result["missing_skills"],
        job_skills=result["job_skills"],
        recommendation=result["recommendation"],
        strengths=result["strengths"],
        recommendations=result["recommendations"],
        experience_alignment=result["experience_alignment"],
        career_fit=result["career_fit"],
        why_match=result["why_match"],
        match_breakdown=result["match_breakdown"],
    )

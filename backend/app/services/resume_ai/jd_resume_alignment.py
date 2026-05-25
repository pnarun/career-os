"""Job description ↔ resume alignment analysis."""

from __future__ import annotations

from typing import Any

from app.models.resume import ResumeDocument
from app.services.job_match_scoring_service import ResumeProfile, score_resume_against_job
from app.services.resume_ai._resume_utils import analyze_action_verbs, detect_sections
from app.services.resume_ai.keyword_optimizer import analyze_keywords
from app.services.resume_ai.section_analyzer import analyze_sections


def align_resume_to_job(
    resume: ResumeDocument,
    *,
    job_description: str,
    job_title: str = "",
    job_location: str = "",
    job_remote: bool = False,
) -> dict[str, Any]:
    """Align resume against a specific job description."""
    match_result = score_resume_against_job(
        ResumeProfile(
            skills=resume.skills,
            experience_keywords=resume.experience_keywords,
            raw_text=resume.raw_text,
            links=resume.links,
        ),
        {
            "title": job_title,
            "description": job_description,
            "location": job_location,
            "remote": job_remote,
        },
    )

    keywords = analyze_keywords(resume, job_description=job_description)
    sections = analyze_sections(resume)
    verbs = analyze_action_verbs(resume.raw_text)
    parsed = detect_sections(resume.raw_text)

    weak_sections: list[str] = []
    for name, detail in sections["sections"].items():
        if detail.get("quality") in ("weak", "missing"):
            weak_sections.append(name)

    strengths: list[str] = list(match_result.get("strengths") or [])
    if match_result.get("matched_skills"):
        strengths.append(
            f"Skills overlap: {', '.join(match_result['matched_skills'][:6])}"
        )

    suggested_additions: list[str] = []
    for item in keywords["missing_keywords"][:8]:
        suggested_additions.append(item["recommendation"])
    for item in keywords["underrepresented_keywords"][:4]:
        suggested_additions.append(item["recommendation"])

    if not verbs["has_measurable_impact"]:
        suggested_additions.append(
            "Add quantified outcomes to experience bullets relevant to this role"
        )

    reorder_suggestions: list[str] = []
    if resume.skills and match_result.get("matched_skills"):
        reorder_suggestions.append(
            f"Move matching skills ({', '.join(match_result['matched_skills'][:4])}) to the top of your Skills section"
        )
    if job_title and parsed:
        reorder_suggestions.append(
            f"Tailor summary to emphasize fit for '{job_title}' using your existing experience"
        )

    return {
        "alignment_score": match_result["match_score"],
        "match_breakdown": match_result.get("match_breakdown", {}),
        "matched_skills": match_result.get("matched_skills", []),
        "missing_keywords": [k["keyword"] for k in keywords["missing_keywords"]],
        "suggested_additions": suggested_additions[:10],
        "weak_sections": weak_sections,
        "strengths": strengths[:8],
        "recommendations": match_result.get("recommendations", []),
        "reorder_suggestions": reorder_suggestions,
        "keyword_coverage": keywords["coverage_percent"],
    }

"""Resume optimization orchestrator — job-specific tailoring recommendations."""

from __future__ import annotations

from typing import Any

from app.models.resume import ResumeDocument
from app.services.resume_ai.ats_scoring_service import compute_ats_score
from app.services.resume_ai.jd_resume_alignment import align_resume_to_job
from app.services.resume_ai.keyword_optimizer import analyze_keywords
from app.services.resume_ai.resume_feedback_service import generate_resume_feedback


def optimize_resume_for_job(
    resume: ResumeDocument,
    *,
    job_description: str,
    job_title: str = "",
    job_location: str = "",
    job_remote: bool = False,
) -> dict[str, Any]:
    """
    Generate truthful optimization plan for a specific job.
    Does NOT fabricate experience — only rewording and emphasis suggestions.
    """
    alignment = align_resume_to_job(
        resume,
        job_description=job_description,
        job_title=job_title,
        job_location=job_location,
        job_remote=job_remote,
    )
    ats_before = compute_ats_score(resume)
    ats_tailored = compute_ats_score(resume, job_description=job_description)
    feedback = generate_resume_feedback(resume, job_description=job_description)
    keywords = analyze_keywords(resume, job_description=job_description)

    optimization_plan: list[dict[str, str]] = []

    for skill in alignment["missing_keywords"][:5]:
        optimization_plan.append({
            "type": "keyword",
            "action": f"Consider adding '{skill}' if you have genuine experience",
            "priority": "high",
        })

    for suggestion in alignment["reorder_suggestions"]:
        optimization_plan.append({
            "type": "structure",
            "action": suggestion,
            "priority": "medium",
        })

    for change in feedback["high_impact_changes"][:4]:
        optimization_plan.append({
            "type": "content",
            "action": change,
            "priority": "high",
        })

    for item in keywords["underrepresented_keywords"][:3]:
        optimization_plan.append({
            "type": "emphasis",
            "action": item["recommendation"],
            "priority": "medium",
        })

    projected_improvement = min(
        100,
        ats_tailored["ats_score"] + len(optimization_plan) * 2,
    )

    return {
        "job_title": job_title,
        "alignment_score": alignment["alignment_score"],
        "ats_score_before": ats_before["ats_score"],
        "ats_score_tailored": ats_tailored["ats_score"],
        "projected_ats_score": projected_improvement,
        "optimization_plan": optimization_plan[:12],
        "alignment": alignment,
        "feedback": feedback,
        "keyword_analysis": keywords,
        "disclaimer": (
            "All suggestions are based on your existing resume content. "
            "Only add skills and achievements you can truthfully demonstrate."
        ),
    }

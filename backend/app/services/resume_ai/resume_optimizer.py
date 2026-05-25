"""Resume optimization orchestrator — job-specific tailoring recommendations."""

from __future__ import annotations

from typing import Any

from app.models.resume import ResumeDocument
from app.services.resume_ai.ats_scoring_service import compute_ats_score
from app.services.resume_ai.jd_resume_alignment import align_resume_to_job
from app.services.resume_ai.keyword_optimizer import analyze_keywords
from app.services.resume_ai.resume_feedback_service import generate_resume_feedback


def _resume_has_skill(resume: ResumeDocument, keyword: str) -> bool:
    needle = keyword.lower().strip()
    if not needle:
        return False
    hay = " ".join(resume.skills).lower()
    if needle in hay:
        return True
    return needle in (resume.raw_text or "").lower()


def _genuine_missing_skills(
    resume: ResumeDocument,
    alignment: dict[str, Any],
    keywords: dict[str, Any],
) -> list[str]:
    """JD keywords absent from resume — only suggest additions the user may truthfully claim."""
    missing: list[str] = []
    seen: set[str] = set()

    for kw in alignment.get("missing_keywords") or []:
        key = str(kw).lower().strip()
        if not key or key in seen or _resume_has_skill(resume, key):
            continue
        seen.add(key)
        missing.append(str(kw))

    for item in keywords.get("missing_keywords") or []:
        word = str(item.get("keyword", "")).strip()
        key = word.lower()
        if not word or key in seen or _resume_has_skill(resume, word):
            continue
        seen.add(key)
        missing.append(word)

    return missing[:10]


def _realistic_improvement_percent(
    ats_before: int,
    ats_tailored: int,
    alignment_score: int,
    plan_count: int,
) -> tuple[int, int, str]:
    """
    Cap projected ATS gain so we never imply fake skills will jump scores unrealistically.
    Returns (projected_ats_score, improvement_potential_percent, summary).
    """
    base = max(ats_before, ats_tailored)
    # Honest ceiling: tailored score + small bump from reordering/emphasis only
    plan_bonus = min(8, plan_count * 2)
    alignment_headroom = max(0, min(12, (alignment_score - base) // 4))
    projected = min(100, base + plan_bonus + alignment_headroom)
    potential = max(0, projected - ats_before)

    if potential <= 2:
        summary = (
            "Your resume already aligns well with this JD. Focus on phrasing and "
            "ordering existing experience rather than adding new skills."
        )
    elif potential <= 8:
        summary = (
            f"Realistic improvement of about {potential}% is possible by emphasizing "
            "skills you already have and tightening bullets for this role."
        )
    else:
        summary = (
            f"Up to ~{potential}% improvement may be achievable if you can truthfully "
            "add a few missing JD keywords you already use in practice."
        )

    return projected, potential, summary


def optimize_resume_for_job(
    resume: ResumeDocument,
    *,
    job_description: str,
    job_title: str = "",
    job_location: str = "",
    job_remote: bool = False,
) -> dict[str, Any]:
    """
    Analyze both JD and resume: gaps, genuine improvements, capped score projection.
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
    genuine_missing = _genuine_missing_skills(resume, alignment, keywords)

    optimization_plan: list[dict[str, str]] = []

    for skill in genuine_missing[:5]:
        optimization_plan.append({
            "type": "keyword",
            "action": (
                f"Add '{skill}' only if it appears in your real projects or work history"
            ),
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

    projected, potential_pct, improvement_summary = _realistic_improvement_percent(
        ats_before["ats_score"],
        ats_tailored["ats_score"],
        alignment["alignment_score"],
        len(optimization_plan),
    )

    return {
        "job_title": job_title,
        "alignment_score": alignment["alignment_score"],
        "ats_score_before": ats_before["ats_score"],
        "ats_score_tailored": ats_tailored["ats_score"],
        "projected_ats_score": projected,
        "improvement_potential_percent": potential_pct,
        "improvement_summary": improvement_summary,
        "genuine_missing_skills": genuine_missing,
        "optimization_plan": optimization_plan[:12],
        "alignment": alignment,
        "feedback": feedback,
        "keyword_analysis": keywords,
        "disclaimer": (
            "Suggestions compare your resume text to this job description. "
            "Only add skills and achievements you can demonstrate in interviews."
        ),
    }

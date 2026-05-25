"""Grounded job and career recommendations."""

from __future__ import annotations

from typing import Any


def build_recommendations(context: dict[str, Any]) -> dict[str, Any]:
    """Generate job, skill, resume, and career path recommendations from context."""
    jobs_ctx = context.get("jobs", {})
    market = context.get("market", {})
    resume = context.get("resume", {})
    skill_demand = market.get("skill_demand", {})

    job_recs = []
    for job in jobs_ctx.get("top_jobs", [])[:5]:
        if job.get("match_percentage", 0) >= 55:
            job_recs.append({
                "type": "job",
                "title": job["title"],
                "company": job["company"],
                "match_score": job["match_percentage"],
                "source": job["source"],
                "reasons": _job_reasons(job, resume),
            })

    skill_recs = []
    for item in (skill_demand.get("learning_priorities") or [])[:5]:
        skill_recs.append({
            "type": "skill",
            "skill": item.get("skill", ""),
            "priority": item.get("priority", "medium"),
            "demand_pct": item.get("demand_pct", 0),
            "reasons": [item.get("reason", "High market demand in your scan")],
        })

    missing = market.get("top_missing_skills") or []
    if missing and not skill_recs:
        for skill in missing[:4]:
            skill_recs.append({
                "type": "skill",
                "skill": skill,
                "priority": "high",
                "reasons": ["Frequently missing across your high-match job listings"],
            })

    resume_recs = []
    if resume.get("skill_count", 0) < 5:
        resume_recs.append({
            "type": "resume",
            "action": "Expand skills section",
            "reasons": ["Resume has fewer than 5 parsed skills — ATS matching may be limited"],
        })
    if jobs_ctx.get("avg_match", 0) < 50:
        resume_recs.append({
            "type": "resume",
            "action": "Tailor resume to top job keywords",
            "reasons": [
                f"Average match across scan is {jobs_ctx.get('avg_match', 0)}%",
                "Use Resume AI to align keywords with your top roles",
            ],
        })

    transitions = market.get("role_transitions", {})
    career_paths = [
        {
            "type": "career_path",
            "role": t.get("target_role", ""),
            "demand_score": t.get("market_demand_score", 0),
            "reasons": [t.get("reason", "")],
        }
        for t in (transitions.get("suggested_transitions") or [])[:4]
    ]

    return {
        "job_recommendations": job_recs,
        "skill_recommendations": skill_recs,
        "resume_recommendations": resume_recs,
        "career_path_suggestions": career_paths,
    }


def _job_reasons(job: dict[str, Any], resume: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if job.get("match_percentage", 0) >= 75:
        reasons.append(f"Strong {job['match_percentage']}% match with your profile")
    if job.get("matched_skills"):
        reasons.append(f"Matched skills: {', '.join(job['matched_skills'][:3])}")
    if job.get("remote"):
        reasons.append("Remote opportunity")
    if job.get("missing_skills"):
        reasons.append(f"Gap to close: {', '.join(job['missing_skills'][:2])}")
    if not reasons:
        reasons.append("Listed in your latest job scan")
    return reasons[:4]

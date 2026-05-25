"""Deterministic match explanations and career-fit insights."""

from __future__ import annotations

from typing import TypedDict

from app.utils.skills_master import TECH_STACK_GROUPS, categorize_skills

STRONG_MATCH_THRESHOLD = 75


class JobInsights(TypedDict):
    strengths: list[str]
    recommendations: list[str]
    experience_alignment: str
    career_fit: str
    why_match: list[str]


def _format_skill_list(skills: list[str], limit: int = 4) -> str:
    if not skills:
        return ""
    shown = skills[:limit]
    text = ", ".join(shown)
    if len(skills) > limit:
        text += f", +{len(skills) - limit} more"
    return text


def _stack_label(stack: str) -> str:
    labels = {
        "frontend": "frontend",
        "backend": "backend",
        "data": "data/storage",
        "cloud_devops": "cloud/DevOps",
        "ml": "ML/AI",
    }
    return labels.get(stack, stack)


def generate_job_insights(
    *,
    match_score: int,
    matched_skills: list[str],
    missing_skills: list[str],
    resume_skills: list[str],
    resume_keywords: list[str],
    job_title: str,
    job_description: str,
    job_remote: bool,
    job_location: str,
) -> JobInsights:
    strengths: list[str] = []
    recommendations: list[str] = []
    why_match: list[str] = []

    resume_groups = categorize_skills(resume_skills)
    job_text = f"{job_title} {job_description}".lower()
    resume_orientation = _infer_orientation(resume_skills)
    job_orientation = _infer_orientation_from_text(job_text)

    if matched_skills:
        top = _format_skill_list(matched_skills)
        strengths.append(f"Strong skill overlap with {top}.")
        why_match.append(f"{len(matched_skills)} required skills already on your resume")

    for group_name, skills in resume_groups.items():
        if not skills:
            continue
        job_group = TECH_STACK_GROUPS.get(group_name, [])
        if any(skill.lower() in job_text for skill in job_group):
            overlap = [s for s in skills if s.lower() in job_text]
            if overlap:
                label = _stack_label(group_name)
                strengths.append(
                    f"Strong {label} alignment with {_format_skill_list(overlap, 3)}."
                )
                why_match.append(f"{label.title()} experience detected in your profile")

    if missing_skills:
        top_missing = _format_skill_list(missing_skills, 3)
        recommendations.append(f"Upskill in {top_missing} to improve fit.")
        if len(missing_skills) == 1:
            strengths.append(f"Only one skill gap: {missing_skills[0]}.")

    if job_remote:
        why_match.append("Remote preference aligned with this role")
        strengths.append("Excellent fit for remote engineering roles.")

    seniority = _experience_alignment(resume_keywords, job_text)
    experience_alignment = seniority

    career_fit = _career_fit_summary(
        match_score=match_score,
        resume_orientation=resume_orientation,
        job_orientation=job_orientation,
        job_remote=job_remote,
        matched_count=len(matched_skills),
        missing_count=len(missing_skills),
    )

    if resume_orientation != job_orientation and resume_orientation != "generalist":
        if job_orientation == "frontend" and resume_orientation == "backend":
            recommendations.append(
                "Frontend-heavy role; your profile is backend-oriented — highlight API/UI integration experience."
            )
        elif job_orientation == "backend" and resume_orientation == "frontend":
            recommendations.append(
                "Backend-heavy role; emphasize any server-side or API work from your frontend background."
            )

    if match_score >= STRONG_MATCH_THRESHOLD and not strengths:
        strengths.append("High overall match based on combined skill and role signals.")

    if not recommendations and missing_skills:
        recommendations.append("Review the missing skills and add relevant projects to your resume.")

    if not why_match and matched_skills:
        why_match.append("Core technologies in the job description match your resume skills")

    return JobInsights(
        strengths=strengths[:5],
        recommendations=recommendations[:4],
        experience_alignment=experience_alignment,
        career_fit=career_fit,
        why_match=why_match[:5],
    )


def _infer_orientation(skills: list[str]) -> str:
    groups = categorize_skills(skills)
    frontend = len(groups.get("frontend", []))
    backend = len(groups.get("backend", []))
    if frontend and backend:
        return "fullstack"
    if backend > frontend:
        return "backend"
    if frontend > backend:
        return "frontend"
    return "generalist"


def _infer_orientation_from_text(text: str) -> str:
    frontend = sum(
        1 for hint in ("frontend", "front-end", "react", "angular", "vue", "ui engineer")
        if hint in text
    )
    backend = sum(
        1
        for hint in (
            "backend",
            "back-end",
            "api",
            "platform",
            "python",
            "node",
            "java",
            "devops",
        )
        if hint in text
    )
    if "full stack" in text or "fullstack" in text:
        return "fullstack"
    if backend > frontend:
        return "backend"
    if frontend > backend:
        return "frontend"
    return "generalist"


def _experience_alignment(resume_keywords: list[str], job_text: str) -> str:
    senior_signals = ("senior", "lead", "staff", "principal", "architect", "manager")
    junior_signals = ("junior", "entry", "intern", "graduate", "fresher")

    resume_senior = any(kw.lower() in senior_signals for kw in resume_keywords)
    resume_junior = any(kw.lower() in junior_signals for kw in resume_keywords)
    job_senior = any(sig in job_text for sig in senior_signals)
    job_junior = any(sig in job_text for sig in junior_signals)

    if resume_senior and job_senior:
        return "Seniority level aligns well with the role."
    if resume_junior and job_junior:
        return "Entry-level signals match this opportunity."
    if resume_senior and job_junior:
        return "You may be overqualified; role targets junior/entry level."
    if resume_junior and job_senior:
        return "Role expects senior experience; consider growing into lead skills."
    return "Experience level is broadly compatible with the role."


def _career_fit_summary(
    *,
    match_score: int,
    resume_orientation: str,
    job_orientation: str,
    job_remote: bool,
    matched_count: int,
    missing_count: int,
) -> str:
    if match_score >= 90:
        prefix = "Excellent career fit"
    elif match_score >= 75:
        prefix = "Strong career fit"
    elif match_score >= 50:
        prefix = "Moderate career fit"
    else:
        prefix = "Limited career fit"

    parts = [prefix]

    if resume_orientation == job_orientation:
        parts.append(f"for {job_orientation} engineering paths")
    elif resume_orientation != "generalist" and job_orientation != "generalist":
        parts.append(f"with some {resume_orientation}/{job_orientation} crossover")

    if job_remote:
        parts.append("in remote-friendly roles")

    if matched_count and missing_count == 0:
        parts.append("with full skill coverage")
    elif missing_count:
        parts.append(f"({missing_count} skill gap{'s' if missing_count > 1 else ''})")

    return " ".join(parts) + "."

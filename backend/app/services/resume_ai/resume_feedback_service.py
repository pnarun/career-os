"""Structured resume feedback — strengths, weaknesses, improvements."""

from __future__ import annotations

from typing import Any

from app.models.resume import ResumeDocument
from app.services.resume_ai._resume_utils import analyze_action_verbs, detect_sections
from app.services.resume_ai.ats_scoring_service import compute_ats_score
from app.services.resume_ai.keyword_optimizer import analyze_keywords
from app.services.resume_ai.section_analyzer import analyze_sections


def generate_resume_feedback(
    resume: ResumeDocument,
    *,
    job_description: str = "",
) -> dict[str, Any]:
    """Generate structured feedback without fabricating experience."""
    ats = compute_ats_score(resume, job_description=job_description)
    sections = analyze_sections(resume)
    keywords = analyze_keywords(resume, job_description=job_description)
    verbs = analyze_action_verbs(resume.raw_text)
    parsed_sections = detect_sections(resume.raw_text)

    strengths: list[str] = []
    weaknesses: list[str] = []
    improvements: list[str] = []
    high_impact: list[str] = []

    if resume.skills and len(resume.skills) >= 8:
        strengths.append(f"Strong skills section with {len(resume.skills)} listed technologies")
    if verbs["has_measurable_impact"]:
        strengths.append(f"Contains measurable outcomes ({verbs['metric_count']} quantified results)")
    if verbs["strong_verb_count"] >= 5:
        strengths.append("Good use of action verbs throughout experience bullets")

    for section, detail in sections["sections"].items():
        if detail.get("quality") == "strong":
            strengths.append(f"Strong {section} section with impact-driven bullets")
        elif detail.get("quality") == "missing":
            weaknesses.append(f"Missing {section} section — ATS parsers expect this")
            improvements.append(f"Add a dedicated {section.title()} section")

    if sections["missing_sections"]:
        for missing in sections["missing_sections"]:
            if missing not in [w.split()[1] for w in weaknesses]:
                weaknesses.append(f"Incomplete resume — no {missing} section detected")

    if verbs["weak_phrases"]:
        weaknesses.append(f"Weak phrasing detected ({len(verbs['weak_phrases'])} instances)")
        improvements.append("Replace passive phrases with action-led bullet points using your real work")

    if keywords["missing_keywords"]:
        top = keywords["missing_keywords"][:3]
        names = ", ".join(k["keyword"] for k in top)
        weaknesses.append(f"Missing keywords for target roles: {names}")
        improvements.append("Only add keywords you can honestly demonstrate in experience bullets")

    if ats["format_score"] < 70:
        weaknesses.append("Formatting may reduce ATS parse accuracy")
        improvements.append("Use simple headings, standard section names, and bullet points")

    if ats["ats_score"] < 60:
        high_impact.append("Add 2–3 quantified achievement bullets to your most recent role")
    if sections["low_impact_bullets"]:
        high_impact.append("Rewrite low-impact bullets with verbs + metrics from your actual results")
    if keywords["underrepresented_keywords"]:
        skill = keywords["underrepresented_keywords"][0]["keyword"]
        high_impact.append(f"Mention '{skill}' in an experience bullet where you used it")
    if not verbs["has_measurable_impact"]:
        high_impact.append("Add numbers where truthful: team size, latency reduction, users served, etc.")

    if parsed_sections and not strengths:
        strengths.append("Resume has structured content ready for optimization")

    return {
        "strengths": strengths[:8],
        "weaknesses": weaknesses[:8],
        "improvements": improvements[:8],
        "high_impact_changes": high_impact[:6],
        "ats_summary": {
            "ats_score": ats["ats_score"],
            "keyword_score": ats["keyword_score"],
            "format_score": ats["format_score"],
        },
    }

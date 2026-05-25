"""Generate role-focused resume variants from master resume."""

from __future__ import annotations

from typing import Any

from app.models.resume import ResumeDocument
from app.utils.skills_master import TECH_STACK_GROUPS, categorize_skills, extract_skills_from_text

VARIANT_PROFILES: dict[str, dict[str, Any]] = {
    "backend": {
        "label": "Backend Engineer",
        "focus_groups": ["backend", "data", "cloud_devops"],
        "title_keywords": ("backend", "api", "platform", "python", "java", "node"),
        "summary_hint": "Emphasize API design, system architecture, and backend services",
    },
    "fullstack": {
        "label": "Full Stack Engineer",
        "focus_groups": ["frontend", "backend", "data"],
        "title_keywords": ("full stack", "fullstack", "web", "react", "node"),
        "summary_hint": "Balance frontend and backend accomplishments equally",
    },
    "devops": {
        "label": "DevOps / Platform Engineer",
        "focus_groups": ["cloud_devops", "backend", "data"],
        "title_keywords": ("devops", "sre", "platform", "infrastructure", "cloud"),
        "summary_hint": "Highlight CI/CD, cloud infrastructure, and reliability work",
    },
    "ai_ml": {
        "label": "AI / ML Engineer",
        "focus_groups": ["ml", "data", "backend"],
        "title_keywords": ("machine learning", "ml", "ai", "data scientist", "deep learning"),
        "summary_hint": "Lead with ML projects, models, and data pipeline experience",
    },
}


def generate_resume_variants(resume: ResumeDocument) -> dict[str, Any]:
    """Generate variant profiles emphasizing different role tracks."""
    skills = resume.skills or extract_skills_from_text(resume.raw_text)
    categories = categorize_skills(skills)
    variants: list[dict[str, Any]] = []

    for variant_id, profile in VARIANT_PROFILES.items():
        focus_skills: list[str] = []
        for group in profile["focus_groups"]:
            focus_skills.extend(categories.get(group, []))

        match_score = _variant_fit_score(resume.raw_text, profile["title_keywords"], focus_skills)

        variants.append({
            "variant_id": variant_id,
            "label": profile["label"],
            "focus_skills": focus_skills[:12],
            "match_score": match_score,
            "summary_hint": profile["summary_hint"],
            "recommended_sections_order": _section_order(variant_id),
            "emphasis_recommendations": _emphasis_tips(variant_id, focus_skills, categories),
        })

    variants.sort(key=lambda v: v["match_score"], reverse=True)
    best = variants[0] if variants else None

    return {
        "variants": variants,
        "recommended_variant": best["variant_id"] if best else "fullstack",
        "master_skill_count": len(skills),
    }


def _variant_fit_score(raw_text: str, keywords: tuple[str, ...], focus_skills: list[str]) -> int:
    lower = raw_text.lower()
    keyword_hits = sum(1 for kw in keywords if kw in lower)
    skill_score = min(60, len(focus_skills) * 8)
    keyword_score = min(40, keyword_hits * 10)
    return min(100, skill_score + keyword_score)


def _section_order(variant_id: str) -> list[str]:
    base = ["Summary", "Skills", "Experience", "Projects", "Education", "Certifications"]
    if variant_id == "ai_ml":
        return ["Summary", "Skills", "Projects", "Experience", "Education", "Certifications"]
    if variant_id == "devops":
        return ["Summary", "Skills", "Experience", "Certifications", "Projects", "Education"]
    return base


def _emphasis_tips(
    variant_id: str,
    focus_skills: list[str],
    categories: dict[str, list[str]],
) -> list[str]:
    tips: list[str] = []
    if focus_skills:
        tips.append(f"Lead with: {', '.join(focus_skills[:5])}")
    missing_groups = [g for g in VARIANT_PROFILES[variant_id]["focus_groups"] if not categories.get(g)]
    for group in missing_groups[:2]:
        group_skills = TECH_STACK_GROUPS.get(group, [])[:3]
        if group_skills:
            tips.append(
                f"Strengthen {group.replace('_', ' ')} presence — relevant skills: {', '.join(group_skills)}"
            )
    tips.append("Reorder bullets to put most relevant accomplishments first")
    return tips[:4]

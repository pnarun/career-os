"""Interview AI — job description analysis utilities."""

from __future__ import annotations

import re
from typing import Any

from app.utils.skills_master import TECH_STACK_GROUPS, categorize_skills, extract_skills_from_text

LEADERSHIP_HINTS = (
    "lead",
    "mentor",
    "manage",
    "team",
    "stakeholder",
    "cross-functional",
    "architect",
    "ownership",
    "technical lead",
)

DEVOPS_HINTS = (
    "devops",
    "ci/cd",
    "kubernetes",
    "docker",
    "terraform",
    "aws",
    "azure",
    "gcp",
    "infrastructure",
    "sre",
    "deployment",
    "monitoring",
)

ARCHITECTURE_HINTS = (
    "microservices",
    "system design",
    "scalability",
    "distributed",
    "event-driven",
    "api design",
    "architecture",
    "high availability",
    "load balancing",
    "caching",
)

ROLE_PATTERNS: dict[str, tuple[str, ...]] = {
    "backend": ("backend", "back-end", "api", "python", "java", "node", "golang", "platform"),
    "frontend": ("frontend", "front-end", "react", "angular", "vue", "ui", "ux"),
    "fullstack": ("full stack", "fullstack", "full-stack"),
    "devops": ("devops", "sre", "platform engineer", "infrastructure", "cloud engineer"),
    "ai_ml": ("machine learning", "ml engineer", "data scientist", "ai ", "deep learning"),
}


def normalize_jd(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def extract_jd_topics(
    job_description: str,
    *,
    job_title: str = "",
) -> dict[str, Any]:
    """Extract technologies, concepts, and role emphasis from a job description."""
    combined = f"{job_title}\n{job_description}"
    lower = combined.lower()
    skills = extract_skills_from_text(combined)
    categories = categorize_skills(skills)

    technologies = skills
    frameworks = [s for s in skills if s in TECH_STACK_GROUPS.get("frontend", []) + TECH_STACK_GROUPS.get("backend", [])]
    databases = categories.get("data", [])
    cloud_tools = categories.get("cloud_devops", [])
    ml_tools = categories.get("ml", [])

    architecture = [hint for hint in ARCHITECTURE_HINTS if hint in lower]
    leadership = [hint for hint in LEADERSHIP_HINTS if hint in lower]
    devops_expectations = [hint for hint in DEVOPS_HINTS if hint in lower]

    role_emphasis = _detect_role_emphasis(lower, categories)

    return {
        "technologies": technologies[:20],
        "frameworks": frameworks[:15],
        "architecture_concepts": architecture[:10],
        "cloud_tools": cloud_tools[:10],
        "databases": databases[:10],
        "ml_tools": ml_tools[:8],
        "frontend_emphasis": len(categories.get("frontend", [])),
        "backend_emphasis": len(categories.get("backend", [])),
        "devops_emphasis": len(categories.get("cloud_devops", [])),
        "leadership_expectations": leadership[:6],
        "devops_expectations": devops_expectations[:6],
        "role_emphasis": role_emphasis,
        "primary_stack": _primary_stack(categories),
    }


def _detect_role_emphasis(lower: str, categories: dict[str, list[str]]) -> str:
    scores: dict[str, int] = {}
    for role, patterns in ROLE_PATTERNS.items():
        scores[role] = sum(2 for p in patterns if p in lower)
    for group, cat_key in (
        ("backend", "backend"),
        ("frontend", "frontend"),
        ("devops", "cloud_devops"),
        ("ai_ml", "ml"),
    ):
        scores[group] = scores.get(group, 0) + len(categories.get(cat_key, []))

    if not any(scores.values()):
        return "general"
    return max(scores, key=scores.get)


def _primary_stack(categories: dict[str, list[str]]) -> list[str]:
    ordered = ("backend", "frontend", "cloud_devops", "data", "ml")
    result: list[str] = []
    for group in ordered:
        result.extend(categories.get(group, [])[:4])
    return result[:12]

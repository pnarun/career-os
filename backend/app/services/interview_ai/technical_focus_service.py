"""Detect technical focus areas from job description."""

from __future__ import annotations

from typing import Any

from app.services.interview_ai._jd_utils import extract_jd_topics

FOCUS_LABELS = {
    "backend": "Backend Engineering",
    "frontend": "Frontend Development",
    "fullstack": "Full Stack Engineering",
    "devops": "DevOps / Cloud Infrastructure",
    "ai_ml": "AI / Machine Learning",
    "general": "General Software Engineering",
}

PREP_AREAS: dict[str, list[str]] = {
    "backend": [
        "REST API design & implementation",
        "Database modeling & query optimization",
        "Authentication & authorization patterns",
        "Caching & performance tuning",
        "Error handling & observability",
    ],
    "frontend": [
        "Component architecture & state management",
        "Performance optimization (Core Web Vitals)",
        "Accessibility & responsive design",
        "API integration patterns",
        "Testing (unit, integration, E2E)",
    ],
    "fullstack": [
        "End-to-end feature delivery",
        "API + UI integration",
        "Database + frontend data flow",
        "Deployment & CI/CD basics",
        "System trade-offs across stack",
    ],
    "devops": [
        "Container orchestration (Docker/K8s)",
        "CI/CD pipeline design",
        "Cloud services (AWS/GCP/Azure)",
        "Infrastructure as Code",
        "Monitoring, logging & incident response",
    ],
    "ai_ml": [
        "ML model lifecycle & evaluation",
        "Feature engineering & data pipelines",
        "Model deployment & serving",
        "Statistics & experimentation",
        "Python ML ecosystem (pandas, sklearn, etc.)",
    ],
    "general": [
        "Data structures & algorithms fundamentals",
        "System design basics",
        "Version control & collaboration",
        "Testing & code quality",
        "Problem-solving approach",
    ],
}


def analyze_technical_focus(
    job_description: str,
    *,
    job_title: str = "",
) -> dict[str, Any]:
    topics = extract_jd_topics(job_description, job_title=job_title)
    emphasis = topics["role_emphasis"]
    label = FOCUS_LABELS.get(emphasis, FOCUS_LABELS["general"])
    areas = list(PREP_AREAS.get(emphasis, PREP_AREAS["general"]))

    tech_priorities: list[dict[str, str]] = []
    for skill in topics.get("primary_stack", [])[:8]:
        tech_priorities.append({
            "topic": skill,
            "priority": "high",
            "reason": f"Listed in job requirements for {label}",
        })

    for concept in topics.get("architecture_concepts", [])[:4]:
        tech_priorities.append({
            "topic": concept.title(),
            "priority": "medium",
            "reason": "Architecture concept mentioned in JD",
        })

    return {
        "focus_type": emphasis,
        "focus_label": label,
        "prioritized_areas": areas,
        "tech_priorities": tech_priorities[:12],
        "frontend_heavy": topics["frontend_emphasis"] > topics["backend_emphasis"],
        "backend_heavy": topics["backend_emphasis"] > topics["frontend_emphasis"],
        "cloud_heavy": topics["devops_emphasis"] >= 3,
        "leadership_expected": len(topics.get("leadership_expectations", [])) > 0,
    }

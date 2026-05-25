"""Multi-day interview preparation plan generator."""

from __future__ import annotations

from typing import Any

from app.services.interview_ai.coding_topic_mapper import map_coding_topics
from app.services.interview_ai.technical_focus_service import analyze_technical_focus


def generate_preparation_plan(
    job_description: str,
    *,
    job_title: str = "",
    days: int = 5,
) -> dict[str, Any]:
    focus = analyze_technical_focus(job_description, job_title=job_title)
    coding = map_coding_topics(job_description, job_title=job_title)
    stack = focus.get("tech_priorities", [])[:3]
    stack_labels = [t["topic"] for t in stack] if stack else ["Core stack review"]

    day_templates = [
        {
            "day": 1,
            "title": f"Core stack — {stack_labels[0] if stack_labels else 'Fundamentals'}",
            "tasks": [
                f"Review {stack_labels[0] if stack_labels else 'primary language'} concepts from JD",
                "Practice 2 technical questions on core stack",
                "Re-read job description and highlight key requirements",
            ],
            "duration_hours": 2,
        },
        {
            "day": 2,
            "title": f"Deep dive — {stack_labels[1] if len(stack_labels) > 1 else 'Databases & APIs'}",
            "tasks": [
                "Study database/API patterns mentioned in JD",
                "Complete 1 SQL or API design exercise",
                "Write bullet notes on past projects matching JD skills",
            ],
            "duration_hours": 2,
        },
        {
            "day": 3,
            "title": "System design & architecture",
            "tasks": [
                f"Practice: {coding['system_design_topics'][0] if coding.get('system_design_topics') else 'Design a scalable API'}",
                "Review architecture concepts from JD",
                "Draw a diagram for a past project you can discuss",
            ],
            "duration_hours": 2.5,
        },
        {
            "day": 4,
            "title": "Behavioral preparation",
            "tasks": [
                "Prepare 4 STAR stories (conflict, failure, leadership, impact)",
                "Practice answers out loud (2 min each)",
                "Map resume bullets to likely behavioral questions",
            ],
            "duration_hours": 1.5,
        },
        {
            "day": 5,
            "title": "Mock interview & review",
            "tasks": [
                "Run a timed mock interview session in Career OS",
                "Review weak areas from readiness score",
                "Prepare 3 thoughtful questions to ask the interviewer",
            ],
            "duration_hours": 2,
        },
    ]

    if focus.get("cloud_heavy"):
        day_templates[2]["tasks"].insert(0, "Review cloud/DevOps topics from JD")

    plan_days = day_templates[: max(1, min(days, len(day_templates)))]

    return {
        "job_title": job_title,
        "focus_label": focus["focus_label"],
        "total_days": len(plan_days),
        "estimated_hours": sum(d["duration_hours"] for d in plan_days),
        "days": plan_days,
    }

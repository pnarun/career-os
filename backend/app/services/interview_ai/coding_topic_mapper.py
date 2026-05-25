"""Map job description to coding & system design preparation topics."""

from __future__ import annotations

from typing import Any

from app.services.interview_ai._jd_utils import extract_jd_topics

DSA_BY_ROLE: dict[str, list[str]] = {
    "backend": ["Arrays & Hash Maps", "Trees & Graphs", "Heaps", "Dynamic Programming (basics)", "String manipulation"],
    "frontend": ["Arrays", "Trees (DOM-like)", "Recursion", "Sliding window", "Two pointers"],
    "fullstack": ["Arrays & Hash Maps", "Trees", "Graphs (basics)", "System design lite", "SQL joins"],
    "devops": ["Scripting logic", "Log parsing", "Concurrency basics", "Networking fundamentals"],
    "ai_ml": ["Arrays & Matrices", "Probability basics", "Optimization", "Graph algorithms"],
    "general": ["Arrays", "Hash Maps", "Trees", "Sorting", "Binary search"],
}

SYSTEM_DESIGN_BY_ROLE: dict[str, list[str]] = {
    "backend": ["URL shortener", "Rate limiter", "Notification system", "Chat backend", "API gateway patterns"],
    "frontend": ["Component design system", "Real-time dashboard", "Infinite scroll feed", "State architecture"],
    "fullstack": ["Job board", "E-commerce checkout", "Collaborative editor", "Analytics dashboard"],
    "devops": ["CI/CD pipeline", "Multi-region deployment", "Observability stack", "Auto-scaling service"],
    "ai_ml": ["Recommendation engine", "ML inference pipeline", "Feature store", "A/B testing platform"],
    "general": ["Todo app at scale", "Paste bin", "News feed", "Parking lot system"],
}

SQL_TOPICS = [
    "JOINs (INNER, LEFT, RIGHT)",
    "Indexing & query plans",
    "Aggregations & GROUP BY",
    "Transactions & isolation levels",
    "Normalization vs denormalization",
]

CONCURRENCY_TOPICS = [
    "Threading vs multiprocessing",
    "Async/await patterns",
    "Race conditions & locks",
    "Message queues",
    "Event-driven architecture",
]

API_TOPICS = [
    "REST design principles",
    "Authentication (JWT, OAuth)",
    "Versioning strategies",
    "Pagination & filtering",
    "Error handling conventions",
]


def map_coding_topics(
    job_description: str,
    *,
    job_title: str = "",
) -> dict[str, Any]:
    topics = extract_jd_topics(job_description, job_title=job_title)
    role = topics["role_emphasis"]

    dsa = list(DSA_BY_ROLE.get(role, DSA_BY_ROLE["general"]))
    system_design = list(SYSTEM_DESIGN_BY_ROLE.get(role, SYSTEM_DESIGN_BY_ROLE["general"]))

    suggested: list[dict[str, str]] = []
    for topic in dsa[:5]:
        suggested.append({"category": "dsa", "topic": topic, "priority": "high"})
    for topic in system_design[:4]:
        suggested.append({"category": "system_design", "topic": topic, "priority": "high"})

    if topics.get("databases"):
        for topic in SQL_TOPICS[:3]:
            suggested.append({"category": "sql", "topic": topic, "priority": "medium"})

    if role in ("backend", "fullstack", "devops"):
        for topic in CONCURRENCY_TOPICS[:3]:
            suggested.append({"category": "concurrency", "topic": topic, "priority": "medium"})

    if role in ("backend", "fullstack"):
        for topic in API_TOPICS[:3]:
            suggested.append({"category": "api_design", "topic": topic, "priority": "medium"})

    return {
        "role_emphasis": role,
        "dsa_topics": dsa,
        "system_design_topics": system_design,
        "sql_topics": SQL_TOPICS if topics.get("databases") else SQL_TOPICS[:2],
        "concurrency_topics": CONCURRENCY_TOPICS if role in ("backend", "devops", "fullstack") else [],
        "api_design_topics": API_TOPICS if role in ("backend", "fullstack") else [],
        "suggested_topics": suggested[:15],
    }

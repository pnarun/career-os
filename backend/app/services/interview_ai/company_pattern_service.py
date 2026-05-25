"""Rule-based company and role interview pattern analysis."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.services.interview_ai._jd_utils import extract_jd_topics

COMPANY_PATTERNS: dict[str, dict[str, Any]] = {
    "startup": {
        "topics": ["Full-stack breadth", "Ownership", "Fast iteration", "System design lite"],
        "emphasis": "generalist_with_depth",
    },
    "enterprise": {
        "topics": ["Scalability", "Security", "Process", "Cross-team collaboration"],
        "emphasis": "depth_and_process",
    },
    "product": {
        "topics": ["User impact", "A/B testing", "Metrics", "Product sense"],
        "emphasis": "impact_driven",
    },
}

ROLE_TRENDS: dict[str, list[str]] = {
    "backend": ["API design", "Database optimization", "Concurrency", "Caching", "Microservices"],
    "frontend": ["React patterns", "Performance", "Accessibility", "State management", "Testing"],
    "devops": ["CI/CD", "Kubernetes", "Cloud architecture", "IaC", "Incident response"],
    "ai_ml": ["ML pipelines", "Model evaluation", "Feature engineering", "Statistics", "Deployment"],
    "fullstack": ["End-to-end features", "API + UI", "Database design", "Deployment", "Trade-offs"],
}


def analyze_company_patterns(
    *,
    company: str = "",
    job_title: str = "",
    job_description: str = "",
    market_jobs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    topics = extract_jd_topics(job_description, job_title=job_title)
    role = topics["role_emphasis"]

    company_lower = company.lower()
    company_type = "startup"
    if any(w in company_lower for w in ("google", "amazon", "microsoft", "meta", "apple", "accenture", "tcs", "infosys")):
        company_type = "enterprise"
    elif any(w in company_lower for w in ("labs", "ai", "data")):
        company_type = "product"

    pattern = COMPANY_PATTERNS.get(company_type, COMPANY_PATTERNS["startup"])
    role_trends = ROLE_TRENDS.get(role, ROLE_TRENDS["fullstack"])

    market_topics: Counter[str] = Counter()
    if market_jobs and company:
        for job in market_jobs:
            if company_lower in job.get("company", "").lower():
                for skill in job.get("technologies", []) or []:
                    market_topics[skill] += 1

    frequent_topics = [t for t, _ in market_topics.most_common(6)] if market_topics else role_trends[:5]

    return {
        "company": company,
        "company_type": company_type,
        "role_emphasis": role,
        "frequent_topics": frequent_topics,
        "role_specific_emphasis": role_trends,
        "interview_trends": pattern["topics"],
        "preparation_focus": pattern["emphasis"],
        "likely_technical_areas": topics.get("primary_stack", [])[:6],
    }

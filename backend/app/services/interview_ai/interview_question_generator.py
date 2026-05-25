"""Generate interview questions from JD, resume, and role focus."""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.interview_ai._jd_utils import extract_jd_topics
from app.services.interview_ai.behavioral_analyzer import analyze_behavioral_focus
from app.services.interview_ai.technical_focus_service import analyze_technical_focus

TECH_QUESTION_BANK: dict[str, list[str]] = {
    "Python": [
        "Explain Python's GIL and when it matters for your applications.",
        "How do you structure a FastAPI project for maintainability?",
        "Difference between async/await and threading in Python?",
    ],
    "FastAPI": [
        "Explain FastAPI dependency injection and its benefits.",
        "How do you handle authentication in FastAPI?",
        "How would you structure background tasks vs Celery workers?",
    ],
    "MongoDB": [
        "How would you optimize slow MongoDB queries?",
        "When would you embed vs reference documents?",
        "Explain indexing strategy for a high-read collection.",
    ],
    "React": [
        "Explain React state management options and when to use each.",
        "How do you prevent unnecessary re-renders?",
        "Describe your approach to component testing.",
    ],
    "Docker": [
        "Explain multi-stage Docker builds and why they matter.",
        "How do you debug a failing container in production?",
        "Docker Compose vs Kubernetes — when to use each?",
    ],
    "Kubernetes": [
        "Explain pods, services, and deployments.",
        "How do you handle rolling updates with zero downtime?",
        "What is a liveness vs readiness probe?",
    ],
    "AWS": [
        "Explain common AWS services you'd use for a web API.",
        "How do you design for high availability on AWS?",
        "S3 vs EBS — use cases for each?",
    ],
    "Node.js": [
        "Explain the Node.js event loop.",
        "How do you handle errors in async Express handlers?",
        "When would you use worker threads?",
    ],
    "PostgreSQL": [
        "Explain indexing and when a query might not use an index.",
        "Difference between INNER and LEFT JOIN with examples.",
        "How do you approach schema migrations safely?",
    ],
    "REST API": [
        "Design a REST API for a job application tracker.",
        "How do you version APIs without breaking clients?",
        "Idempotency — why does it matter for POST/PUT?",
    ],
    "Machine Learning": [
        "Walk through an ML project from data to deployment.",
        "How do you detect and handle model drift?",
        "Bias vs variance — practical implications?",
    ],
}

SYSTEM_DESIGN_PROMPTS = [
    "Design a real-time job notification system for 100k users.",
    "How would you build a rate-limited public API?",
    "Design a resume parsing pipeline at scale.",
    "Architect a multi-tenant SaaS backend with tenant isolation.",
    "Design a browser automation system with session management.",
]

PROJECT_PROMPTS = [
    "Walk me through a recent project end-to-end: problem, architecture, trade-offs, outcome.",
    "What was the hardest technical decision in your last project?",
    "How did you ensure reliability and observability in production?",
]


def generate_questions(
    job_description: str,
    *,
    job_title: str = "",
    resume_text: str = "",
    resume_skills: list[str] | None = None,
) -> dict[str, Any]:
    topics = extract_jd_topics(job_description, job_title=job_title)
    focus = analyze_technical_focus(job_description, job_title=job_title)
    behavioral = analyze_behavioral_focus(job_description, job_title=job_title, resume_text=resume_text)

    technical: list[dict[str, str]] = []
    for skill in topics.get("technologies", [])[:10]:
        bank = TECH_QUESTION_BANK.get(skill, [])
        if bank:
            for q in bank[:2]:
                technical.append({"question": q, "topic": skill, "category": "technical"})
        else:
            technical.append({
                "question": f"Explain your experience with {skill} and a challenging problem you solved using it.",
                "topic": skill,
                "category": "technical",
            })

    for skill in (resume_skills or [])[:5]:
        if skill not in topics.get("technologies", []):
            bank = TECH_QUESTION_BANK.get(skill, [])
            if bank:
                technical.append({"question": bank[0], "topic": skill, "category": "resume_technical"})

    system_design = [
        {"question": q, "topic": "system_design", "category": "system_design"}
        for q in SYSTEM_DESIGN_PROMPTS[:3]
    ]

    project_based = [
        {"question": q, "topic": "projects", "category": "project"}
        for q in PROJECT_PROMPTS
    ]

    resume_based = [
        {
            "question": q["question"],
            "topic": q.get("theme", "resume"),
            "category": "resume_based",
        }
        for q in behavioral.get("resume_based_questions", [])
    ]

    behavioral_qs = [
        {
            "question": q["question"],
            "topic": q["theme"],
            "category": "behavioral",
            "tip": q.get("tip", ""),
        }
        for q in behavioral.get("recommended_questions", [])
    ]

    return {
        "technical_questions": technical[:12],
        "behavioral_questions": behavioral_qs[:8],
        "system_design_prompts": system_design,
        "project_questions": project_based,
        "resume_based_questions": resume_based,
        "focus_label": focus["focus_label"],
        "question_source": "static",
        "total_count": len(technical) + len(behavioral_qs) + len(system_design) + len(project_based) + len(resume_based),
    }


def _to_question_item(entry: dict[str, str]) -> dict[str, str]:
    return {
        "question": entry.get("question", ""),
        "topic": entry.get("topic", "web"),
        "category": entry.get("category", "technical"),
        "tip": entry.get("tip", ""),
        "source": entry.get("source", ""),
    }


def merge_web_and_static_questions(
    static: dict[str, Any],
    web: dict[str, Any],
) -> dict[str, Any]:
    """Prefer web-fetched job-specific questions; fill gaps from static bank."""
    if not web.get("total_found"):
        static["question_source"] = "static"
        return static

    def _merge_category(web_key: str, static_key: str, limit: int) -> list[dict[str, str]]:
        merged: list[dict[str, str]] = []
        seen: set[str] = set()
        for entry in web.get(web_key, []) + static.get(static_key, []):
            q = entry.get("question", "") if isinstance(entry, dict) else str(entry)
            key = q.lower().strip()
            if not q or key in seen:
                continue
            seen.add(key)
            merged.append(_to_question_item(entry if isinstance(entry, dict) else {"question": q}))
            if len(merged) >= limit:
                break
        return merged

    technical = _merge_category("technical_questions", "technical_questions", 12)
    behavioral = _merge_category("behavioral_questions", "behavioral_questions", 8)
    system_design = _merge_category("system_design_prompts", "system_design_prompts", 5)

    # Resume-based and project questions stay static (personalized to user)
    project = [_to_question_item(q) for q in static.get("project_questions", [])]
    resume_based = [_to_question_item(q) for q in static.get("resume_based_questions", [])]

    total = len(technical) + len(behavioral) + len(system_design) + len(project) + len(resume_based)

    return {
        "technical_questions": technical,
        "behavioral_questions": behavioral,
        "system_design_prompts": system_design,
        "project_questions": project,
        "resume_based_questions": resume_based,
        "focus_label": static.get("focus_label", ""),
        "question_source": web.get("source", "web"),
        "web_pages_fetched": web.get("pages_fetched", 0),
        "total_count": total,
    }


async def generate_questions_with_web(
    job_description: str,
    *,
    job_id: str = "",
    job_title: str = "",
    company: str = "",
    resume_text: str = "",
    resume_skills: list[str] | None = None,
) -> dict[str, Any]:
    """Generate questions: web search first, static bank as fallback."""
    from app.services.interview_ai.web_question_service import fetch_web_interview_questions

    static = generate_questions(
        job_description,
        job_title=job_title,
        resume_text=resume_text,
        resume_skills=resume_skills,
    )

    topics = extract_jd_topics(job_description, job_title=job_title)
    skills = topics.get("technologies", []) + (resume_skills or [])

    if not settings.INTERVIEW_WEB_QUESTIONS_ENABLED:
        static["question_source"] = "static"
        return static

    try:
        web = await fetch_web_interview_questions(
            job_id=job_id,
            job_title=job_title,
            company=company,
            skills=skills[:10],
        )
    except Exception:
        static["question_source"] = "static"
        return static

    return merge_web_and_static_questions(static, web)

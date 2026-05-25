"""Interview readiness scoring."""

from __future__ import annotations

from typing import Any

from app.models.resume import ResumeDocument
from app.services.interview_ai.behavioral_analyzer import analyze_behavioral_focus
from app.services.interview_ai.coding_topic_mapper import map_coding_topics
from app.services.interview_ai.interview_question_generator import generate_questions
from app.services.interview_ai.technical_focus_service import analyze_technical_focus
from app.utils.skills_master import extract_skills_from_text


def compute_readiness(
    job_description: str,
    *,
    job_title: str = "",
    resume: ResumeDocument | None = None,
    practiced_count: int = 0,
    completed_topics: int = 0,
) -> dict[str, Any]:
    resume_text = resume.raw_text if resume else ""
    resume_skills = resume.skills if resume else []

    focus = analyze_technical_focus(job_description, job_title=job_title)
    coding = map_coding_topics(job_description, job_title=job_title)
    behavioral = analyze_behavioral_focus(job_description, job_title=job_title, resume_text=resume_text)
    questions = generate_questions(
        job_description,
        job_title=job_title,
        resume_text=resume_text,
        resume_skills=resume_skills,
    )

    job_skills = set(s.lower() for s in extract_skills_from_text(job_description))
    resume_skill_set = set(s.lower() for s in resume_skills) | set(
        s.lower() for s in extract_skills_from_text(resume_text)
    )

    skill_overlap = len(job_skills & resume_skill_set) / max(len(job_skills), 1)
    technical_readiness = int(min(100, skill_overlap * 70 + len(resume_skills) * 1.5 + completed_topics * 3))
    behavioral_readiness = int(
        min(100, 50 + len(behavioral.get("resume_based_questions", [])) * 8 + practiced_count * 2)
    )
    system_design_readiness = int(
        min(100, 40 + len(coding.get("system_design_topics", [])) * 5 + completed_topics * 4)
    )

    readiness_score = int(
        technical_readiness * 0.45
        + behavioral_readiness * 0.30
        + system_design_readiness * 0.25
    )

    weak_areas: list[str] = []
    if skill_overlap < 0.5:
        missing = job_skills - resume_skill_set
        weak_areas.extend(f"Review: {s.title()}" for s in list(missing)[:4])
    if not behavioral.get("resume_based_questions"):
        weak_areas.append("Prepare STAR stories from your resume projects")
    if system_design_readiness < 60:
        weak_areas.append("Practice system design for role-relevant scenarios")

    topic_confidence = _topic_confidence(coding, resume_skill_set, job_skills)

    return {
        "readiness_score": readiness_score,
        "technical_readiness": technical_readiness,
        "behavioral_readiness": behavioral_readiness,
        "system_design_readiness": system_design_readiness,
        "focus_label": focus["focus_label"],
        "weak_areas": weak_areas[:6],
        "topic_confidence": topic_confidence,
        "question_count": questions["total_count"],
    }


def _topic_confidence(
    coding: dict[str, Any],
    resume_skills: set[str],
    job_skills: set[str],
) -> list[dict[str, Any]]:
    bars: list[dict[str, Any]] = []
    for item in coding.get("suggested_topics", [])[:8]:
        topic_lower = item["topic"].lower()
        matched = any(
            js in topic_lower or topic_lower in js
            for js in resume_skills | job_skills
        )
        base = 75 if matched else 45
        bars.append({
            "topic": item["topic"],
            "category": item["category"],
            "confidence": min(100, base + (10 if item["priority"] == "high" else 0)),
        })
    return bars

"""Behavioral interview question analysis and generation."""

from __future__ import annotations

import re
from typing import Any

BEHAVIORAL_TEMPLATES: list[dict[str, str]] = [
    {
        "question": "Tell me about a production issue you solved and what you learned.",
        "theme": "problem_solving",
        "tip": "Use STAR: Situation, Task, Action, Result — focus on your specific contribution.",
    },
    {
        "question": "Describe a difficult debugging experience and how you approached it.",
        "theme": "technical_depth",
        "tip": "Show systematic debugging: hypothesis, logs, reproduction, fix, prevention.",
    },
    {
        "question": "How do you handle tight deadlines while maintaining code quality?",
        "theme": "time_management",
        "tip": "Mention prioritization, communication with stakeholders, and technical debt trade-offs.",
    },
    {
        "question": "Tell me about a time you disagreed with a teammate. How did you resolve it?",
        "theme": "collaboration",
        "tip": "Emphasize empathy, data-driven discussion, and team outcome over being right.",
    },
    {
        "question": "Describe a project where you took ownership beyond your role.",
        "theme": "leadership",
        "tip": "Highlight initiative, impact metrics, and cross-team coordination.",
    },
    {
        "question": "Tell me about a mistake you made. What did you do afterward?",
        "theme": "accountability",
        "tip": "Be honest, focus on remediation, postmortem, and process improvements.",
    },
    {
        "question": "How do you stay current with new technologies?",
        "theme": "growth",
        "tip": "Mention learning habits, side projects, docs, and applying new skills at work.",
    },
    {
        "question": "Describe working with non-technical stakeholders on a complex feature.",
        "theme": "communication",
        "tip": "Show how you translated technical constraints into business language.",
    },
]

LEADERSHIP_JD_HINTS = ("lead", "senior", "staff", "principal", "manager", "mentor", "architect")


def analyze_behavioral_focus(
    job_description: str,
    *,
    job_title: str = "",
    resume_text: str = "",
) -> dict[str, Any]:
    combined = f"{job_title} {job_description}".lower()
    leadership_focus = any(h in combined for h in LEADERSHIP_JD_HINTS)

    questions = list(BEHAVIORAL_TEMPLATES)
    if leadership_focus:
        questions = [q for q in questions if q["theme"] in ("leadership", "collaboration", "communication", "accountability")]
        questions.extend(BEHAVIORAL_TEMPLATES[:2])

    resume_questions = _resume_behavioral_questions(resume_text)

    themes = list({q["theme"] for q in questions})

    return {
        "leadership_focus": leadership_focus,
        "recommended_questions": questions[:8],
        "resume_based_questions": resume_questions[:5],
        "key_themes": themes,
        "preparation_tips": [
            "Prepare 4–6 STAR stories covering different themes",
            "Quantify impact where possible (latency, users, revenue, time saved)",
            "Practice concise 2-minute answers",
            "Never blame former teammates — focus on your actions",
        ],
    }


def _resume_behavioral_questions(resume_text: str) -> list[dict[str, str]]:
    if not resume_text or len(resume_text) < 100:
        return []

    questions: list[dict[str, str]] = []
    lines = [ln.strip() for ln in resume_text.splitlines() if len(ln.strip()) > 20]

    for line in lines[:15]:
        if re.search(r"\b(led|built|designed|implemented|migrated|scaled)\b", line, re.I):
            snippet = line[:80] + ("…" if len(line) > 80 else "")
            questions.append({
                "question": f"Walk me through this experience from your resume: \"{snippet}\"",
                "theme": "resume_based",
                "tip": "Explain context, your role, technical decisions, and measurable outcome.",
            })
        if len(questions) >= 5:
            break

    return questions

"""Mock interview session — ethical practice only, no live assistance."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone
from typing import Any

from app.services.interview_ai.behavioral_analyzer import BEHAVIORAL_TEMPLATES
from app.services.interview_ai.interview_question_generator import (
    SYSTEM_DESIGN_PROMPTS,
    TECH_QUESTION_BANK,
    generate_questions,
)

MOCK_ROUNDS = {
    "technical": {"label": "Technical Round", "time_limit_sec": 300, "question_count": 5},
    "behavioral": {"label": "HR / Behavioral Round", "time_limit_sec": 180, "question_count": 4},
    "system_design": {"label": "System Design Round", "time_limit_sec": 900, "question_count": 2},
    "mixed": {"label": "Mixed Round", "time_limit_sec": 600, "question_count": 6},
}


def start_mock_session(
    job_description: str,
    *,
    job_title: str = "",
    resume_text: str = "",
    category: str = "mixed",
    seed: int | None = None,
) -> dict[str, Any]:
    """Start a mock interview with random questions — practice only."""
    rng = random.Random(seed)
    session_id = str(uuid.uuid4())
    round_config = MOCK_ROUNDS.get(category, MOCK_ROUNDS["mixed"])

    pool: list[dict[str, Any]] = []
    generated = generate_questions(job_description, job_title=job_title, resume_text=resume_text)

    if category in ("technical", "mixed"):
        pool.extend(generated.get("technical_questions", []))
    if category in ("behavioral", "mixed"):
        pool.extend(generated.get("behavioral_questions", []))
    if category in ("system_design", "mixed"):
        pool.extend(generated.get("system_design_prompts", []))

    if not pool:
        for bank in TECH_QUESTION_BANK.values():
            pool.extend({"question": q, "category": "technical", "topic": "general"} for q in bank[:1])
        pool.extend(
            {"question": b["question"], "category": "behavioral", "topic": b["theme"]}
            for b in BEHAVIORAL_TEMPLATES[:3]
        )

    rng.shuffle(pool)
    selected = pool[: round_config["question_count"]]

    questions = [
        {
            "id": f"q-{i + 1}",
            "question": q["question"],
            "category": q.get("category", category),
            "topic": q.get("topic", ""),
            "time_limit_sec": round_config["time_limit_sec"] // max(len(selected), 1),
        }
        for i, q in enumerate(selected)
    ]

    return {
        "session_id": session_id,
        "category": category,
        "round_label": round_config["label"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": len(questions),
        "questions": questions,
        "disclaimer": "Practice mode only — not for use during live interviews.",
    }


def get_random_practice_question(category: str = "mixed", seed: int | None = None) -> dict[str, str]:
    rng = random.Random(seed)
    if category == "behavioral":
        item = rng.choice(BEHAVIORAL_TEMPLATES)
        return {"question": item["question"], "category": "behavioral", "tip": item.get("tip", "")}
    if category == "system_design":
        return {"question": rng.choice(SYSTEM_DESIGN_PROMPTS), "category": "system_design", "tip": "Think aloud: requirements, scale, components, trade-offs."}
    all_tech = [q for bank in TECH_QUESTION_BANK.values() for q in bank]
    return {"question": rng.choice(all_tech), "category": "technical", "tip": "Explain concept, trade-offs, and a real example from your experience."}

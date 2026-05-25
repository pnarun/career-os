"""Route copilot intents to grounded advisor services."""

from __future__ import annotations

import re
from typing import Any

from app.services.copilot.application_strategy_service import advise_application_strategy
from app.services.copilot.interview_advisor import advise_interview
from app.services.copilot.market_reasoning_service import reason_about_market
from app.services.copilot.opportunity_advisor import advise_opportunities
from app.services.copilot.recommendation_engine import build_recommendations
from app.services.copilot.skill_advisor import advise_skills
from app.services.copilot.user_context_builder import build_user_context


INTENT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("opportunities", re.compile(r"best job|fit me|matches|opportunit|which job|recommend job", re.I)),
    ("match_score", re.compile(r"match score|why.*low|low match|improve match", re.I)),
    ("skills", re.compile(r"skill|learn|roi|what should i learn", re.I)),
    ("interviews", re.compile(r"interview|not getting|response|reject", re.I)),
    ("providers", re.compile(r"provider|linkedin|indeed|naukri|source", re.I)),
    ("career_path", re.compile(r"backend|devops|full stack|career path|focus on|transition", re.I)),
    ("resume", re.compile(r"resume|ats|variant|tailor", re.I)),
    ("market", re.compile(r"market|trend|salary|demand|remote", re.I)),
    ("strategy", re.compile(r"apply|strategy|priorit|follow up|when to", re.I)),
]


def detect_intent(message: str) -> str:
    text = message.strip()
    for name, pattern in INTENT_PATTERNS:
        if pattern.search(text):
            return name
    return "general"


async def route_copilot_query(message: str) -> dict[str, Any]:
    """Build context, detect intent, and return grounded advisor payload."""
    context = await build_user_context()
    intent = detect_intent(message)
    recommendations = build_recommendations(context)

    payload: dict[str, Any] = {
        "intent": intent,
        "context_summary": _context_summary(context),
        "recommendations": recommendations,
    }

    if intent in ("opportunities", "general"):
        payload["opportunities"] = advise_opportunities(context)
    if intent in ("skills", "general", "resume"):
        payload["skills"] = advise_skills(context)
    if intent in ("interviews", "general", "strategy"):
        payload["interview"] = advise_interview(context)
    if intent in ("strategy", "interviews", "providers", "general"):
        payload["application_strategy"] = advise_application_strategy(context)
    if intent in ("market", "career_path", "skills", "general"):
        payload["market"] = reason_about_market(context)
    if intent == "match_score":
        payload["match_explanation"] = _explain_match_score(context)
    if intent == "providers":
        payload["providers"] = context.get("market", {}).get("provider_performance", {})
    if intent == "career_path":
        payload["career_paths"] = context.get("market", {}).get("role_transitions", {})

    return payload


def _context_summary(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "resume_skills": len(context.get("resume", {}).get("skills", [])),
        "jobs_in_scan": context.get("jobs", {}).get("total", 0),
        "avg_match": context.get("jobs", {}).get("avg_match", 0),
        "applications": context.get("applications", {}).get("total", 0),
        "growth_score": context.get("market", {}).get("growth_score", 0),
        "primary_role": context.get("market", {}).get("primary_role", ""),
    }


def _explain_match_score(context: dict[str, Any]) -> dict[str, Any]:
    jobs_ctx = context.get("jobs", {})
    avg = jobs_ctx.get("avg_match", 0)
    reasons: list[str] = []

    if avg < 50:
        reasons.append(f"Average match across your scan is {avg}% — resume keywords may not align with job descriptions.")
    elif avg < 70:
        reasons.append(f"Average match is {avg}% — decent alignment with room to improve via missing skills.")
    else:
        reasons.append(f"Average match is {avg}% — strong overall alignment.")

    missing = context.get("market", {}).get("top_missing_skills") or []
    if missing:
        reasons.append(f"Most common missing skills: {', '.join(missing[:3])}.")

    low = jobs_ctx.get("low_match_count", 0)
    if low > jobs_ctx.get("high_match_count", 0):
        reasons.append("Many roles in your scan are below 55% match — consider refining search or upskilling.")

    resume_count = context.get("resume", {}).get("skill_count", 0)
    if resume_count < 8:
        reasons.append("Resume has limited parsed skills — expand skills section for better matching.")

    return {
        "average_match": avg,
        "high_match_count": jobs_ctx.get("high_match_count", 0),
        "reasons": reasons,
        "improvement_tips": [
            "Use Resume AI to optimize keywords for your top target roles",
            "Focus applications on 75%+ match jobs",
            *( [f"Learn {missing[0]} to boost matches"] if missing else [] ),
        ],
    }

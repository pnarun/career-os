"""Career chat — grounded responses with optional Gemini polish."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import requests

from app.core.config import settings
from app.services.copilot.copilot_router import route_copilot_query
from app.services.copilot.insight_memory_service import record_insight, save_chat_turn
from app.services.copilot.recommendation_engine import build_recommendations
from app.services.copilot.user_context_builder import build_user_context

logger = logging.getLogger(__name__)


def get_quick_actions() -> list[dict[str, str]]:
    return [
        {"id": "best_matches", "label": "Find Best Matches", "prompt": "Which jobs fit me best?"},
        {"id": "resume_weaknesses", "label": "Analyze Resume Weaknesses", "prompt": "How can I improve my ATS score and resume?"},
        {"id": "career_growth", "label": "Suggest Career Growth Plan", "prompt": "Should I focus on backend or DevOps? What skills should I learn next?"},
        {"id": "interview_strategy", "label": "Generate Interview Strategy", "prompt": "Why am I not getting interviews? What should I prepare?"},
        {"id": "roi_skills", "label": "Show Highest ROI Skills", "prompt": "What skills should I learn next for highest ROI?"},
        {"id": "provider_advice", "label": "Best Provider for Me", "prompt": "Which provider works best for me?"},
    ]


async def handle_chat(
    message: str,
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Process a user message and return grounded copilot response."""
    session_id = session_id or str(uuid.uuid4())
    message = message.strip()
    if not message:
        return _empty_response(session_id)

    routed = await route_copilot_query(message)
    intent = routed["intent"]
    reasons = _collect_reasons(routed)
    cards = _build_recommendation_cards(routed)
    response_text = _format_rule_based_response(message, routed, reasons)

    if settings.GEMINI_API_KEY:
        polished = _try_gemini_polish(message, routed, response_text)
        if polished:
            response_text = polished

    await save_chat_turn(
        session_id=session_id,
        user_message=message,
        assistant_message=response_text,
        intent=intent,
        recommendations=cards,
        reasons=reasons,
    )
    await record_insight(
        insight_type="recommendation",
        title=intent,
        message=response_text[:200],
        metadata={"intent": intent, "reasons": reasons[:3]},
        session_id=session_id,
    )

    return {
        "session_id": session_id,
        "message": response_text,
        "intent": intent,
        "reasons": reasons,
        "recommendations": cards,
        "context_summary": routed.get("context_summary", {}),
        "source": "gemini" if settings.GEMINI_API_KEY else "grounded",
    }


async def run_quick_action(action_id: str, session_id: str | None = None) -> dict[str, Any]:
    actions = {a["id"]: a for a in get_quick_actions()}
    action = actions.get(action_id)
    if not action:
        raise ValueError(f"Unknown action: {action_id}")
    return await handle_chat(action["prompt"], session_id=session_id)


async def get_copilot_overview() -> dict[str, Any]:
    context = await build_user_context()
    recs = build_recommendations(context)
    return {
        "context_summary": {
            "jobs_in_scan": context.get("jobs", {}).get("total", 0),
            "avg_match": context.get("jobs", {}).get("avg_match", 0),
            "growth_score": context.get("market", {}).get("growth_score", 0),
            "primary_role": context.get("market", {}).get("primary_role", ""),
            "skills_on_resume": context.get("resume", {}).get("skill_count", 0),
        },
        "quick_actions": get_quick_actions(),
        "top_recommendations": (
            recs.get("job_recommendations", [])[:3]
            + recs.get("skill_recommendations", [])[:2]
        ),
        "gemini_enabled": bool(settings.GEMINI_API_KEY),
    }


def _empty_response(session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "message": "Ask me anything about your jobs, skills, applications, or career strategy.",
        "intent": "general",
        "reasons": [],
        "recommendations": [],
        "context_summary": {},
        "source": "grounded",
    }


def _collect_reasons(routed: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in ("opportunities", "skills", "interview", "application_strategy", "market", "match_explanation"):
        block = routed.get(key)
        if not block:
            continue
        reasons.extend(block.get("reasons") or [])
        for r in block.get("recommendations") or []:
            if isinstance(r, str):
                reasons.append(r)
    return list(dict.fromkeys(r for r in reasons if r))[:8]


def _build_recommendation_cards(routed: dict[str, Any]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    recs = routed.get("recommendations", {})
    for job in recs.get("job_recommendations", [])[:4]:
        cards.append({
            "type": "job",
            "title": f"{job['title']} · {job['company']}",
            "subtitle": f"{job['match_score']}% match · {job['source']}",
            "reasons": job.get("reasons", []),
        })
    for skill in recs.get("skill_recommendations", [])[:3]:
        cards.append({
            "type": "skill",
            "title": skill.get("skill", ""),
            "subtitle": f"Priority: {skill.get('priority', 'medium')}",
            "reasons": skill.get("reasons", []),
        })
    for path in recs.get("career_path_suggestions", [])[:2]:
        cards.append({
            "type": "career_path",
            "title": path.get("role", ""),
            "subtitle": f"Demand score: {path.get('demand_score', 0)}",
            "reasons": path.get("reasons", []),
        })
    return cards


def _format_rule_based_response(message: str, routed: dict[str, Any], reasons: list[str]) -> str:
    intent = routed["intent"]
    parts: list[str] = []

    if intent == "opportunities" and routed.get("opportunities"):
        opp = routed["opportunities"]
        parts.append(opp.get("summary", ""))
        if opp.get("strongest_opportunities"):
            parts.append("\n**Strongest opportunities:**")
            for o in opp["strongest_opportunities"][:5]:
                parts.append(f"• {o}")
        for ri in opp.get("response_insights", [])[:2]:
            parts.append(f"• {ri}")

    elif intent == "match_score" and routed.get("match_explanation"):
        me = routed["match_explanation"]
        parts.append(f"Your average match score across the latest scan is **{me.get('average_match', 0)}%**.")
        for r in me.get("reasons", []):
            parts.append(f"• {r}")
        if me.get("improvement_tips"):
            parts.append("\n**How to improve:**")
            for t in me["improvement_tips"][:3]:
                parts.append(f"• {t}")

    elif intent == "skills" and routed.get("skills"):
        sk = routed["skills"]
        parts.append(sk.get("summary", ""))
        for r in sk.get("recommendations", [])[:4]:
            parts.append(f"• {r}")

    elif intent == "interviews" and routed.get("interview"):
        iv = routed["interview"]
        parts.append(iv.get("summary", ""))
        if iv.get("weak_areas"):
            parts.append("\n**Areas to strengthen:**")
            for w in iv["weak_areas"][:4]:
                parts.append(f"• {w}")
        if routed.get("application_strategy"):
            parts.append("\n**Application strategy:**")
            for s in routed["application_strategy"].get("strategy_steps", [])[:3]:
                parts.append(f"• {s}")

    elif intent == "providers" and routed.get("providers"):
        prov = routed["providers"]
        parts.append(f"Best match provider for your profile: **{prov.get('best_match_provider', 'N/A')}**.")
        for p in (prov.get("providers") or [])[:4]:
            parts.append(
                f"• {p.get('label', p.get('source', ''))}: "
                f"{p.get('avg_match_score', 0)}% avg match, "
                f"{p.get('interview_conversion_rate', 0)}% interview rate"
            )

    elif intent == "career_path":
        if routed.get("market"):
            parts.append(routed["market"].get("summary", ""))
            for i in routed["market"].get("market_insights", [])[:4]:
                parts.append(f"• {i}")
        trans = routed.get("career_paths", {})
        if trans.get("suggested_transitions"):
            parts.append("\n**Suggested transitions:**")
            for t in trans["suggested_transitions"][:3]:
                parts.append(f"• {t.get('target_role', '')}: {t.get('reason', '')}")

    elif intent == "resume":
        recs = routed.get("recommendations", {})
        parts.append("Based on your resume and scan data:")
        for rr in recs.get("resume_recommendations", [])[:3]:
            parts.append(f"• **{rr.get('action', '')}**")
            for r in rr.get("reasons", []):
                parts.append(f"  – {r}")
        if routed.get("skills"):
            parts.append(routed["skills"].get("summary", ""))

    elif intent == "strategy" and routed.get("application_strategy"):
        st = routed["application_strategy"]
        parts.append(st.get("summary", ""))
        for s in st.get("strategy_steps", [])[:5]:
            parts.append(f"• {s}")

    elif intent == "market" and routed.get("market"):
        mk = routed["market"]
        parts.append(mk.get("summary", ""))
        for i in mk.get("market_insights", [])[:5]:
            parts.append(f"• {i}")

    else:
        if routed.get("opportunities"):
            parts.append(routed["opportunities"].get("summary", ""))
        if routed.get("skills"):
            parts.append(routed["skills"].get("summary", ""))
        ctx = routed.get("context_summary", {})
        if ctx:
            parts.append(
                f"\nYour scan has {ctx.get('jobs_in_scan', 0)} jobs "
                f"(avg {ctx.get('avg_match', 0)}% match). "
                f"Career growth score: {ctx.get('growth_score', 0)}."
            )

    if reasons and intent != "match_score":
        parts.append("\n**Recommended because:**")
        for r in reasons[:5]:
            parts.append(f"• {r}")

    text = "\n".join(p for p in parts if p).strip()
    return text or "I don't have enough data yet. Upload a resume and run a job scan, then ask again."


def _try_gemini_polish(question: str, routed: dict[str, Any], draft: str) -> str | None:
    """Optional Gemini layer — must not invent facts beyond context."""
    try:
        context_json = json.dumps({
            "intent": routed.get("intent"),
            "context_summary": routed.get("context_summary"),
            "opportunities": routed.get("opportunities"),
            "skills": routed.get("skills"),
            "interview": routed.get("interview"),
            "market": routed.get("market"),
            "match_explanation": routed.get("match_explanation"),
            "recommendations": routed.get("recommendations"),
        }, default=str)[:12000]

        prompt = (
            "You are Career OS Copilot. Answer ONLY using the JSON context below. "
            "Never invent jobs, salaries, or statistics not in the context. "
            "Never guarantee hiring outcomes. Be concise, helpful, and explain WHY. "
            "Use bullet points where helpful.\n\n"
            f"CONTEXT:\n{context_json}\n\n"
            f"DRAFT ANSWER:\n{draft}\n\n"
            f"USER QUESTION:\n{question}\n\n"
            "Polish the draft answer. Keep all facts accurate to the context."
        )

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
        )
        resp = requests.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20,
        )
        if resp.status_code != 200:
            logger.warning("Gemini polish failed: %s", resp.status_code)
            return None
        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts") or []
        text = parts[0].get("text", "").strip() if parts else ""
        return text or None
    except Exception as exc:
        logger.warning("Gemini polish error: %s", exc)
        return None

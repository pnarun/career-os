"""Application strategy — funnel optimization and provider advice."""

from __future__ import annotations

from typing import Any


def advise_application_strategy(context: dict[str, Any]) -> dict[str, Any]:
    apps = context.get("applications", {})
    market = context.get("market", {})
    jobs_ctx = context.get("jobs", {})
    funnel = market.get("application_funnel", {})

    app_analytics = apps.get("analytics", {})
    providers = market.get("provider_performance", {})
    provider_list = providers.get("providers") or []

    strategy: list[str] = []
    reasons: list[str] = []

    total_applied = app_analytics.get("total_applied", 0)
    response_rate = app_analytics.get("response_rate", 0)

    if total_applied == 0:
        strategy.append("Start by saving 5–10 high-match jobs (75%+) from your latest scan.")
        reasons.append("No applications tracked yet — build pipeline from saved jobs.")
    elif response_rate < 10:
        strategy.append("Prioritize roles with 75%+ match before applying broadly.")
        reasons.append(f"Response rate is {response_rate}% — quality over quantity.")
    else:
        strategy.append("Continue applying to high-match roles; your response rate shows traction.")
        reasons.append(f"Response rate: {response_rate}%.")

    best_conv = max(provider_list, key=lambda p: p.get("interview_conversion_rate", 0), default=None)
    if best_conv and best_conv.get("interview_conversion_rate", 0) > 0:
        strategy.append(f"Focus applications on {best_conv.get('label', best_conv.get('source', ''))}.")
        reasons.append(f"Best interview conversion: {best_conv['interview_conversion_rate']}%.")

    high_matches = [j for j in jobs_ctx.get("top_jobs", []) if j.get("match_percentage", 0) >= 75]
    if high_matches:
        strategy.append(f"Apply first to {len(high_matches)} roles scoring 75%+ in your scan.")
        reasons.append("High-match roles correlate with better outcomes in your data.")

    if funnel.get("funnel"):
        saved = next((s for s in funnel["funnel"] if s.get("stage") == "Saved"), {})
        applied = next((s for s in funnel["funnel"] if s.get("stage") == "Applied"), {})
        if saved.get("count", 0) > applied.get("count", 0) * 2:
            strategy.append("Convert saved jobs to applications — you have a large saved backlog.")
            reasons.append("Saved-to-applied conversion is low.")

    strategy.append("Follow up on applications older than 7 days with no status change.")

    return {
        "strategy_steps": strategy[:6],
        "reasons": reasons[:5],
        "funnel": funnel.get("funnel", []),
        "response_rate": response_rate,
        "summary": strategy[0] if strategy else "Track applications in the CRM to get personalized strategy.",
    }

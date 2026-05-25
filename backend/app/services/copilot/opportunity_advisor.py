"""Opportunity advisor — best-fit jobs and response patterns."""

from __future__ import annotations

from typing import Any


def advise_opportunities(context: dict[str, Any]) -> dict[str, Any]:
    jobs_ctx = context.get("jobs", {})
    market = context.get("market", {})
    apps = context.get("applications", {})

    strongest: list[str] = []
    for job in jobs_ctx.get("top_jobs", [])[:5]:
        if job.get("match_percentage", 0) >= 60:
            remote = "Remote " if job.get("remote") else ""
            strongest.append(f"{remote}{job['title']} at {job['company']} ({job['match_percentage']}% match)")

    weekly = market.get("weekly_insights", {})
    if weekly.get("strongest_opportunities"):
        for opp in weekly["strongest_opportunities"][:3]:
            if opp not in strongest:
                strongest.append(opp)

    providers = market.get("provider_performance", {})
    provider_list = providers.get("providers") or []
    best_provider = providers.get("best_match_provider", "")
    best_conversion = providers.get("best_interview_conversion")

    response_insights: list[str] = []
    app_analytics = apps.get("analytics", {})
    if app_analytics.get("response_rate", 0) > 0:
        response_insights.append(
            f"Your application response rate is {app_analytics['response_rate']}%."
        )
    if best_conversion:
        response_insights.append(
            f"Highest interview conversion: {best_conversion.get('label', '')} "
            f"({best_conversion.get('interview_conversion_rate', 0)}%)."
        )
    elif best_provider:
        response_insights.append(f"Highest match quality provider: {best_provider}.")

    high_match = [j for j in jobs_ctx.get("top_jobs", []) if j.get("match_percentage", 0) >= 85]
    if high_match and app_analytics.get("response_rate", 0) < 10:
        response_insights.append(
            "You have strong matches but low response rate — consider tailoring resume per role."
        )

    return {
        "strongest_opportunities": strongest[:6],
        "response_insights": response_insights,
        "best_provider": best_provider,
        "high_match_available": len(high_match),
        "summary": _build_summary(strongest, best_provider, jobs_ctx),
    }


def _build_summary(strongest: list[str], best_provider: str, jobs_ctx: dict) -> str:
    if not strongest:
        return "Run a job scan to discover opportunities aligned with your profile."
    parts = [f"Your strongest opportunities currently include {len(strongest)} roles from your latest scan."]
    if best_provider:
        parts.append(f"{best_provider} shows the best match quality for your profile.")
    if jobs_ctx.get("remote_count", 0) > 0:
        parts.append(f"{jobs_ctx['remote_count']} remote roles are available in your scan.")
    return " ".join(parts)

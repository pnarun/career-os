"""Market trend analysis from scan history and latest jobs."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.services.career_analytics._analytics_utils import (
    ROLE_KEYWORDS,
    collect_market_skills,
    infer_primary_role,
    pct_change,
)
from app.services.career_analytics._constants import ANALYTICS_HISTORY_SAMPLE
from app.services.job_service import get_all_jobs, get_latest_scan_jobs
from app.services.scan_session_service import list_recent_scan_sessions


async def build_market_trends() -> dict[str, Any]:
    jobs = await get_latest_scan_jobs()
    all_jobs = await get_all_jobs(limit=ANALYTICS_HISTORY_SAMPLE)
    from app.core.user_context import get_request_user_id

    user_id = get_request_user_id() or ""
    sessions = (
        await list_recent_scan_sessions(user_id, limit=8)
        if user_id
        else []
    )

    skill_counts = collect_market_skills(jobs)
    total_jobs = len(jobs) or 1

    most_demanded = [
        {
            "technology": skill,
            "job_count": count,
            "demand_pct": int(round(count / total_jobs * 100)),
        }
        for skill, count in skill_counts.most_common(12)
    ]

    # Role growth from title tokens
    role_counts: Counter[str] = Counter()
    for job in jobs:
        title_lower = job.title.lower()
        for keyword, label in ROLE_KEYWORDS:
            if keyword in title_lower:
                role_counts[label] += 1
    fastest_growing_roles = [
        {"role": role, "openings": count, "share_pct": int(round(count / total_jobs * 100))}
        for role, count in role_counts.most_common(6)
    ]

    # Compare skill demand across recent vs older jobs
    recent_cutoff = len(all_jobs) // 2
    older_jobs = all_jobs[recent_cutoff:] if recent_cutoff else []
    newer_jobs = all_jobs[:recent_cutoff] if recent_cutoff else jobs
    old_skills = collect_market_skills(older_jobs if older_jobs else jobs[: max(1, len(jobs) // 2)])
    new_skills = collect_market_skills(newer_jobs if newer_jobs else jobs)

    rising: list[dict[str, Any]] = []
    declining: list[dict[str, Any]] = []
    for skill in set(list(old_skills.keys()) + list(new_skills.keys())):
        old_c = old_skills.get(skill, 0)
        new_c = new_skills.get(skill, 0)
        change = pct_change(new_c, old_c)
        entry = {"technology": skill, "change_pct": change, "current_count": new_c}
        if change >= 15:
            rising.append(entry)
        elif change <= -15 and old_c >= 2:
            declining.append(entry)
    rising.sort(key=lambda x: x["change_pct"], reverse=True)
    declining.sort(key=lambda x: x["change_pct"])

    remote_count = sum(1 for j in jobs if j.remote_priority)
    remote_pct = int(round(remote_count / total_jobs * 100))

    trend_insights: list[str] = []
    if most_demanded:
        top = most_demanded[0]
        trend_insights.append(
            f"{top['technology']} appears in {top['demand_pct']}% of roles in your latest scan."
        )
    for item in rising[:3]:
        trend_insights.append(f"{item['technology']} demand increased {item['change_pct']}% recently.")
    for item in declining[:2]:
        trend_insights.append(f"{item['technology']} demand declined {abs(item['change_pct'])}%.")
    if remote_pct >= 35:
        trend_insights.append(f"Remote roles represent {remote_pct}% of your market — strong remote hiring.")
    elif remote_pct >= 20:
        trend_insights.append(f"Remote opportunities growing — {remote_pct}% of latest scan.")

    # Hiring spikes from scan sessions
    hiring_spikes: list[dict[str, Any]] = []
    if len(sessions) >= 2:
        for i in range(len(sessions) - 1):
            curr = sessions[i]
            prev = sessions[i + 1]
            delta = curr.qualified_jobs - prev.qualified_jobs
            if delta >= 5 or (prev.qualified_jobs and delta / prev.qualified_jobs >= 0.2):
                hiring_spikes.append({
                    "scan_id": curr.scan_id,
                    "qualified_jobs": curr.qualified_jobs,
                    "change": delta,
                    "timestamp": curr.scan_timestamp or curr.created_at,
                })

    return {
        "most_demanded_technologies": most_demanded,
        "fastest_growing_roles": fastest_growing_roles,
        "rising_technologies": rising[:8],
        "declining_technologies": declining[:6],
        "remote_market_pct": remote_pct,
        "remote_trend": "growing" if remote_pct >= 25 else "moderate" if remote_pct >= 15 else "low",
        "trend_insights": trend_insights[:8],
        "hiring_spikes": hiring_spikes[:5],
        "primary_role": infer_primary_role(jobs),
        "total_jobs_analyzed": total_jobs,
    }

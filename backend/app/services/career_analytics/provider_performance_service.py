"""Provider performance analytics across match quality and outcomes."""

from __future__ import annotations

from typing import Any

from app.core.database import get_database
from app.services.career_analytics._analytics_utils import provider_label
from app.services.job_service import get_latest_scan_jobs


async def build_provider_performance() -> dict[str, Any]:
    jobs = await get_latest_scan_jobs()
    collection = get_database()["applications"]
    from app.services.application_service import _scoped_query

    cursor = collection.find(
        _scoped_query(),
        {"status": 1, "source": 1, "match_score": 1},
    ).limit(500)
    applications = await cursor.to_list(length=500)

    provider_jobs: dict[str, list] = {}
    for job in jobs:
        provider_jobs.setdefault(job.source, []).append(job)

    provider_apps: dict[str, list] = {}
    for app in applications:
        src = str(app.get("source") or "unknown").lower()
        provider_apps.setdefault(src, []).append(app)

    all_sources = set(provider_jobs.keys()) | set(provider_apps.keys())
    results: list[dict[str, Any]] = []

    for source in all_sources:
        job_list = provider_jobs.get(source, [])
        app_list = provider_apps.get(source, [])

        avg_match = (
            int(sum(j.match_percentage for j in job_list) / len(job_list))
            if job_list else 0
        )
        remote_count = sum(1 for j in job_list if j.remote_priority)
        remote_pct = int(round(remote_count / len(job_list) * 100)) if job_list else 0
        avg_quality = (
            int(sum(j.job_quality_score for j in job_list) / len(job_list))
            if job_list else 0
        )
        high_match = sum(1 for j in job_list if j.match_percentage >= 75)

        interviews = sum(1 for a in app_list if a.get("status") in ("interview", "assessment"))
        applied = sum(1 for a in app_list if a.get("status") not in ("saved", "withdrawn"))
        interview_rate = round((interviews / applied) * 100, 1) if applied else 0.0

        results.append({
            "source": source,
            "label": provider_label(source),
            "job_count": len(job_list),
            "avg_match_score": avg_match,
            "high_match_count": high_match,
            "remote_opportunity_pct": remote_pct,
            "avg_quality_score": avg_quality,
            "applications": len(app_list),
            "interview_conversion_rate": interview_rate,
            "quality_rating": _quality_rating(avg_match, avg_quality, remote_pct),
        })

    results.sort(key=lambda x: (x["avg_match_score"], x["job_count"]), reverse=True)

    best_match = results[0]["label"] if results else ""
    best_conversion = max(results, key=lambda x: x["interview_conversion_rate"]) if results else None
    most_remote = max(results, key=lambda x: x["remote_opportunity_pct"]) if results else None

    return {
        "providers": results,
        "best_match_provider": best_match,
        "best_interview_conversion": best_conversion,
        "most_remote_opportunities": most_remote,
        "summary": _build_summary(results),
    }


def _quality_rating(avg_match: int, avg_quality: int, remote_pct: int) -> str:
    score = avg_match * 0.5 + avg_quality * 0.3 + remote_pct * 0.2
    if score >= 70:
        return "excellent"
    if score >= 55:
        return "good"
    if score >= 40:
        return "fair"
    return "limited"


def _build_summary(providers: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    if not providers:
        return ["Run a job scan to compare provider performance."]
    top = providers[0]
    lines.append(f"{top['label']} delivers the highest average match ({top['avg_match_score']}%).")
    remote_leader = max(providers, key=lambda x: x["remote_opportunity_pct"])
    if remote_leader["remote_opportunity_pct"] >= 30:
        lines.append(
            f"{remote_leader['label']} has the most remote roles ({remote_leader['remote_opportunity_pct']}%)."
        )
    conv = [p for p in providers if p["interview_conversion_rate"] > 0]
    if conv:
        best = max(conv, key=lambda x: x["interview_conversion_rate"])
        lines.append(
            f"{best['label']} shows {best['interview_conversion_rate']}% interview conversion from applications."
        )
    return lines

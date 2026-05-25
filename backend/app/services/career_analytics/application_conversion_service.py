"""Application funnel and conversion analytics."""

from __future__ import annotations

from typing import Any

from app.core.database import get_database
from app.services.application_service import (
    INTERVIEW_STATUSES,
    REJECTION_STATUSES,
    build_application_analytics,
)
from app.services.job_service import get_latest_scan_jobs


async def build_application_conversion_analytics() -> dict[str, Any]:
    jobs = await get_latest_scan_jobs()
    app_analytics = await build_application_analytics()

    collection = get_database()["applications"]
    from app.services.application_service import _scoped_query

    documents = await collection.find(_scoped_query()).to_list(length=1000)

    jobs_viewed = len(jobs)
    saved = app_analytics.total_saved + sum(
        1 for d in documents if d.get("status") != "saved"
    )
    applied = sum(
        1 for d in documents
        if d.get("status") not in ("saved", "withdrawn") and d.get("applied_at")
    )
    interviews = sum(1 for d in documents if d.get("status") in INTERVIEW_STATUSES)
    offers = sum(1 for d in documents if d.get("status") == "offer")

    def _pct(num: int, denom: int) -> float:
        return round((num / denom) * 100, 1) if denom else 0.0

    funnel = [
        {"stage": "Jobs Viewed", "count": jobs_viewed, "conversion_pct": 100.0},
        {"stage": "Saved", "count": saved, "conversion_pct": _pct(saved, jobs_viewed)},
        {"stage": "Applied", "count": applied, "conversion_pct": _pct(applied, saved or jobs_viewed)},
        {"stage": "Interview", "count": interviews, "conversion_pct": _pct(interviews, applied or 1)},
        {"stage": "Offer", "count": offers, "conversion_pct": _pct(offers, interviews or applied or 1)},
    ]

    # Provider conversion
    provider_stats: dict[str, dict[str, int]] = {}
    for doc in documents:
        src = str(doc.get("source") or "unknown").lower()
        provider_stats.setdefault(src, {"saved": 0, "applied": 0, "interview": 0, "offer": 0})
        status = doc.get("status", "")
        if status == "saved":
            provider_stats[src]["saved"] += 1
        elif status not in ("withdrawn",):
            provider_stats[src]["applied"] += 1
        if status in INTERVIEW_STATUSES:
            provider_stats[src]["interview"] += 1
        if status == "offer":
            provider_stats[src]["offer"] += 1

    provider_success = []
    for src, stats in provider_stats.items():
        applied_n = stats["applied"] or stats["saved"]
        provider_success.append({
            "source": src,
            "applied": stats["applied"],
            "interviews": stats["interview"],
            "offers": stats["offer"],
            "interview_rate": _pct(stats["interview"], applied_n),
            "offer_rate": _pct(stats["offer"], applied_n),
        })
    provider_success.sort(key=lambda x: x["interview_rate"], reverse=True)

    # Match score effectiveness
    match_buckets: dict[str, list[str]] = {"high": [], "medium": [], "low": []}
    for doc in documents:
        score = int(doc.get("match_score") or 0)
        status = doc.get("status", "")
        if score >= 75:
            bucket = "high"
        elif score >= 55:
            bucket = "medium"
        else:
            bucket = "low"
        if status in INTERVIEW_STATUSES | {"offer"} | REJECTION_STATUSES:
            match_buckets[bucket].append("responded")
        elif status == "applied":
            match_buckets[bucket].append("pending")

    match_effectiveness = []
    for label, outcomes in match_buckets.items():
        total = len(outcomes)
        responded = sum(1 for o in outcomes if o == "responded")
        match_effectiveness.append({
            "bucket": label,
            "applications": total,
            "response_rate": _pct(responded, total),
        })

    return {
        "funnel": funnel,
        "overall_response_rate": app_analytics.response_rate,
        "provider_success_rate": provider_success,
        "match_score_effectiveness": match_effectiveness,
        "response_rate_trend": "stable",
        "totals": {
            "saved": app_analytics.total_saved,
            "applied": app_analytics.total_applied,
            "interviews": app_analytics.interviews,
            "offers": app_analytics.offers,
            "rejections": app_analytics.rejections,
        },
    }

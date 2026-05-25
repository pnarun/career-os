"""Job market heatmap — location and remote density."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.services.career_analytics._analytics_utils import job_city
from app.services.job_service import get_all_jobs, get_latest_scan_jobs


async def build_job_market_heatmap() -> dict[str, Any]:
    jobs = await get_latest_scan_jobs()
    all_jobs = await get_all_jobs()

    city_counts: Counter[str] = Counter()
    city_match: dict[str, list[int]] = {}
    remote_count = 0

    for job in jobs:
        city = job_city(job)
        city_counts[city] += 1
        city_match.setdefault(city, []).append(job.match_percentage)
        if job.remote_priority or city == "Remote":
            remote_count += 1

    total = len(jobs) or 1
    heatmap = []
    for city, count in city_counts.most_common(15):
        avg_match = int(sum(city_match[city]) / len(city_match[city])) if city_match[city] else 0
        heatmap.append({
            "location": city,
            "job_count": count,
            "demand_intensity": min(100, int(round(count / total * 100)) + count),
            "avg_match_score": avg_match,
            "share_pct": int(round(count / total * 100)),
        })

    # Historical location trend from all jobs
    historical_cities: Counter[str] = Counter()
    for job in all_jobs:
        historical_cities[job_city(job)] += 1

    trending_up: list[dict[str, Any]] = []
    for city, curr in city_counts.most_common(10):
        hist = historical_cities.get(city, curr)
        if curr > hist * 0.6:
            trending_up.append({"location": city, "current": curr, "historical": hist})

    remote_density = int(round(remote_count / total * 100))

    return {
        "heatmap": heatmap,
        "remote_opportunity_density": remote_density,
        "strongest_hiring_cities": [h["location"] for h in heatmap[:5]],
        "location_trends": trending_up[:8],
        "total_locations": len(city_counts),
        "total_jobs": total,
    }

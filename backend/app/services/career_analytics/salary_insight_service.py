"""Salary intelligence from job descriptions and market benchmarks."""

from __future__ import annotations

from collections import Counter
from typing import Any

from app.models.job import JobDocument
from app.services.career_analytics._analytics_utils import (
    ROLE_SALARY_BENCHMARKS,
    SKILL_SALARY_PREMIUM,
    infer_primary_role,
    parse_salary_from_text,
    provider_label,
)
from app.services.job_service import get_latest_scan_jobs
from app.services.user_preferences_service import get_preferences


USD_TO_INR = 83


def _usd_to_inr(amount: int) -> int:
    return int(amount * USD_TO_INR)


async def build_salary_insights(target_role: str | None = None) -> dict[str, Any]:
    jobs = await get_latest_scan_jobs()
    if target_role and target_role.strip():
        needle = target_role.strip().lower()
        jobs = [j for j in jobs if needle in (j.title or "").lower()]
    preferences = await get_preferences()

    parsed_salaries: list[int] = []
    remote_salaries: list[int] = []
    onsite_salaries: list[int] = []
    skill_salary_map: dict[str, list[int]] = {}
    provider_salaries: dict[str, list[int]] = {}

    for job in jobs:
        text = f"{job.description} {job.title}"
        salary = parse_salary_from_text(text)
        if salary:
            parsed_salaries.append(salary)
            bucket = remote_salaries if job.remote_priority else onsite_salaries
            bucket.append(salary)
            provider_salaries.setdefault(job.source, []).append(salary)
            for skill in (job.matched_skills or []) + (job.missing_skills or []):
                skill_salary_map.setdefault(skill, []).append(salary)

    primary_role = infer_primary_role(jobs)
    benchmark = ROLE_SALARY_BENCHMARKS.get(primary_role, ROLE_SALARY_BENCHMARKS["general"])

    if parsed_salaries:
        avg_usd = int(sum(parsed_salaries) / len(parsed_salaries))
        avg = _usd_to_inr(avg_usd)
        lo, hi = _usd_to_inr(min(parsed_salaries)), _usd_to_inr(max(parsed_salaries))
        salary_range = f"₹{lo:,} – ₹{hi:,}"
    else:
        avg = _usd_to_inr(int((benchmark[0] + benchmark[1]) / 2))
        lo, hi = _usd_to_inr(benchmark[0]), _usd_to_inr(benchmark[1])
        salary_range = f"₹{lo:,} – ₹{hi:,} (estimated)"

    top_paying_skills: list[dict[str, Any]] = []
    if skill_salary_map:
        for skill, values in skill_salary_map.items():
            top_paying_skills.append({
                "skill": skill,
                "avg_salary": _usd_to_inr(int(sum(values) / len(values))),
                "job_count": len(values),
            })
        top_paying_skills.sort(key=lambda x: x["avg_salary"], reverse=True)
        top_paying_skills = top_paying_skills[:8]
    else:
        for skill, premium in sorted(SKILL_SALARY_PREMIUM.items(), key=lambda x: -x[1])[:8]:
            top_paying_skills.append({
                "skill": skill,
                "avg_salary": avg + premium,
                "job_count": 0,
                "estimated_premium": premium,
            })

    remote_avg = int(sum(remote_salaries) / len(remote_salaries)) if remote_salaries else 0
    onsite_avg = int(sum(onsite_salaries) / len(onsite_salaries)) if onsite_salaries else avg
    if remote_avg and onsite_avg:
        premium_pct = int(round(((remote_avg - onsite_avg) / onsite_avg) * 100))
        remote_premium = f"{premium_pct:+d}% vs on-site average"
    elif remote_avg:
        remote_premium = "Remote roles show competitive compensation in your scan"
    else:
        remote_premium = "Insufficient salary data for remote comparison"

    provider_distribution = [
        {
            "provider": provider_label(src),
            "avg_salary": int(sum(vals) / len(vals)),
            "sample_size": len(vals),
        }
        for src, vals in provider_salaries.items()
        if vals
    ]
    provider_distribution.sort(key=lambda x: x["avg_salary"], reverse=True)

    expected = (preferences.expected_salary or "").strip()
    growth_trend = "Stable market demand for your target roles"
    if parsed_salaries and expected:
        growth_trend = f"Market average ${avg:,} vs your expectation: {expected}"

    return {
        "average_salary": f"${avg:,}",
        "salary_range": salary_range,
        "top_paying_skills": top_paying_skills,
        "salary_growth_trend": growth_trend,
        "remote_salary_premium": remote_premium,
        "provider_salary_distribution": provider_distribution,
        "primary_role": primary_role,
        "salary_data_points": len(parsed_salaries),
    }

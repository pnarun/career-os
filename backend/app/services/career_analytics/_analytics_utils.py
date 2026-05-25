"""Shared utilities for career analytics services."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.models.job import JobDocument
from app.utils.skills_master import extract_skills_from_text

ROLE_KEYWORDS = (
    ("backend", "Backend Engineering"),
    ("back-end", "Backend Engineering"),
    ("frontend", "Frontend Engineering"),
    ("front-end", "Frontend Engineering"),
    ("full stack", "Full Stack Engineering"),
    ("fullstack", "Full Stack Engineering"),
    ("devops", "DevOps Engineering"),
    ("platform", "Platform Engineering"),
    ("data engineer", "Data Engineering"),
    ("data scientist", "Data Science"),
    ("machine learning", "ML Engineering"),
    ("cloud", "Cloud Engineering"),
    ("sre", "Site Reliability Engineering"),
    ("mobile", "Mobile Engineering"),
    ("qa", "QA Engineering"),
    ("quality assurance", "QA Engineering"),
)

ROLE_TRANSITIONS: dict[str, list[dict[str, str]]] = {
    "Backend Engineering": [
        {"role": "Platform Engineer", "reason": "Strong backend + infrastructure skills transfer well to platform roles."},
        {"role": "DevOps Engineer", "reason": "Backend automation and deployment experience maps to DevOps."},
        {"role": "Cloud Engineer", "reason": "Cloud infrastructure is a natural next step."},
    ],
    "Frontend Engineering": [
        {"role": "Full Stack Engineer", "reason": "Frontend depth pairs well with backend-oriented market demand."},
        {"role": "UI Engineer", "reason": "UI specialization remains in high demand."},
        {"role": "Solutions Architect", "reason": "Client-facing architecture roles value frontend expertise."},
    ],
    "Full Stack Engineering": [
        {"role": "Solutions Architect", "reason": "Broad stack coverage supports end-to-end design roles."},
        {"role": "Platform Engineer", "reason": "Full stack + infra exposure fits platform engineering."},
        {"role": "Backend Engineer", "reason": "Backend roles often offer stronger salary trajectory."},
    ],
    "DevOps Engineering": [
        {"role": "Cloud Engineer", "reason": "Cloud + automation skills dominate current hiring."},
        {"role": "Site Reliability Engineer", "reason": "Reliability engineering is a natural adjacent path."},
        {"role": "Platform Engineer", "reason": "Internal platform teams are scaling rapidly."},
    ],
    "general": [
        {"role": "Backend Engineer", "reason": "Backend roles show consistent demand across providers."},
        {"role": "Full Stack Engineer", "reason": "Versatile engineering roles remain widely available."},
        {"role": "Cloud Engineer", "reason": "Cloud infrastructure skills have strong hiring momentum."},
    ],
}

# Approximate annual salary benchmarks (USD) by role tier when JD parsing is sparse
ROLE_SALARY_BENCHMARKS: dict[str, tuple[int, int]] = {
    "Backend Engineering": (95000, 145000),
    "Frontend Engineering": (85000, 130000),
    "Full Stack Engineering": (90000, 140000),
    "DevOps Engineering": (100000, 155000),
    "Platform Engineering": (105000, 160000),
    "Cloud Engineering": (110000, 170000),
    "Data Engineering": (100000, 150000),
    "ML Engineering": (115000, 175000),
    "general": (80000, 125000),
}

SKILL_SALARY_PREMIUM: dict[str, int] = {
    "Kubernetes": 12000,
    "AWS": 10000,
    "Docker": 6000,
    "Python": 8000,
    "FastAPI": 7000,
    "React": 5000,
    "TypeScript": 5000,
    "Terraform": 9000,
    "Machine Learning": 15000,
    "GraphQL": 4000,
    "Microservices": 6000,
    "Kafka": 7000,
}

CITY_DEMAND_HINTS = (
    "bengaluru",
    "bangalore",
    "hyderabad",
    "chennai",
    "pune",
    "mumbai",
    "delhi",
    "noida",
    "gurgaon",
    "remote",
    "san francisco",
    "new york",
    "austin",
    "seattle",
    "london",
    "berlin",
)

PROVIDER_LABELS = {
    "linkedin": "LinkedIn",
    "indeed": "Indeed",
    "naukri": "Naukri",
    "remoteok": "RemoteOK",
    "arbeitnow": "Arbeitnow",
    "instahyre": "Instahyre",
}


def provider_label(source: str) -> str:
    return PROVIDER_LABELS.get((source or "").lower(), (source or "Unknown").title())


def infer_primary_role(jobs: list[JobDocument]) -> str:
    counts: Counter[str] = Counter()
    for job in jobs[:50]:
        title_lower = job.title.lower()
        for keyword, label in ROLE_KEYWORDS:
            if keyword in title_lower:
                counts[label] += 1
    if counts:
        return counts.most_common(1)[0][0]
    return "Software Engineering"


def job_city(job: JobDocument) -> str:
    loc = (job.location or "").strip().lower()
    if not loc:
        return "Unknown"
    if any(h in loc for h in ("remote", "work from home", "wfh", "anywhere")):
        return "Remote"
    for city in CITY_DEMAND_HINTS:
        if city in loc:
            return city.title() if city != "remote" else "Remote"
    return (job.location or "Unknown")[:40]


def _parse_int_token(raw: str) -> int | None:
    cleaned = raw.replace(",", "").strip()
    if not cleaned or not any(c.isdigit() for c in cleaned):
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def parse_salary_from_text(text: str) -> int | None:
    """Extract a midpoint annual salary in USD (or INR converted roughly)."""
    if not text:
        return None
    lower = text.lower()

    # USD patterns: $120k, $120,000, 120k USD
    for match in re.finditer(r"\$\s*([\d,]+)\s*k?\b", lower):
        parsed = _parse_int_token(match.group(1))
        if parsed is None:
            continue
        val = parsed * 1000 if parsed < 1000 else parsed
        if 30000 <= val <= 500000:
            return val

    for match in re.finditer(r"([\d,]+)\s*k\s*(?:usd|\$|per\s*year|/yr)?", lower):
        parsed = _parse_int_token(match.group(1))
        if parsed is None:
            continue
        val = parsed * 1000
        if 30000 <= val <= 500000:
            return val

    # INR lakh pattern — rough USD conversion (~83 INR = 1 USD)
    for match in re.finditer(r"([\d.]+)\s*[-–to]+\s*([\d.]+)\s*lpa", lower):
        low = float(match.group(1))
        high = float(match.group(2))
        avg_lpa = (low + high) / 2
        inr = avg_lpa * 100000
        usd = int(inr / 83)
        if 15000 <= usd <= 400000:
            return usd

    for match in re.finditer(r"([\d.]+)\s*lpa", lower):
        lpa = float(match.group(1))
        usd = int(lpa * 100000 / 83)
        if 15000 <= usd <= 400000:
            return usd

    return None


def job_to_dict(job: JobDocument) -> dict[str, Any]:
    return {
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "source": job.source,
        "description": job.description,
        "remote_priority": job.remote_priority,
        "match_percentage": job.match_percentage,
        "matched_skills": job.matched_skills,
        "missing_skills": job.missing_skills,
    }


def collect_market_skills(jobs: list[JobDocument]) -> Counter[str]:
    skill_counts: Counter[str] = Counter()
    for job in jobs:
        text = f"{job.title} {job.description} {' '.join(job.matched_skills)} {' '.join(job.missing_skills)}"
        for skill in extract_skills_from_text(text):
            skill_counts[skill] += 1
    return skill_counts


def pct_change(current: int, previous: int) -> int:
    if previous <= 0:
        return 100 if current > 0 else 0
    return int(round(((current - previous) / previous) * 100))

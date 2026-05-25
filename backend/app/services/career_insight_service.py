"""Rule-based career insights — no LLM APIs."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.database import get_database
from app.models.career_insight import CareerInsightDocument, CareerInsightsSummary
from app.models.job import JobDocument
from app.models.user_preferences import UserPreferencesDocument
from app.services.application_service import build_application_analytics, list_applications
from app.services.job_service import get_latest_scan_jobs
from app.services.resume_service import get_resume_by_id

logger = logging.getLogger(__name__)

CAREER_INSIGHTS_COLLECTION = "career_insights"
HIGH_MATCH_THRESHOLD = 85


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_collection() -> AsyncIOMotorCollection:
    return get_database()[CAREER_INSIGHTS_COLLECTION]


async def ensure_career_insight_indexes() -> None:
    collection = _get_collection()
    await collection.create_index([("created_at", -1)])
    await collection.create_index("insight_type")
    await collection.create_index("preference_id")
    logger.info("Career insights collection indexes ensured")


def _infer_role_alignment(jobs: list[JobDocument], resume_skills: list[str]) -> str:
    if not jobs:
        return "Upload a resume and run a scan to discover your market alignment."

    title_tokens: Counter[str] = Counter()
    for job in jobs[:30]:
        title_lower = job.title.lower()
        for keyword in ("backend", "frontend", "full stack", "fullstack", "devops", "data", "python", "java", "react"):
            if keyword in title_lower:
                title_tokens[keyword] += 1

    if not title_tokens:
        return "Your profile aligns with general software engineering roles across multiple stacks."

    top_role = title_tokens.most_common(1)[0][0]
    skill_hint = resume_skills[0] if resume_skills else top_role
    return f"Your strongest market alignment is {top_role} roles, leveraging skills like {skill_hint}."


def _top_missing_skills(jobs: list[JobDocument]) -> list[str]:
    missing: Counter[str] = Counter()
    for job in jobs:
        if job.match_percentage >= 60:
            for skill in job.missing_skills or []:
                missing[skill.strip()] += 1
    return [skill for skill, _ in missing.most_common(5)]


def _best_source_by_match(jobs: list[JobDocument]) -> str:
    if not jobs:
        return ""
    source_scores: dict[str, list[int]] = {}
    for job in jobs:
        source_scores.setdefault(job.source, []).append(job.match_percentage)
    averages = {
        source: sum(scores) / len(scores)
        for source, scores in source_scores.items()
        if scores
    }
    if not averages:
        return ""
    best = max(averages, key=averages.get)
    labels = {
        "linkedin": "LinkedIn",
        "indeed": "Indeed",
        "naukri": "Naukri",
        "remoteok": "RemoteOK",
        "arbeitnow": "Arbeitnow",
        "instahyre": "Instahyre",
    }
    label = labels.get(best.lower(), best.title())
    return f"{label} gives highest match quality for your profile (avg {averages[best]:.0f}%)."


def _remote_trend_message(jobs: list[JobDocument]) -> str:
    remote_count = sum(1 for j in jobs if j.remote_priority)
    total = len(jobs) or 1
    pct = int(remote_count / total * 100)
    if pct >= 40:
        return f"Remote opportunities represent {pct}% of your latest scan — strong remote market fit."
    if pct >= 20:
        return f"Remote opportunities increased to {pct}% of roles in your latest scan."
    return "On-site and hybrid roles dominate your current scan — consider enabling remote filters."


async def generate_career_insights(
    preferences: UserPreferencesDocument | None = None,
    *,
    persist: bool = True,
) -> CareerInsightsSummary:
    """Generate rule-based insights from latest scan, resume, and applications."""
    jobs = await get_latest_scan_jobs()
    if preferences and preferences.remote_only:
        jobs = [j for j in jobs if j.remote_priority]

    resume_skills: list[str] = []
    if preferences and preferences.resume_id:
        try:
            resume = await get_resume_by_id(preferences.resume_id)
            resume_skills = list(resume.skills or [])[:10]
        except Exception:
            pass

    messages: list[str] = []
    insight_docs: list[CareerInsightDocument] = []

    alignment = _infer_role_alignment(jobs, resume_skills)
    messages.append(alignment)

    missing_skills = _top_missing_skills(jobs)
    if missing_skills:
        top_skill = missing_skills[0]
        messages.append(f"Most missing skill across high-match jobs: {top_skill}.")

    messages.append(_remote_trend_message(jobs))

    best_source = _best_source_by_match(jobs)
    if best_source:
        messages.append(best_source)

    high_matches = [j for j in jobs if j.match_percentage >= HIGH_MATCH_THRESHOLD]
    if high_matches:
        messages.append(
            f"{len(high_matches)} roles scored {HIGH_MATCH_THRESHOLD}%+ — prioritize these opportunities."
        )

    app_analytics = await build_application_analytics()
    if app_analytics.total_applied > 0 and app_analytics.response_rate > 0:
        messages.append(
            f"Your application response rate is {app_analytics.response_rate:.0f}% — "
            f"{'above' if app_analytics.response_rate >= 15 else 'below'} typical benchmarks."
        )

    pref_id = preferences.id if preferences else ""
    now = _utc_now_iso()
    collection = _get_collection()

    for idx, message in enumerate(messages):
        insight_type = ["alignment", "skills", "remote", "source", "matches", "applications"][min(idx, 5)]
        document: dict[str, Any] = {
            "insight_type": insight_type,
            "title": message.split(".")[0][:80],
            "message": message,
            "category": insight_type,
            "metadata": {"missing_skills": missing_skills},
            "preference_id": pref_id,
            "created_at": now,
        }
        if persist:
            result = await collection.insert_one(document)
            document["_id"] = result.inserted_id
        else:
            document["_id"] = f"preview-{idx}"
        insight_docs.append(CareerInsightDocument.from_mongo(document))

    return CareerInsightsSummary(
        insights=insight_docs,
        top_skills_to_learn=missing_skills,
        strongest_alignment=alignment,
        best_source=best_source.split(" gives")[0] if best_source else "",
    )


async def list_career_insights(limit: int = 20) -> list[CareerInsightDocument]:
    collection = _get_collection()
    cursor = collection.find({}).sort("created_at", -1).limit(limit)
    documents = await cursor.to_list(length=limit)
    return [CareerInsightDocument.from_mongo(doc) for doc in documents]


def get_top_missing_skills(jobs: list[JobDocument]) -> list[str]:
    return _top_missing_skills(jobs)


async def get_insight_messages_for_digest(
    preferences: UserPreferencesDocument | None = None,
) -> list[str]:
    summary = await generate_career_insights(preferences, persist=False)
    return [doc.message for doc in summary.insights]

"""Weighted resume-to-job match scoring (deterministic, no LLM)."""

from __future__ import annotations

import logging
import re
from typing import TypedDict

from app.utils.skills_master import (
    TECH_STACK_GROUPS,
    categorize_skills,
    extract_skills_from_text,
)

logger = logging.getLogger(__name__)

WEIGHT_SKILL_OVERLAP = 40
WEIGHT_TECH_STACK = 25
WEIGHT_EXPERIENCE = 15
WEIGHT_LOCATION_REMOTE = 10
WEIGHT_TITLE = 10

SENIORITY_LEVELS = (
    ("intern", 0),
    ("junior", 1),
    ("entry", 1),
    ("associate", 2),
    ("mid", 2),
    ("senior", 3),
    ("lead", 4),
    ("staff", 4),
    ("principal", 5),
    ("architect", 5),
    ("manager", 4),
    ("director", 5),
)

BACKEND_TITLE_HINTS = (
    "backend",
    "back-end",
    "api",
    "platform",
    "infrastructure",
    "devops",
    "sre",
    "python",
    "node",
    "java",
    "golang",
)

FRONTEND_TITLE_HINTS = (
    "frontend",
    "front-end",
    "ui",
    "ux",
    "react",
    "angular",
    "vue",
    "web developer",
)

FULLSTACK_TITLE_HINTS = ("full stack", "fullstack", "full-stack")

REMOTE_HINTS = ("remote", "work from home", "wfh", "distributed", "anywhere")
INDIA_HINTS = (
    "india",
    "bengaluru",
    "bangalore",
    "hyderabad",
    "chennai",
    "pune",
    "mumbai",
    "delhi",
    "noida",
    "gurgaon",
)


class ResumeProfile(TypedDict, total=False):
    skills: list[str]
    experience_keywords: list[str]
    links: list[str]
    raw_text: str


class JobProfile(TypedDict, total=False):
    title: str
    description: str
    location: str
    remote: bool
    experience_level: str


class MatchBreakdown(TypedDict):
    skill_overlap: float
    tech_stack: float
    experience: float
    location_remote: float
    title: float


class JobMatchResult(TypedDict):
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    job_skills: list[str]
    strengths: list[str]
    recommendations: list[str]
    experience_alignment: str
    career_fit: str
    recommendation: str
    why_match: list[str]
    match_breakdown: MatchBreakdown


def _normalize_skill_map(skills: list[str]) -> dict[str, str]:
    return {skill.lower(): skill for skill in skills if skill.strip()}


def _infer_seniority(text: str) -> int:
    text_lower = text.lower()
    level = 2
    for keyword, rank in SENIORITY_LEVELS:
        if keyword in text_lower:
            level = max(level, rank)
    return level


def _dominant_stack(skills: list[str]) -> str:
    groups = categorize_skills(skills)
    scores = {name: len(items) for name, items in groups.items() if items}
    if not scores:
        return "generalist"
    return max(scores, key=scores.get)


def _infer_job_orientation(title: str, description: str) -> str:
    combined = f"{title} {description}".lower()
    if any(hint in combined for hint in FULLSTACK_TITLE_HINTS):
        return "fullstack"
    backend = sum(1 for hint in BACKEND_TITLE_HINTS if hint in combined)
    frontend = sum(1 for hint in FRONTEND_TITLE_HINTS if hint in combined)
    if backend > frontend and backend > 0:
        return "backend"
    if frontend > backend and frontend > 0:
        return "frontend"
    return "generalist"


def _score_skill_overlap(resume_skills: list[str], job_skills: list[str]) -> tuple[float, list[str], list[str]]:
    resume_map = _normalize_skill_map(resume_skills)
    job_map = _normalize_skill_map(job_skills)

    matched = sorted(
        [resume_map[key] for key in job_map if key in resume_map],
        key=str.lower,
    )
    missing = sorted(
        [job_map[key] for key in job_map if key not in resume_map],
        key=str.lower,
    )

    if not job_skills:
        return 0.0, matched, missing

    ratio = len(matched) / len(job_skills)
    return min(WEIGHT_SKILL_OVERLAP, ratio * WEIGHT_SKILL_OVERLAP), matched, missing


def _score_tech_stack(resume_skills: list[str], job_skills: list[str]) -> float:
    if not job_skills:
        return 0.0

    resume_groups = categorize_skills(resume_skills)
    job_groups = categorize_skills(job_skills)

    active_groups = [name for name, items in job_groups.items() if items]
    if not active_groups:
        return WEIGHT_TECH_STACK * 0.5

    overlap_count = 0
    for group_name in active_groups:
        resume_set = {s.lower() for s in resume_groups.get(group_name, [])}
        job_set = {s.lower() for s in job_groups.get(group_name, [])}
        if resume_set & job_set:
            overlap_count += 1

    ratio = overlap_count / len(active_groups)
    return min(WEIGHT_TECH_STACK, ratio * WEIGHT_TECH_STACK)


def _score_experience(
    resume_keywords: list[str],
    job_title: str,
    job_description: str,
) -> float:
    job_text = f"{job_title} {job_description}".lower()
    resume_seniority = _infer_seniority(" ".join(resume_keywords))
    job_seniority = _infer_seniority(job_text)

    seniority_gap = abs(resume_seniority - job_seniority)
    seniority_score = max(0.0, 1.0 - (seniority_gap * 0.25))

    keyword_hits = sum(1 for kw in resume_keywords if kw.lower() in job_text)
    keyword_ratio = min(1.0, keyword_hits / max(len(resume_keywords), 1))

    combined = (seniority_score * 0.6) + (keyword_ratio * 0.4)
    return min(WEIGHT_EXPERIENCE, combined * WEIGHT_EXPERIENCE)


def _score_location_remote(
    resume_text: str,
    job_location: str,
    job_remote: bool,
) -> float:
    resume_lower = resume_text.lower()
    location_lower = (job_location or "").lower()

    score = 0.0
    resume_remote = any(hint in resume_lower for hint in REMOTE_HINTS)
    resume_india = any(hint in resume_lower for hint in INDIA_HINTS)
    job_india = any(hint in location_lower for hint in INDIA_HINTS)

    if job_remote and resume_remote:
        score += WEIGHT_LOCATION_REMOTE * 0.7
    elif job_remote:
        score += WEIGHT_LOCATION_REMOTE * 0.45
    elif job_india and resume_india:
        score += WEIGHT_LOCATION_REMOTE * 0.6
    elif not location_lower or location_lower == "remote":
        score += WEIGHT_LOCATION_REMOTE * 0.4
    else:
        score += WEIGHT_LOCATION_REMOTE * 0.2

    return min(WEIGHT_LOCATION_REMOTE, score)


def _score_title_relevance(resume_skills: list[str], job_title: str) -> float:
    title_lower = job_title.lower()
    if not title_lower.strip():
        return 0.0

    hits = 0
    for skill in resume_skills:
        if skill.lower() in title_lower:
            hits += 1

    title_tokens = re.findall(r"[a-z0-9+#./-]{2,}", title_lower)
    token_hits = sum(
        1
        for token in title_tokens
        if any(token in skill.lower() or skill.lower() in token for skill in resume_skills)
    )

    combined_hits = hits + min(token_hits, 3)
    ratio = min(1.0, combined_hits / 4)
    return min(WEIGHT_TITLE, ratio * WEIGHT_TITLE)


def _recommendation_for_score(match_score: int) -> str:
    if match_score >= 90:
        return "Excellent Match"
    if match_score >= 75:
        return "Strong Match"
    if match_score >= 50:
        return "Moderate Match"
    return "Weak Match"


def score_resume_against_job(
    resume: ResumeProfile,
    job: JobProfile,
) -> JobMatchResult:
    """Compute weighted match score and structured match payload."""
    resume_skills = list(resume.get("skills") or [])
    resume_keywords = list(resume.get("experience_keywords") or [])
    resume_text = " ".join(
        filter(
            None,
            [
                resume.get("raw_text", ""),
                " ".join(resume_skills),
                " ".join(resume_keywords),
            ],
        )
    )

    title = str(job.get("title") or "")
    description = str(job.get("description") or "")
    location = str(job.get("location") or "")
    remote = bool(job.get("remote"))
    job_text = f"{title} {description} {location}"

    job_skills = extract_skills_from_text(job_text)
    if title and not job_skills:
        job_skills = extract_skills_from_text(title)

    skill_pts, matched_skills, missing_skills = _score_skill_overlap(resume_skills, job_skills)
    tech_pts = _score_tech_stack(resume_skills, job_skills)
    exp_pts = _score_experience(resume_keywords, title, description)
    loc_pts = _score_location_remote(resume_text, location, remote)
    title_pts = _score_title_relevance(resume_skills, title)

    raw_score = skill_pts + tech_pts + exp_pts + loc_pts + title_pts
    match_score = max(0, min(100, round(raw_score)))
    # Keep jobs visible when at least one skill overlaps — user decides whether to apply.
    if matched_skills:
        floor = min(45, 10 + len(matched_skills) * 5)
        match_score = max(match_score, floor)

    breakdown: MatchBreakdown = {
        "skill_overlap": round(skill_pts, 2),
        "tech_stack": round(tech_pts, 2),
        "experience": round(exp_pts, 2),
        "location_remote": round(loc_pts, 2),
        "title": round(title_pts, 2),
    }

    from app.services.job_insight_service import generate_job_insights

    insights = generate_job_insights(
        match_score=match_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        resume_skills=resume_skills,
        resume_keywords=resume_keywords,
        job_title=title,
        job_description=description,
        job_remote=remote,
        job_location=location,
    )

    logger.info(
        "Match v2: score=%d skill=%.1f tech=%.1f exp=%.1f loc=%.1f title=%.1f",
        match_score,
        skill_pts,
        tech_pts,
        exp_pts,
        loc_pts,
        title_pts,
    )

    return JobMatchResult(
        match_score=match_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        job_skills=job_skills,
        strengths=insights["strengths"],
        recommendations=insights["recommendations"],
        experience_alignment=insights["experience_alignment"],
        career_fit=insights["career_fit"],
        recommendation=_recommendation_for_score(match_score),
        why_match=insights["why_match"],
        match_breakdown=breakdown,
    )

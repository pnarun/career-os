"""Fetch job-specific interview questions from the web (DuckDuckGo + page scrape).

LLM generation can replace this layer later; for now questions come from
public interview prep pages found via search.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any
import requests
from ddgs import DDGS

from app.core.database import get_database

logger = logging.getLogger(__name__)

CACHE_COLLECTION = "interview_web_questions_cache"
CACHE_TTL_HOURS = 24
FETCH_TIMEOUT_SEC = 8
MAX_PAGES_TO_FETCH = 4
MAX_QUESTIONS_PER_CATEGORY = 10

BEHAVIORAL_HINTS = (
    "tell me about",
    "describe a time",
    "describe when",
    "how do you handle",
    "give an example",
    "situation where",
    "conflict",
    "deadline",
    "team",
    "mistake",
    "failure",
    "leadership",
)

SYSTEM_DESIGN_HINTS = (
    "design a",
    "design an",
    "architect",
    "scale",
    "system design",
    "how would you build",
)

NOISE_PATTERNS = (
    "cookie",
    "subscribe",
    "sign up",
    "sign in",
    "register",
    "javascript:",
    "click here",
    "privacy policy",
    "are you interested to work",
    "do you want to work with",
    "inside scoop",
    "is this your company",
    "add an interview",
    "log in",
    "create account",
    "terms of service",
    "all rights reserved",
    "follow us",
    "newsletter",
    "where can i find",
    "interview questions [",
    "common stages of the interview",
    "according to",
)

PREFERRED_URL_HINTS = (
    "interview",
    "question",
    "glassdoor",
    "leetcode",
    "geeksforgeeks",
    "interviewbit",
    "indeed.com/hire",
    "prep",
    "coding",
)


def _cache_key(job_id: str, job_title: str, company: str) -> str:
    if job_id.strip():
        return f"job:{job_id.strip()}"
    raw = f"{job_title.lower()}|{company.lower()}"
    return f"hash:{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _extract_questions_from_html(html: str) -> list[str]:
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    candidates: list[str] = []
    for match in re.finditer(r"[^.?!]{15,350}\?", text):
        q = match.group(0).strip()
        q = re.sub(r"^\d+[\).\s]+", "", q)
        q = re.sub(r"^[-•*]\s*", "", q)
        if _is_valid_question(q):
            candidates.append(q)

    return candidates


def _is_valid_question(q: str) -> bool:
    lower = q.lower()
    if len(q) < 25 or len(q) > 320:
        return False
    if any(noise in lower for noise in NOISE_PATTERNS):
        return False
    if lower.count("?") > 1:
        return False
    # Must start with a letter (filters UI fragments and encoding junk)
    if not q.lstrip()[0].isalpha():
        return False
    # Reject questions that are mostly non-ASCII / garbled
    ascii_chars = sum(1 for c in q if ord(c) < 128)
    if ascii_chars / max(len(q), 1) < 0.85:
        return False
    return True


def _categorize_question(q: str) -> str:
    lower = q.lower()
    if any(h in lower for h in SYSTEM_DESIGN_HINTS):
        return "system_design"
    if any(h in lower for h in BEHAVIORAL_HINTS):
        return "behavioral"
    return "technical"


def _score_search_result(result: dict[str, str]) -> int:
    href = (result.get("href") or "").lower()
    title = (result.get("title") or "").lower()
    body = (result.get("body") or "").lower()
    score = 0
    for hint in PREFERRED_URL_HINTS:
        if hint in href or hint in title:
            score += 3
    if "interview" in body:
        score += 1
    if any(skip in href for skip in ("/jobs/", "/job/", "cutshort.io/jobs")):
        score -= 2
    return score


def _build_search_queries(job_title: str, company: str, skills: list[str]) -> list[str]:
    title = job_title.strip()
    comp = company.strip()
    skill_str = " ".join(skills[:4])
    queries = [
        f'"{title}" "{comp}" interview questions',
        f"{title} {comp} technical interview questions",
        f"{title} interview questions {skill_str}".strip(),
        f"{comp} {title} coding interview questions",
    ]
    return [q for q in queries if len(q) > 10]


def _fetch_questions_sync(
    *,
    job_title: str,
    company: str,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    skills = skills or []
    queries = _build_search_queries(job_title, company, skills)
    seen_urls: set[str] = set()
    ranked_results: list[dict[str, str]] = []

    try:
        with DDGS() as ddgs:
            for query in queries:
                try:
                    for result in ddgs.text(query, max_results=6):
                        href = result.get("href") or ""
                        if not href or href in seen_urls:
                            continue
                        seen_urls.add(href)
                        ranked_results.append(result)
                except Exception as exc:
                    logger.warning("Web search failed for query=%s: %s", query, exc)
    except Exception as exc:
        logger.warning("DDGS init failed: %s", exc)
        return _empty_result(source="search_unavailable")

    ranked_results.sort(key=_score_search_result, reverse=True)

    all_questions: list[dict[str, str]] = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    pages_fetched = 0
    for result in ranked_results:
        if pages_fetched >= MAX_PAGES_TO_FETCH:
            break
        href = result.get("href") or ""
        if not href.startswith("http"):
            continue
        try:
            resp = requests.get(href, timeout=FETCH_TIMEOUT_SEC, headers=headers)
            if resp.status_code != 200:
                continue
            pages_fetched += 1
            extracted = _extract_questions_from_html(resp.text)
            for q in extracted:
                all_questions.append({
                    "question": q,
                    "category": _categorize_question(q),
                    "topic": "web",
                    "source": href,
                    "source_title": result.get("title", "")[:120],
                })
        except Exception as exc:
            logger.debug("Failed to fetch %s: %s", href, exc)

    # Also mine question-like phrases from search snippets
    for result in ranked_results[:8]:
        body = result.get("body") or ""
        for q in _extract_questions_from_html(body + "?"):
            all_questions.append({
                "question": q,
                "category": _categorize_question(q),
                "topic": "web_snippet",
                "source": result.get("href", ""),
                "source_title": result.get("title", "")[:120],
            })

    deduped = _dedupe_questions(all_questions)

    technical = [q for q in deduped if q["category"] == "technical"][:MAX_QUESTIONS_PER_CATEGORY]
    behavioral = [q for q in deduped if q["category"] == "behavioral"][:MAX_QUESTIONS_PER_CATEGORY]
    system_design = [q for q in deduped if q["category"] == "system_design"][:6]

    return {
        "technical_questions": technical,
        "behavioral_questions": behavioral,
        "system_design_prompts": system_design,
        "source": "web",
        "pages_fetched": pages_fetched,
        "search_queries": queries,
        "total_found": len(deduped),
    }


def _dedupe_questions(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for item in items:
        key = re.sub(r"\s+", " ", item["question"].lower().strip())
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _empty_result(source: str = "none") -> dict[str, Any]:
    return {
        "technical_questions": [],
        "behavioral_questions": [],
        "system_design_prompts": [],
        "source": source,
        "pages_fetched": 0,
        "search_queries": [],
        "total_found": 0,
    }


async def _get_cached(key: str) -> dict[str, Any] | None:
    try:
        doc = await get_database()[CACHE_COLLECTION].find_one({"cache_key": key})
        if not doc:
            return None
        expires = doc.get("expires_at")
        if expires and isinstance(expires, datetime) and expires < _utc_now():
            return None
        return doc.get("payload")
    except Exception:
        return None


async def _set_cached(key: str, payload: dict[str, Any]) -> None:
    try:
        col = get_database()[CACHE_COLLECTION]
        await col.update_one(
            {"cache_key": key},
            {
                "$set": {
                    "cache_key": key,
                    "payload": payload,
                    "expires_at": _utc_now() + timedelta(hours=CACHE_TTL_HOURS),
                    "updated_at": _utc_now().isoformat(),
                }
            },
            upsert=True,
        )
    except Exception as exc:
        logger.warning("Failed to cache web questions: %s", exc)


async def ensure_web_question_cache_indexes() -> None:
    col = get_database()[CACHE_COLLECTION]
    await col.create_index("cache_key", unique=True)
    await col.create_index("expires_at", expireAfterSeconds=0)


async def fetch_web_interview_questions(
    *,
    job_id: str = "",
    job_title: str = "",
    company: str = "",
    skills: list[str] | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Fetch job-specific questions from the web; cached 24h per job."""
    if not job_title.strip() and not company.strip():
        return _empty_result()

    key = _cache_key(job_id, job_title, company)
    if use_cache:
        cached = await _get_cached(key)
        if cached:
            cached["source"] = cached.get("source", "web_cache")
            return cached

    payload = await asyncio.to_thread(
        _fetch_questions_sync,
        job_title=job_title,
        company=company,
        skills=skills or [],
    )
    payload["cached_at"] = _utc_now().isoformat()

    if payload.get("total_found", 0) > 0:
        await _set_cached(key, payload)

    return payload

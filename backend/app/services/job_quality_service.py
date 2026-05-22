import logging
import re
from typing import Any, Literal, TypedDict
from urllib.parse import urlparse

from app.services.job_filter_service import (
    ENGINEERING_REJECT_KEYWORDS,
    is_india_location_job,
    is_remote_job,
    is_relevant_engineering_job,
)

logger = logging.getLogger(__name__)

MIN_QUALITY_SCORE = 30
MIN_TITLE_LENGTH = 5
MAX_SCORE = 100

QualityRejectionReason = Literal["suspicious", "low_quality_score"]

_QUALITY_REJECTION_BUFFER: list[dict[str, Any]] = []
_QUALITY_REJECTION_MAX = 500

SPAM_KEYWORDS = (
    "earn money",
    "work from home earn",
    "no experience needed",
    "urgent hiring",
    "click here",
    "limited slots",
    "guaranteed income",
    "mlm",
    "pyramid",
    "crypto mining",
    "whatsapp only",
    "telegram only",
)

DUPLICATE_SPAM_KEYWORDS = (
    "hiring now hiring",
    "apply apply apply",
    "remote remote remote",
    "work from home work from home",
)

SUSPICIOUS_TITLE_PATTERNS = (
    r"^\$\d+",
    r"!!!+",
    r"\bfree\b.*\bmoney\b",
    r"\btest\b.*\bjob\b",
)


class QualityEvaluableJob(TypedDict, total=False):
    title: str
    company: str
    location: str
    apply_url: str
    source: str
    description: str
    easy_apply: bool
    match_percentage: int
    remote_priority: bool
    india_focused: bool
    job_type: str
    tags: list[str]


class JobQualityResult(TypedDict):
    has_apply_url: bool
    is_easy_apply_possible: bool
    job_quality_score: int
    is_suspicious: bool
    quality_flags: list[str]


def is_valid_apply_url(url: str | None) -> bool:
    """True when apply URL is safe and usable for automation prep."""
    raw = (url or "").strip()
    if not raw:
        return False

    lower = raw.lower()
    if lower.startswith("javascript:") or "void(0)" in lower:
        return False
    if not (lower.startswith("http://") or lower.startswith("https://")):
        return False
    if "localhost" in lower or "127.0.0.1" in lower or "0.0.0.0" in lower:
        return False
    if " " in raw:
        return False

    try:
        parsed = urlparse(raw)
        if not parsed.netloc:
            return False
        if "." not in parsed.netloc:
            return False
        return True
    except ValueError:
        return False


def _job_text(job: QualityEvaluableJob) -> str:
    parts = (
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("description", ""),
        job.get("job_type", ""),
    )
    return " ".join(part for part in parts if part).lower()


def _has_valid_location(job: QualityEvaluableJob) -> bool:
    location = (job.get("location") or "").strip()
    return len(location) >= 2


def _has_description(job: QualityEvaluableJob) -> bool:
    return len((job.get("description") or "").strip()) >= 50


def _detect_spam_signals(text: str) -> bool:
    return any(keyword in text for keyword in SPAM_KEYWORDS)


def _detect_duplicate_spam(text: str) -> bool:
    return any(keyword in text for keyword in DUPLICATE_SPAM_KEYWORDS)


def _detect_suspicious_title(title: str) -> bool:
    if len(title.strip()) < MIN_TITLE_LENGTH:
        return True
    for pattern in SUSPICIOUS_TITLE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return True
    return False


def _is_malformed_apply_url(url: str) -> bool:
    raw = (url or "").strip()
    if not raw:
        return True
    return not is_valid_apply_url(raw)


def evaluate_job_quality(job: QualityEvaluableJob) -> JobQualityResult:
    """
    Score job usefulness and apply readiness.
    Does not persist; call after filter + match in the storage pipeline.
    """
    title = (job.get("title") or "").strip()
    company = (job.get("company") or "").strip()
    apply_url = (job.get("apply_url") or "").strip()
    text = _job_text(job)
    match_pct = int(job.get("match_percentage") or 0)

    flags: list[str] = []
    score = 0
    penalties: list[str] = []

    has_url = is_valid_apply_url(apply_url)
    if has_url:
        score += 20
        flags.append("valid_apply_url")
    else:
        penalties.append("missing_or_invalid_apply_url")

    if company:
        score += 10
        flags.append("valid_company")
    else:
        penalties.append("blank_company")

    if is_relevant_engineering_job(job):
        score += 15
        flags.append("engineering_title")
    else:
        penalties.append("non_engineering_signals")
        score -= 25

    if _has_valid_location(job):
        score += 5
        flags.append("valid_location")

    if _has_description(job):
        score += 10
        flags.append("has_description")

    if match_pct > 50:
        score += 15
        flags.append("strong_match")

    if job.get("remote_priority") or is_remote_job(job):
        score += 10
        flags.append("remote_role")

    if job.get("india_focused") or is_india_location_job(job):
        score += 10
        flags.append("india_role")

    if _detect_suspicious_title(title):
        score -= 20
        penalties.append("suspicious_title")

    if not has_url:
        score -= 30

    if not company:
        score -= 25

    if apply_url and _is_malformed_apply_url(apply_url):
        score -= 20
        penalties.append("malformed_url")

    if any(keyword in text for keyword in ENGINEERING_REJECT_KEYWORDS):
        score -= 15
        if "non_engineering_signals" not in penalties:
            penalties.append("non_engineering_signals")

    if _detect_spam_signals(text):
        score -= 30
        penalties.append("spam_keywords")

    if _detect_duplicate_spam(text):
        score -= 15
        penalties.append("duplicate_spam")

    score = max(0, min(MAX_SCORE, score))

    is_suspicious = (
        len(title) < MIN_TITLE_LENGTH
        or not company
        or not has_url
        or (not _has_valid_location(job) and not _has_description(job))
        or _detect_spam_signals(text)
        or _detect_suspicious_title(title)
    )

    if is_suspicious and "suspicious_job" not in flags:
        flags.append("suspicious_job")

    if not is_suspicious and score >= 70 and has_url and company:
        flags.append("verified")

    easy_apply = bool(job.get("easy_apply", False))
    is_easy_apply_possible = easy_apply and has_url

    if is_easy_apply_possible:
        flags.append("easy_apply_ready")

    return JobQualityResult(
        has_apply_url=has_url,
        is_easy_apply_possible=is_easy_apply_possible,
        job_quality_score=score,
        is_suspicious=is_suspicious,
        quality_flags=flags,
    )


def get_quality_rejection_reason(result: JobQualityResult) -> QualityRejectionReason | None:
    if result["is_suspicious"]:
        return "suspicious"
    if result["job_quality_score"] < MIN_QUALITY_SCORE:
        return "low_quality_score"
    return None


def should_reject_by_quality(result: JobQualityResult) -> bool:
    return get_quality_rejection_reason(result) is not None


def apply_quality_to_job(job: dict[str, Any]) -> dict[str, Any]:
    """Merge quality evaluation fields onto a job dict."""
    quality = evaluate_job_quality(job)
    return {**job, **quality}


def log_quality_rejected_job(
    job: QualityEvaluableJob,
    result: JobQualityResult,
    reason: QualityRejectionReason,
) -> None:
    entry = {
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "source": job.get("source", ""),
        "rejection_reason": reason,
        "job_quality_score": result["job_quality_score"],
        "is_suspicious": result["is_suspicious"],
        "quality_flags": result["quality_flags"],
    }
    _QUALITY_REJECTION_BUFFER.append(entry)
    if len(_QUALITY_REJECTION_BUFFER) > _QUALITY_REJECTION_MAX:
        del _QUALITY_REJECTION_BUFFER[: len(_QUALITY_REJECTION_BUFFER) - _QUALITY_REJECTION_MAX]

    tag = "SUSPICIOUS" if reason == "suspicious" else "LOW_QUALITY"
    logger.warning(
        "[REJECTED][QUALITY][%s] score=%d suspicious=%s\n%s\n%s — %s\nflags=%s",
        tag,
        result["job_quality_score"],
        result["is_suspicious"],
        entry["title"],
        entry["company"],
        entry["location"] or "N/A",
        ", ".join(result["quality_flags"]) or "none",
    )


def filter_jobs_by_quality(jobs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Evaluate quality, reject suspicious/low-score jobs, return (accepted, rejected_count)."""
    accepted: list[dict[str, Any]] = []
    rejected = 0

    for job in jobs:
        enriched = apply_quality_to_job(job)
        reason = get_quality_rejection_reason(enriched)
        if reason is None:
            accepted.append(enriched)
        else:
            log_quality_rejected_job(job, enriched, reason)
            rejected += 1

    logger.info(
        "Job quality gate: accepted=%d rejected=%d",
        len(accepted),
        rejected,
    )
    return accepted, rejected


def get_recent_quality_rejection_logs(limit: int = 100) -> list[dict[str, Any]]:
    return list(_QUALITY_REJECTION_BUFFER[-limit:])

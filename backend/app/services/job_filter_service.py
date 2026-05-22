import logging
from typing import Literal, TypedDict

logger = logging.getLogger(__name__)

RejectionReason = Literal["location_filter", "non_engineering"]

# In-memory ring buffer for temporary diagnostics (not persisted).
_REJECTION_LOG_BUFFER: list[dict[str, str]] = []
_REJECTION_LOG_MAX = 500

INDIA_LOCATION_KEYWORDS = (
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
    "gurugram",
    "kochi",
    "ahmedabad",
    "bombay",
    "ncr",
)

REJECT_LOCATION_KEYWORDS = (
    "germany",
    "austria",
    "france",
    "poland",
    "netherlands",
    "europe only",
    "europe-only",
    "berlin",
    "munich",
    "vienna",
    "paris",
    "amsterdam",
    "warsaw",
    "zurich",
    "switzerland",
    "belgium",
    "spain",
    "italy",
    "uk only",
    "united kingdom only",
)

REMOTE_KEYWORDS = (
    "remote",
    "work from home",
    "work-from-home",
    "wfh",
    "anywhere",
    "distributed team",
    "distributed",
    "fully remote",
    "remote-first",
    "remote first",
    "global remote",
)

ENGINEERING_ALLOW_KEYWORDS = (
    "software engineer",
    "software engineering",
    "full stack",
    "fullstack",
    "backend",
    "frontend",
    "front-end",
    "back-end",
    "devops",
    "cloud",
    "platform engineer",
    "site reliability",
    "sre",
    "automation engineer",
    "ai engineer",
    "ml engineer",
    "machine learning engineer",
    "python developer",
    "react developer",
    "node.js",
    "nodejs",
    "fastapi",
    "aws",
    "developer",
    "engineering",
    "software development",
)

ENGINEERING_REJECT_KEYWORDS = (
    "finance manager",
    "financial analyst",
    "sales manager",
    "sales executive",
    "account executive",
    "hr manager",
    "human resources",
    "recruiter",
    "marketing manager",
    "marketing specialist",
    "medical",
    "nurse",
    "physician",
    "accounting",
    "accountant",
    "customer support",
    "customer service",
    "call center",
    "manufacturing operator",
    "mechanical technician",
    "civil engineer",
    "business development",
    "legal counsel",
    "compliance officer",
)


class FilterableJob(TypedDict, total=False):
    title: str
    company: str
    location: str
    description: str
    job_type: str
    tags: list[str]
    source: str


def _job_text(job: FilterableJob) -> str:
    tags = job.get("tags") or []
    tag_text = " ".join(tags) if isinstance(tags, list) else str(tags)
    parts = (
        job.get("location", ""),
        job.get("description", ""),
        job.get("title", ""),
        job.get("job_type", ""),
        tag_text,
    )
    return " ".join(part for part in parts if part).lower()


def is_remote_job(job: FilterableJob) -> bool:
    """Detect remote-friendly roles."""
    text = _job_text(job)
    if any(keyword in text for keyword in REMOTE_KEYWORDS):
        return True
    return "remote" in (job.get("job_type") or "").lower()


def is_india_location_job(job: FilterableJob) -> bool:
    """Detect India-based locations."""
    text = _job_text(job)
    return any(keyword in text for keyword in INDIA_LOCATION_KEYWORDS)


def _is_rejected_international_only(job: FilterableJob) -> bool:
    """Reject Europe/international-only roles without India or remote signals."""
    text = _job_text(job)

    if not any(keyword in text for keyword in REJECT_LOCATION_KEYWORDS):
        return False

    if is_india_location_job(job) or is_remote_job(job):
        return False

    return True


def is_india_or_remote_job(job: FilterableJob) -> bool:
    """Allow India-based or remote-friendly engineering opportunities."""
    if _is_rejected_international_only(job):
        return False

    return is_india_location_job(job) or is_remote_job(job)


def is_relevant_engineering_job(job: FilterableJob) -> bool:
    """Allow engineering roles and reject unrelated business functions."""
    text = _job_text(job)

    if any(keyword in text for keyword in ENGINEERING_REJECT_KEYWORDS):
        return False

    return any(keyword in text for keyword in ENGINEERING_ALLOW_KEYWORDS)


def get_rejection_reason(job: FilterableJob) -> RejectionReason | None:
    """Return why a job failed filters, or None if it passes."""
    if not is_relevant_engineering_job(job):
        return "non_engineering"
    if not is_india_or_remote_job(job):
        return "location_filter"
    return None


def passes_job_filters(job: FilterableJob) -> bool:
    """Single gate for India/remote + engineering relevance."""
    return get_rejection_reason(job) is None


def log_rejected_job(job: FilterableJob, rejection_reason: RejectionReason) -> None:
    """Log rejection to console and temporary in-memory buffer."""
    entry = {
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "location": job.get("location", ""),
        "source": job.get("source", ""),
        "rejection_reason": rejection_reason,
    }

    _REJECTION_LOG_BUFFER.append(entry)
    if len(_REJECTION_LOG_BUFFER) > _REJECTION_LOG_MAX:
        del _REJECTION_LOG_BUFFER[: len(_REJECTION_LOG_BUFFER) - _REJECTION_LOG_MAX]

    tag = "LOCATION" if rejection_reason == "location_filter" else "NON_ENGINEERING"
    logger.warning(
        "[REJECTED][%s]\n%s\n%s — %s\nsource=%s",
        tag,
        entry["title"],
        entry["company"],
        entry["location"] or "N/A",
        entry["source"] or "unknown",
    )


def get_recent_rejection_logs(limit: int = 100) -> list[dict[str, str]]:
    """Return recent in-memory rejection entries (debug only)."""
    return list(_REJECTION_LOG_BUFFER[-limit:])


def enrich_job_filter_metadata(job: FilterableJob) -> dict:
    """Attach prioritization metadata used for storage and sorting."""
    return {
        **job,
        "remote_priority": is_remote_job(job),
        "india_focused": is_india_location_job(job),
    }


def filter_normalized_jobs(jobs: list[dict]) -> tuple[list[dict], int]:
    """
    Filter normalized jobs through India/remote and engineering rules.
    Returns (accepted_jobs, rejected_count).
    """
    accepted: list[dict] = []
    rejected_count = 0

    for job in jobs:
        reason = get_rejection_reason(job)
        if reason is None:
            accepted.append(enrich_job_filter_metadata(job))
        else:
            log_rejected_job(job, reason)
            rejected_count += 1

    logger.info(
        "Job filter applied: accepted=%d rejected=%d",
        len(accepted),
        rejected_count,
    )
    return accepted, rejected_count

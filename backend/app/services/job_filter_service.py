import logging
from typing import Literal, TypedDict

logger = logging.getLogger(__name__)

RejectionReason = Literal["location_filter"]

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
    "karnataka",
    "maharashtra",
    "tamil nadu",
    "telangana",
)

FOREIGN_ONSITE_KEYWORDS = (
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
    "london, uk",
    "london, england",
    "manchester, uk",
    "united states",
    "united states of america",
    "usa",
    ", us",
    " u.s.",
    "new york",
    "san francisco",
    "california",
    "texas",
    "seattle",
    "boston",
    "chicago",
    "austin",
    "denver",
    "atlanta",
    "washington dc",
    "canada",
    "toronto",
    "vancouver",
    "montreal",
    "sydney",
    "melbourne",
    "singapore only",
)

# Soft signals for quality scoring only — not used to drop jobs from the feed.
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
    "work from anywhere",
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


def _has_foreign_onsite_signal(job: FilterableJob) -> bool:
    """True when location text clearly points to a non-India, non-remote onsite role."""
    text = _job_text(job)
    if not text.strip():
        return False
    return any(keyword in text for keyword in FOREIGN_ONSITE_KEYWORDS)


def is_foreign_onsite_only(job: FilterableJob) -> bool:
    """Foreign location without India or remote — not actionable for most Indian applicants."""
    if is_india_location_job(job) or is_remote_job(job):
        return False
    return _has_foreign_onsite_signal(job)


def is_actionable_for_india_user(job: FilterableJob) -> bool:
    """User can realistically apply: India onsite/hybrid or remote; not foreign onsite."""
    if is_foreign_onsite_only(job):
        return False
    if is_india_location_job(job) or is_remote_job(job):
        return True
    # Unknown/empty location: keep visible but not promoted as high-match India role
    return not _has_foreign_onsite_signal(job)


def is_india_or_remote_job(job: FilterableJob) -> bool:
    """Legacy helper — India or remote-friendly."""
    return is_india_location_job(job) or is_remote_job(job)


def is_relevant_engineering_job(job: FilterableJob) -> bool:
    """Soft signal for quality scoring only — not used to drop jobs from the feed."""
    text = _job_text(job)
    engineering_hints = (
        "developer",
        "engineer",
        "engineering",
        "architect",
        "devops",
        "sre",
        "full stack",
        "fullstack",
        "software",
        "backend",
        "frontend",
        "consultant",
        "analyst",
        "manager",
        "lead",
        "specialist",
    )
    return any(hint in text for hint in engineering_hints)


def get_rejection_reason(job: FilterableJob) -> RejectionReason | None:
    """
    Hard reject only clear foreign onsite roles (no India, no remote).
    All other jobs pass through for match scoring and sorting.
    """
    if is_foreign_onsite_only(job):
        return "location_filter"
    return None


def passes_job_filters(job: FilterableJob) -> bool:
    """Location gate for fetch pipeline — does not filter by role or skills."""
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

    logger.warning(
        "[REJECTED][LOCATION]\n%s\n%s — %s\nsource=%s",
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
        "actionable_in_india": is_actionable_for_india_user(job),
        "foreign_onsite_only": is_foreign_onsite_only(job),
    }


def filter_normalized_jobs(jobs: list[dict]) -> tuple[list[dict], int]:
    """
    Drop only foreign onsite roles (no India, no remote).
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
        "Job location filter: accepted=%d rejected_foreign_onsite=%d",
        len(accepted),
        rejected_count,
    )
    return accepted, rejected_count

import hashlib
import logging
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from html import unescape
from typing import Any

from app.services.job_sources.base.provider_diagnostics import (
    ProviderFetchLogger,
    diagnostic_from_exception,
    finalize_diagnostic,
)
from app.services.job_sources.base.source_result import (
    NormalizedSourceJob,
    RawSourceJob,
    SourceFetchResult,
)

logger = logging.getLogger(__name__)


class BaseJobSource(ABC):
    """Abstract adapter for a single job provider."""

    source_name: str = "unknown"
    request_timeout: int = 25
    max_retries: int = 2

    @abstractmethod
    async def fetch_jobs(self) -> SourceFetchResult:
        """Fetch and normalize jobs from the provider."""

    def normalize_job(self, raw_job: RawSourceJob) -> NormalizedSourceJob | None:
        """Map raw provider job into unified schema. Return None to skip."""
        title = self.sanitize_text(raw_job.title)
        company = self.sanitize_text(raw_job.company)
        apply_url = (raw_job.apply_url or "").strip()

        if not title or not company:
            return None

        location = self.normalize_location(raw_job.location, remote=raw_job.remote)
        fetch_ts = self._utc_now_iso()

        return NormalizedSourceJob(
            source=raw_job.source or self.source_name,
            source_job_id=raw_job.source_job_id or self.build_job_hash(title, company, apply_url),
            title=title,
            company=company,
            location=location,
            remote=raw_job.remote,
            apply_url=apply_url,
            description=self.sanitize_text(raw_job.description, max_length=8000),
            posted_at=raw_job.posted_at or "",
            fetch_timestamp=fetch_ts,
            metadata=dict(raw_job.metadata),
            tags=list(self.safe_get(raw_job.metadata, "tags", default=[]) or []),
            job_type="remote" if raw_job.remote else "",
        )

    @staticmethod
    def sanitize_text(value: Any, max_length: int = 2000) -> str:
        if value is None:
            return ""
        text = unescape(str(value))
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if max_length and len(text) > max_length:
            return text[:max_length].rstrip() + "…"
        return text

    @staticmethod
    def normalize_location(location: str, *, remote: bool = False) -> str:
        cleaned = BaseJobSource.sanitize_text(location, max_length=200)
        if remote and cleaned and "remote" not in cleaned.lower():
            return f"{cleaned} · Remote"
        if remote and not cleaned:
            return "Remote"
        return cleaned or ("Remote" if remote else "")

    @staticmethod
    def safe_get(data: Any, key: str, default: Any = None) -> Any:
        if isinstance(data, dict):
            return data.get(key, default)
        return getattr(data, key, default)

    @staticmethod
    def build_job_hash(title: str, company: str, apply_url: str = "") -> str:
        raw = f"{title.strip().lower()}|{company.strip().lower()}|{apply_url.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def run_fetch(self) -> SourceFetchResult:
        """Execute fetch with timing, diagnostics, and isolated error handling."""
        log = ProviderFetchLogger(self.source_name)
        log.started()
        started = time.perf_counter()
        try:
            result = await self.fetch_jobs()
            duration_ms = int((time.perf_counter() - started) * 1000)
            result.duration_ms = duration_ms
            result.fetched_count = len(result.jobs)
            result.diagnostic = finalize_diagnostic(
                self.source_name,
                jobs=result.jobs,
                duration_ms=duration_ms,
                error=result.error,
                explicit=result.diagnostic,
            )
            if result.diagnostic.status != "success":
                result.error = result.error or result.diagnostic.error_message
            return result
        except Exception as exc:
            duration_ms = int((time.perf_counter() - started) * 1000)
            diagnostic = diagnostic_from_exception(
                self.source_name, exc, duration_ms=duration_ms
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                fetched_count=0,
                error=diagnostic.error_message,
                duration_ms=duration_ms,
                diagnostic=diagnostic,
            )

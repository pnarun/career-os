from typing import Any

from app.services.job_quality_service import is_valid_apply_url
from app.services.job_sources.base.base_source import BaseJobSource
from app.services.job_sources.base.http_client import fetch_json
from app.services.job_sources.base.provider_diagnostics import (
    ProviderFetchLogger,
    diagnostic_failure,
)
from app.services.job_sources.base.source_result import RawSourceJob, SourceFetchResult

ARBEITNOW_API_URL = "https://arbeitnow.com/api/job-board-api"


class ArbeitnowJobSource(BaseJobSource):
    source_name = "arbeitnow"

    async def fetch_jobs(self) -> SourceFetchResult:
        log = ProviderFetchLogger(self.source_name)

        try:
            payload = await fetch_json(ARBEITNOW_API_URL)
        except Exception as exc:
            raise RuntimeError(f"Arbeitnow API request failed: {exc}") from exc

        log.step(f"JSON loaded type={type(payload).__name__}")

        if not isinstance(payload, dict):
            message = f"Arbeitnow API returned unexpected payload type: {type(payload).__name__}"
            diagnostic = diagnostic_failure(
                self.source_name,
                error_type="parsing_failure",
                error_message=message,
            )
            return SourceFetchResult(
                source=self.source_name,
                jobs=[],
                error=message,
                diagnostic=diagnostic,
            )

        data_items = payload.get("data") or []
        log.step(f"JSON data[] listings={len(data_items) if isinstance(data_items, list) else 0}")

        normalized = []
        for item in data_items:
            if not isinstance(item, dict):
                continue
            raw = self._item_to_raw(item)
            if not raw.apply_url or not is_valid_apply_url(raw.apply_url):
                continue
            job = self.normalize_job(raw)
            if job:
                job_types = item.get("job_types") or []
                if isinstance(job_types, list) and job_types:
                    job.job_type = ", ".join(str(t) for t in job_types)
                if item.get("remote"):
                    job.job_type = f"remote{', ' + job.job_type if job.job_type else ''}".strip(", ")
                normalized.append(job)

        log.parsed(len(normalized), raw_count=len(data_items) if isinstance(data_items, list) else 0)
        return SourceFetchResult(source=self.source_name, jobs=normalized)

    def _item_to_raw(self, item: dict[str, Any]) -> RawSourceJob:
        title = (item.get("title") or "").strip()
        company = (item.get("company_name") or item.get("company") or "").strip()
        location = (item.get("location") or "Remote").strip()
        apply_url = self._normalize_apply_url(item.get("url") or "")
        is_remote = bool(item.get("remote"))
        source_id = str(item.get("slug") or item.get("id") or self.build_job_hash(title, company, apply_url))

        return RawSourceJob(
            source=self.source_name,
            source_job_id=source_id,
            title=title,
            company=company,
            location=location,
            remote=is_remote,
            apply_url=apply_url,
            description=item.get("description") or "",
            posted_at=str(item.get("created_at") or ""),
            metadata={"tags": item.get("tags") or [], "job_types": item.get("job_types") or []},
            raw_payload=item,
        )

    @staticmethod
    def _normalize_apply_url(url: str) -> str:
        url = (url or "").strip()
        if url.startswith("//"):
            return f"https:{url}"
        return url

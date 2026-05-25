from typing import Any

from app.services.job_quality_service import is_valid_apply_url
from app.services.job_sources.base.base_source import BaseJobSource
from app.services.job_sources.base.http_client import fetch_json
from app.services.job_sources.base.provider_diagnostics import (
    ProviderFetchLogger,
    diagnostic_failure,
)
from app.services.job_sources.base.source_result import RawSourceJob, SourceFetchResult

REMOTEOK_API_URL = "https://remoteok.com/api"


class RemoteOKJobSource(BaseJobSource):
    source_name = "remoteok"

    async def fetch_jobs(self) -> SourceFetchResult:
        log = ProviderFetchLogger(self.source_name)

        try:
            payload = await fetch_json(REMOTEOK_API_URL)
        except Exception as exc:
            raise RuntimeError(f"RemoteOK API request failed: {exc}") from exc

        log.step(f"JSON loaded type={type(payload).__name__}")

        if not isinstance(payload, list):
            message = f"RemoteOK API returned unexpected payload type: {type(payload).__name__}"
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

        normalized = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            if "position" not in item and "company" not in item:
                continue

            raw = self._item_to_raw(item)
            if not raw.apply_url or not is_valid_apply_url(raw.apply_url):
                continue
            job = self.normalize_job(raw)
            if job:
                tags = item.get("tags")
                if isinstance(tags, list):
                    job.tags = [str(t) for t in tags if t]
                normalized.append(job)

        log.parsed(len(normalized), raw_count=len(payload))
        return SourceFetchResult(source=self.source_name, jobs=normalized)

    def _item_to_raw(self, item: dict[str, Any]) -> RawSourceJob:
        title = (item.get("position") or item.get("title") or "").strip()
        company = (item.get("company") or "").strip()
        location = (item.get("location") or "Remote").strip()
        apply_url = self._normalize_apply_url(item.get("url") or item.get("apply_url") or "")
        description = item.get("description") or ""
        source_id = str(item.get("id") or item.get("slug") or self.build_job_hash(title, company, apply_url))

        return RawSourceJob(
            source=self.source_name,
            source_job_id=source_id,
            title=title,
            company=company,
            location=location,
            remote=True,
            apply_url=apply_url,
            description=description,
            posted_at=str(item.get("date") or ""),
            metadata={"tags": item.get("tags") or []},
            raw_payload=item,
        )

    @staticmethod
    def _normalize_apply_url(url: str) -> str:
        url = (url or "").strip()
        if not url:
            return ""
        if url.startswith("//"):
            return f"https:{url}"
        if url.startswith("/"):
            return f"https://remoteok.com{url}"
        return url

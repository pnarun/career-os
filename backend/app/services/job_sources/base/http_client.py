import asyncio
import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "CareerOS/1.0 (job-discovery; +https://github.com/career-os)",
    "Accept": "application/json, text/html, application/xml;q=0.9, */*;q=0.8",
}
DEFAULT_TIMEOUT = 25


async def fetch_http(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = 2,
) -> requests.Response:
    """GET with retries; runs in thread pool for async compatibility."""

    merged_headers = {**DEFAULT_HEADERS, **(headers or {})}

    def _request() -> requests.Response:
        last_exc: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(
                    url,
                    headers=merged_headers,
                    timeout=timeout,
                )
                return response
            except requests.RequestException as exc:
                last_exc = exc
                logger.debug(
                    "HTTP retry source attempt=%d url=%s error=%s",
                    attempt + 1,
                    url,
                    exc,
                )
        assert last_exc is not None
        raise last_exc

    return await asyncio.to_thread(_request)


async def fetch_json(url: str, **kwargs: Any) -> Any:
    response = await fetch_http(url, **kwargs)
    response.raise_for_status()
    return response.json()


async def fetch_text(url: str, **kwargs: Any) -> str:
    response = await fetch_http(url, **kwargs)
    response.raise_for_status()
    return response.text

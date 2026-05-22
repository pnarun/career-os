"""Naukri job source — Playwright integration placeholder."""

from typing import Any


class NaukriJobSource:
    """Future Playwright-based Naukri job ingestion."""

    source_name = "naukri"

    async def fetch_jobs(self) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "Naukri source is not implemented yet. "
            "Playwright automation will be added in a future release."
        )

"""Instahyre job source — Playwright integration placeholder."""

from typing import Any


class InstahyreJobSource:
    """Future Playwright-based Instahyre job ingestion."""

    source_name = "instahyre"

    async def fetch_jobs(self) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "Instahyre source is not implemented yet. "
            "Playwright automation will be added in a future release."
        )

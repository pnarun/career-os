"""Indeed job source — Playwright integration placeholder."""

from typing import Any


class IndeedJobSource:
    """Future Playwright-based Indeed job ingestion."""

    source_name = "indeed"

    async def fetch_jobs(self) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "Indeed source is not implemented yet. "
            "Playwright automation will be added in a future release."
        )

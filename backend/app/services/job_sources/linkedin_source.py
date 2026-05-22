"""LinkedIn job source — Playwright integration placeholder."""

from typing import Any


class LinkedInJobSource:
    """Future Playwright-based LinkedIn job ingestion."""

    source_name = "linkedin"

    async def fetch_jobs(self) -> list[dict[str, Any]]:
        raise NotImplementedError(
            "LinkedIn source is not implemented yet. "
            "Playwright automation will be added in a future release."
        )

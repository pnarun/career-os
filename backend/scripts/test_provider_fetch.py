"""Run one fetch test per HTTP provider and print URL/debug summary."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(message)s")

from app.services.job_sources.indeed_source import (
    IndeedJobSource,
    build_indeed_rss_url,
    build_indeed_search_url,
)
from app.services.job_sources.instahyre_source import (
    InstahyreJobSource,
    build_instahyre_api_url,
    build_instahyre_search_url,
)
from app.services.job_sources.naukri_source import (
    NaukriJobSource,
    build_naukri_api_url,
    build_naukri_search_url,
)


async def _run_one(name: str, source, web_url: str, fetch_url: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"PROVIDER: {name}")
    print(f"generated web URL: {web_url}")
    print(f"generated fetch URL: {fetch_url}")
    result = await source.run_fetch()
    status = "error"
    if result.error and "HTTP" in (result.error or ""):
        for token in result.error.split():
            if token.startswith("HTTP"):
                status = token.replace("HTTP", "").strip()
                break
    elif result.jobs:
        status = "200"
    elif not result.error:
        status = "200"
    else:
        status = result.error[:80]
    print(f"response status: {status}")
    print(f"jobs extracted count: {len(result.jobs)}")
    first_title = result.jobs[0].title if result.jobs else "(none)"
    print(f"first extracted job title: {first_title}")
    if result.error:
        print(f"error: {result.error}")


async def main() -> None:
    role = "software engineer"
    location_indeed = "India"
    location_naukri = "india"
    location_instahyre = "India"
    remote = False

    await _run_one(
        "indeed",
        IndeedJobSource(role=role, location=location_indeed, remote=remote),
        build_indeed_search_url(role, location_indeed, remote=remote),
        build_indeed_rss_url(role, location_indeed, remote=remote),
    )
    await _run_one(
        "naukri",
        NaukriJobSource(role=role, location=location_naukri, remote=remote),
        build_naukri_search_url(role, location_naukri, remote=remote),
        build_naukri_api_url(role, location_naukri, remote=remote),
    )
    await _run_one(
        "instahyre",
        InstahyreJobSource(role=role, location=location_instahyre, remote=remote),
        build_instahyre_search_url(role, location_instahyre, remote=remote),
        build_instahyre_api_url(role, location_instahyre, remote=remote),
    )


if __name__ == "__main__":
    asyncio.run(main())

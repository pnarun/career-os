"""Job source integrations (public APIs today, Playwright sources later)."""

from app.services.job_sources.indeed_source import IndeedJobSource
from app.services.job_sources.instahyre_source import InstahyreJobSource
from app.services.job_sources.linkedin_source import LinkedInJobSource
from app.services.job_sources.naukri_source import NaukriJobSource

__all__ = [
    "LinkedInJobSource",
    "NaukriJobSource",
    "InstahyreJobSource",
    "IndeedJobSource",
]

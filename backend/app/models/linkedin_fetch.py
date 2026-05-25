from pydantic import BaseModel, Field

from app.models.job import JobDocument


class LinkedInFetchResponse(BaseModel):
    """Result of a background LinkedIn discovery fetch merged into the jobs feed."""

    status: str
    message: str = ""
    session_valid: bool = True
    jobs_fetched: int = 0
    jobs_filtered: int = 0
    jobs_stored: int = 0
    jobs_skipped: int = 0
    easy_apply_count: int = 0
    search_keywords: list[str] = Field(default_factory=list)
    scan_id: str = ""
    jobs: list[JobDocument] = Field(default_factory=list)

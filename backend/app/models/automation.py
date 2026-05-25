from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

SessionStatusValue = Literal["none", "ready", "corrupted"]


class PlatformSessionStatus(BaseModel):
    status: SessionStatusValue = "none"
    last_saved_at: str | None = None
    cookie_count: int = 0
    storage_size_kb: float = 0
    exists: bool = False


class TestOpenRequest(BaseModel):
    url: HttpUrl = Field(..., examples=["https://example.com"])
    platform: str = "generic"
    headless: bool | None = None


class TestOpenResponse(BaseModel):
    status: str
    title: str = ""
    screenshot_path: str = ""
    url: str = ""
    message: str = ""


class BrowserHealthResponse(BaseModel):
    status: str
    browser_connected: bool = False
    chromium_version: str = ""
    message: str = ""


class PrepareSessionDoneResponse(BaseModel):
    status: str = "ok"
    platform: str
    message: str = ""


class TestSessionResponse(BaseModel):
    status: str
    platform: str
    session_saved: bool = False
    session_path: str = ""
    home_url: str = ""
    message: str = ""
    session_status: SessionStatusValue | None = None
    cookie_count: int | None = None
    storage_size_kb: float | None = None
    last_saved_at: str | None = None
    login_warning: bool = False


class OpenSessionResponse(BaseModel):
    status: str
    platform: str = ""
    home_url: str = ""
    message: str = ""


class DeleteSessionResponse(BaseModel):
    status: str
    platform: str
    message: str = ""


class SessionStatusResponse(BaseModel):
    """Per-platform session health (linkedin, naukri, etc.)."""

    sessions: dict[str, PlatformSessionStatus] = Field(default_factory=dict)


class LinkedInDiscoveryResponse(BaseModel):
    status: str
    message: str = ""
    jobs_fetched: int = 0
    easy_apply_count: int = 0
    screenshot_path: str = ""
    session_valid: bool = True
    jobs: list[dict] = Field(default_factory=list)

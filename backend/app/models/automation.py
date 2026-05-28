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


class LinkedInCookiePayload(BaseModel):
    name: str
    value: str
    domain: str
    path: str = "/"
    expires: float | int = -1
    httpOnly: bool = False
    secure: bool = True
    sameSite: str | None = None


class LinkedInConnectRequest(BaseModel):
    platform: str = "linkedin"
    cookies: list[LinkedInCookiePayload] = Field(default_factory=list)
    userAgent: str = ""
    syncedAt: str | None = None


class LinkedInDiscoveryResponse(BaseModel):
    status: str
    message: str = ""
    jobs_fetched: int = 0
    easy_apply_count: int = 0
    screenshot_path: str = ""
    session_valid: bool = True
    jobs: list[dict] = Field(default_factory=list)


class LinkedInPairingCodeResponse(BaseModel):
    pairingCode: str
    expiresIn: int = 300
    expiresAt: str | None = None


class LinkedInConnectWithCodeRequest(BaseModel):
    pairingCode: str = Field(..., min_length=6, max_length=6)
    cookies: list[LinkedInCookiePayload] = Field(default_factory=list)
    userAgent: str = ""
    extensionVersion: str = ""


class LinkedInConnectWithCodeResponse(BaseModel):
    success: bool = True
    connected: bool = True
    syncedAt: str
    syncToken: str = ""


class LinkedInResyncRequest(BaseModel):
    syncToken: str = Field(..., min_length=16)
    cookies: list[LinkedInCookiePayload] = Field(default_factory=list)
    userAgent: str = ""
    extensionVersion: str = ""


class LinkedInResyncResponse(BaseModel):
    success: bool = True
    syncedAt: str


class LinkedInDisconnectResponse(BaseModel):
    success: bool = True
    message: str = "LinkedIn session disconnected."


class LinkedInConnectionStatusResponse(BaseModel):
    connected: bool = False
    lastSyncedAt: str | None = None
    expiresSoon: bool = False
    sessionHealthy: bool = False
    providerStatus: str = "disconnected"
    lastFetchAt: str | None = None
    lastFetchJobCount: int = 0

"""
Structured per-provider fetch diagnostics and step logging.

Log prefix format: [INDEED] Fetch started
"""

from __future__ import annotations

import logging
from typing import Literal

import requests
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

ProviderStatus = Literal["success", "failed", "empty"]
ProviderErrorType = Literal[
    "none",
    "network_failure",
    "parsing_failure",
    "auth_required",
    "rate_limit",
    "selector_mismatch",
    "timeout",
    "unknown",
]


class ProviderFetchDiagnostic(BaseModel):
    source: str
    status: ProviderStatus
    jobs_fetched: int = 0
    duration_ms: int = 0
    error_type: ProviderErrorType = "none"
    error_message: str = ""
    requires_auth: bool = False
    session_valid: bool | None = None

    def to_public_dict(self) -> dict:
        return self.model_dump()


class ProviderFetchLogger:
    """Structured [SOURCE] log lines for fetch pipelines."""

    def __init__(self, source: str) -> None:
        self._tag = source.strip().upper()

    def started(self, detail: str = "") -> None:
        msg = "Fetch started"
        if detail:
            msg = f"{msg} — {detail}"
        logger.info("[%s] %s", self._tag, msg)

    def step(self, message: str) -> None:
        logger.info("[%s] %s", self._tag, message)

    def parsed(self, count: int, *, raw_count: int | None = None) -> None:
        if raw_count is not None:
            logger.info("[%s] Parsed jobs=%d (raw=%d)", self._tag, count, raw_count)
        else:
            logger.info("[%s] Parsed jobs=%d", self._tag, count)

    def success(self, count: int, duration_ms: int) -> None:
        logger.info("[%s] SUCCESS jobs=%d duration_ms=%d", self._tag, count, duration_ms)

    def failed(self, error_type: ProviderErrorType, message: str) -> None:
        logger.warning("[%s] FAILED %s — %s", self._tag, error_type, message)


def _lower(text: str) -> str:
    return (text or "").lower()


def classify_message(
    message: str,
    *,
    http_status: int | None = None,
) -> tuple[ProviderErrorType, bool, bool | None]:
    """
    Infer error_type, requires_auth, session_valid from a message / HTTP status.
    session_valid is False only for explicit session/auth failures.
    """
    text = _lower(message)

    if http_status == 429:
        return "rate_limit", False, None
    if http_status == 401:
        return "auth_required", True, False
    if http_status == 403:
        if any(k in text for k in ("session", "login", "cookie", "unauthorized")):
            return "auth_required", True, False
        return "rate_limit", False, None
    if http_status == 404:
        return "network_failure", False, None
    if http_status and http_status >= 500:
        return "network_failure", False, None

    if "404" in text or "not found" in text:
        return "network_failure", False, None
    if "403" in text or "forbidden" in text:
        if any(k in text for k in ("session", "login", "cookie")):
            return "auth_required", True, False
        return "rate_limit", False, None

    if any(k in text for k in ("timeout", "timed out", "read timed out")):
        return "timeout", False, None
    if any(
        k in text
        for k in (
            "connection",
            "network",
            "dns",
            "refused",
            "unreachable",
            "ssl",
            "certificate",
        )
    ):
        return "network_failure", False, None
    if any(k in text for k in ("429", "rate limit", "too many requests")):
        return "rate_limit", False, None
    if any(
        k in text
        for k in (
            "session",
            "login",
            "cookie",
            "auth",
            "unauthorized",
            "forbidden",
            "403",
            "401",
        )
    ):
        session_valid = "session" in text or "expired" in text or "login" in text
        return "auth_required", True, False if session_valid else None
    if any(k in text for k in ("parse", "xml", "json", "invalid payload", "malformed")):
        return "parsing_failure", False, None
    if any(
        k in text
        for k in (
            "selector",
            "no job cards",
            "no parseable",
            "0 job items",
            "empty channel",
            "unexpected payload",
        )
    ):
        return "selector_mismatch", False, None

    return "unknown", False, None


def classify_exception(exc: BaseException) -> tuple[ProviderErrorType, str, bool, bool | None]:
    message = str(exc) or exc.__class__.__name__
    if isinstance(exc, requests.Timeout):
        return "timeout", message, False, None
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        status = exc.response.status_code
        error_type, requires_auth, session_valid = classify_message(
            message, http_status=status
        )
        return error_type, message, requires_auth, session_valid
    if isinstance(exc, requests.RequestException):
        return "network_failure", message, False, None

    error_type, requires_auth, session_valid = classify_message(message)
    return error_type, message, requires_auth, session_valid


def diagnostic_from_exception(
    source: str,
    exc: BaseException,
    *,
    duration_ms: int = 0,
) -> ProviderFetchDiagnostic:
    error_type, message, requires_auth, session_valid = classify_exception(exc)
    log = ProviderFetchLogger(source)
    log.failed(error_type, message)
    return ProviderFetchDiagnostic(
        source=source,
        status="failed",
        jobs_fetched=0,
        duration_ms=duration_ms,
        error_type=error_type,
        error_message=message,
        requires_auth=requires_auth,
        session_valid=session_valid,
    )


def diagnostic_failure(
    source: str,
    *,
    error_type: ProviderErrorType,
    error_message: str,
    duration_ms: int = 0,
    requires_auth: bool = False,
    session_valid: bool | None = None,
    jobs_fetched: int = 0,
) -> ProviderFetchDiagnostic:
    log = ProviderFetchLogger(source)
    log.failed(error_type, error_message)
    return ProviderFetchDiagnostic(
        source=source,
        status="failed" if jobs_fetched == 0 else "empty",
        jobs_fetched=jobs_fetched,
        duration_ms=duration_ms,
        error_type=error_type,
        error_message=error_message,
        requires_auth=requires_auth,
        session_valid=session_valid,
    )


def diagnostic_success(
    source: str,
    *,
    jobs_fetched: int,
    duration_ms: int,
) -> ProviderFetchDiagnostic:
    log = ProviderFetchLogger(source)
    log.success(jobs_fetched, duration_ms)
    return ProviderFetchDiagnostic(
        source=source,
        status="success",
        jobs_fetched=jobs_fetched,
        duration_ms=duration_ms,
        error_type="none",
        error_message="",
        requires_auth=False,
        session_valid=None,
    )


def finalize_diagnostic(
    source: str,
    *,
    jobs: list,
    duration_ms: int,
    error: str | None = None,
    explicit: ProviderFetchDiagnostic | None = None,
    empty_error_type: ProviderErrorType = "parsing_failure",
    empty_message: str = "",
) -> ProviderFetchDiagnostic:
    """
    Build a diagnostic when the source did not set one explicitly.
    Zero jobs without an error is reported as failed (not silent).
    """
    count = len(jobs)

    if explicit is not None:
        explicit.jobs_fetched = count
        explicit.duration_ms = duration_ms
        if error and not explicit.error_message:
            explicit.error_message = error
            explicit.status = "failed"
            et, ra, sv = classify_message(error)
            explicit.error_type = et
            explicit.requires_auth = explicit.requires_auth or ra
            if sv is not None:
                explicit.session_valid = sv
        elif count > 0 and explicit.status != "success":
            explicit.status = "success"
            explicit.error_type = "none"
            explicit.error_message = ""
        ProviderFetchLogger(source).success(count, duration_ms)
        return explicit

    if error:
        error_type, requires_auth, session_valid = classify_message(error)
        return diagnostic_failure(
            source,
            error_type=error_type,
            error_message=error,
            duration_ms=duration_ms,
            requires_auth=requires_auth,
            session_valid=session_valid,
            jobs_fetched=count,
        )

    if count == 0:
        msg = empty_message or "Provider returned no parseable jobs"
        return diagnostic_failure(
            source,
            error_type=empty_error_type,
            error_message=msg,
            duration_ms=duration_ms,
        )

    return diagnostic_success(source, jobs_fetched=count, duration_ms=duration_ms)


def merge_http_status_message(status_code: int, body_hint: str = "") -> str:
    hint = f" — {body_hint}" if body_hint else ""
    return f"HTTP {status_code}{hint}"

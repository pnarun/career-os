"""Human confirmation signals — required before final submit."""

from __future__ import annotations

import time
from pathlib import Path

from app.automation.browser.session_manager import PROFILES_DIR

APPLY_FLAGS_DIR = PROFILES_DIR / "apply_flags"
CONFIRM_TIMEOUT_SEC = 600
POLL_INTERVAL_SEC = 2.0


def confirm_flag_path(session_id: str) -> Path:
    return APPLY_FLAGS_DIR / f".apply_confirm_{session_id}.flag"


def cancel_flag_path(session_id: str) -> Path:
    return APPLY_FLAGS_DIR / f".apply_cancel_{session_id}.flag"


def clear_apply_flags(session_id: str) -> None:
    for path in (confirm_flag_path(session_id), cancel_flag_path(session_id)):
        if path.is_file():
            path.unlink()


def signal_apply_confirm(session_id: str) -> None:
    APPLY_FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    clear_apply_flags(session_id)
    confirm_flag_path(session_id).write_text("1", encoding="utf-8")


def signal_apply_cancel(session_id: str) -> None:
    APPLY_FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    cancel_flag_path(session_id).write_text("1", encoding="utf-8")


def is_apply_confirmed(session_id: str) -> bool:
    return confirm_flag_path(session_id).is_file()


def is_apply_cancelled(session_id: str) -> bool:
    return cancel_flag_path(session_id).is_file()


def wait_for_confirmation(session_id: str, *, timeout_sec: int = CONFIRM_TIMEOUT_SEC) -> str:
    """
    Poll for user confirmation or cancel.
    Returns: 'confirmed' | 'cancelled' | 'timeout'
    """
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if is_apply_confirmed(session_id):
            confirm_flag_path(session_id).unlink(missing_ok=True)
            return "confirmed"
        if is_apply_cancelled(session_id):
            cancel_flag_path(session_id).unlink(missing_ok=True)
            return "cancelled"
        time.sleep(POLL_INTERVAL_SEC)
    return "timeout"

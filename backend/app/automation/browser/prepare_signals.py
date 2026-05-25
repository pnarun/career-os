"""File-based signals when the user finishes a headed manual browser flow."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from app.automation.browser.session_manager import PROFILES_DIR, normalize_platform

ManualSessionMode = Literal["prepare", "open"]


def manual_done_flag_path(platform: str, mode: ManualSessionMode) -> Path:
    key = normalize_platform(platform)
    return PROFILES_DIR / f".{mode}_done_{key}.flag"


def clear_manual_done(platform: str, mode: ManualSessionMode) -> None:
    path = manual_done_flag_path(platform, mode)
    if path.is_file():
        path.unlink()


def signal_manual_done(platform: str, mode: ManualSessionMode) -> None:
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    manual_done_flag_path(platform, mode).write_text("1", encoding="utf-8")


def is_manual_done(platform: str, mode: ManualSessionMode) -> bool:
    return manual_done_flag_path(platform, mode).is_file()


def consume_manual_done(platform: str, mode: ManualSessionMode) -> bool:
    path = manual_done_flag_path(platform, mode)
    if not path.is_file():
        return False
    path.unlink()
    return True


def clear_prepare_done(platform: str) -> None:
    clear_manual_done(platform, "prepare")


def signal_prepare_done(platform: str) -> None:
    signal_manual_done(platform, "prepare")


def is_prepare_done(platform: str) -> bool:
    return is_manual_done(platform, "prepare")


def consume_prepare_done(platform: str) -> bool:
    return consume_manual_done(platform, "prepare")

"""Career Lens extension version checks for beta distribution."""

from __future__ import annotations

import re

from app.core.config import settings


def _parse_version(raw: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", raw or "")
    if not parts:
        return (0,)
    return tuple(int(p) for p in parts[:4])


def extension_version_ok(version: str) -> bool:
    """Return True when extension meets EXTENSION_MIN_VERSION (semver-ish)."""
    reported = (version or "").strip()
    if not reported or reported.lower() in ("unknown", "dev"):
        return True
    min_v = _parse_version(settings.EXTENSION_MIN_VERSION)
    cur = _parse_version(reported)
    length = max(len(min_v), len(cur))
    min_padded = min_v + (0,) * (length - len(min_v))
    cur_padded = cur + (0,) * (length - len(cur))
    return cur_padded >= min_padded


def extension_version_message(version: str) -> str:
    return (
        f"Career Lens extension is outdated (v{version or 'unknown'}). "
        f"Please update to v{settings.EXTENSION_MIN_VERSION} or newer from your beta package."
    )

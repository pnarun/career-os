"""Entrypoint env defaults — call before importing app settings."""

from __future__ import annotations

import os

from app.runtime.service_mode import ServiceMode


def _clear_settings_cache() -> None:
    try:
        from app.core.config import get_settings

        get_settings.cache_clear()
    except Exception:
        pass


def apply_entrypoint_defaults(mode: ServiceMode) -> None:
    """
    Set os.environ defaults for dedicated start_*.py scripts only.
    Does not override values already set in the environment.
    """
    os.environ.setdefault("SERVICE_MODE", mode.value)

    if mode == ServiceMode.API:
        os.environ.setdefault("ENABLE_SCHEDULER", "false")
        os.environ.setdefault("ENABLE_REALTIME", "true")
        os.environ.setdefault("ENABLE_AUTOMATION", "true")
        os.environ.setdefault("ENABLE_PLAYWRIGHT", "true")
        os.environ.setdefault("SCAN_EXECUTION_MODE", "dispatch")
    elif mode == ServiceMode.SCAN_WORKER:
        os.environ.setdefault("ENABLE_SCHEDULER", "true")
        os.environ.setdefault("ENABLE_REALTIME", "false")
        os.environ.setdefault("ENABLE_AUTOMATION", "false")
        os.environ.setdefault("ENABLE_PLAYWRIGHT", "true")
        os.environ.setdefault("SCAN_EXECUTION_MODE", "dispatch")
        os.environ.setdefault("SCHEDULER_STARTUP_CATCHUP", "false")
    elif mode == ServiceMode.AUTOMATION_WORKER:
        os.environ.setdefault("ENABLE_SCHEDULER", "false")
        os.environ.setdefault("ENABLE_REALTIME", "false")
        os.environ.setdefault("ENABLE_AUTOMATION", "true")
        os.environ.setdefault("ENABLE_PLAYWRIGHT", "true")
        os.environ.setdefault("SCAN_EXECUTION_MODE", "dispatch")

    _clear_settings_cache()

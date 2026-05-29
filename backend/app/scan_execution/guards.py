"""Runtime guards — block inline scan execution on API in dispatch mode."""

from __future__ import annotations

from app.runtime.service_mode import runtime


class ScanExecutionBlockedError(RuntimeError):
    """Raised when scan pipelines are invoked on API in dispatch mode."""


def ensure_worker_may_execute_scans() -> None:
    """
    Scan pipelines may run on scan_worker OR in inline monolith mode only.
    API + dispatch must enqueue and return immediately.
    """
    if runtime.is_scan_worker():
        return
    if runtime.is_api() and runtime.should_execute_scans_inline():
        return
    raise ScanExecutionBlockedError(
        f"Scan execution blocked in process (mode={runtime.mode.value}, "
        f"execution={runtime.scan_execution_mode()}). Use scan_worker."
    )


def api_is_dispatch_only() -> bool:
    return runtime.is_api() and runtime.should_enqueue_scans_for_worker()

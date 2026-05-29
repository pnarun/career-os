"""Subprocess runner for Playwright (isolated from FastAPI event loop)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_WORKER_MODULE = "app.automation.browser.worker_cli"
_DEFAULT_TIMEOUT_SEC = 120
_OPEN_SESSION_TIMEOUT_SEC = 600
_PREPARE_SESSION_TIMEOUT_SEC = 600
_LINKEDIN_DISCOVER_TIMEOUT_SEC = 115
_STREAM_STDERR_COMMANDS = frozenset({"prepare-session", "open-session", "linkedin-easy-apply"})
_LINKEDIN_EASY_APPLY_TIMEOUT_SEC = 660


def _worker_argv(command: str, payload_json: str) -> list[str]:
    """Run worker as a package module so `app` imports resolve."""
    return [
        sys.executable,
        "-m",
        _WORKER_MODULE,
        command,
        payload_json,
    ]


def normalize_worker_command(command: str) -> str:
    """Single entry point for command names (no legacy test-session subprocess)."""
    if command == "test-session":
        logger.warning(
            "[AUTOMATION][WORKER] Deprecated command test-session — use prepare-session"
        )
        return "prepare-session"
    return command


def _emit_worker_line(line: str) -> None:
    stripped = line.strip()
    if not stripped:
        return
    if "[SESSION]" in stripped or "[WORKER]" in stripped or "TRACEBACK" in stripped:
        logger.info("%s", stripped)
    elif stripped.startswith("INFO:app.automation.session:"):
        logger.info("%s", stripped.split(":", 2)[-1].strip())
    # Do not flush parent sys.stderr here — blocks the drain thread when stderr is a
    # full pipe/TUI, which deadlocks the worker child after the first stderr write.


def _drain_stderr(pipe, buffer: list[str]) -> None:
    try:
        for line in pipe:
            buffer.append(line)
            _emit_worker_line(line)
    except Exception:
        pass
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def _run_worker_streaming(
    command: str,
    payload: dict[str, Any] | None,
    *,
    timeout_sec: int,
) -> dict[str, Any]:
    """
    Run long-lived worker commands (prepare-session, open-session).

    Worker stderr is inherited (not piped) so logs appear live in the uvicorn
    terminal. Piping stderr + logging each line in the drain thread deadlocks on
    Windows when the parent console is busy (child blocks after the first write).
    """
    payload_json = json.dumps(payload or {})
    env = {**os.environ, "PYTHONPATH": str(_BACKEND_ROOT)}
    platform = (payload or {}).get("platform", "")
    logger.info(
        "[AUTOMATION][WORKER] spawning subprocess command=%s platform=%s timeout=%ss "
        "(worker stderr inherited — watch this terminal for [WORKER]/[SESSION] logs)",
        command,
        platform,
        timeout_sec,
    )

    proc = subprocess.Popen(
        _worker_argv(command, payload_json),
        stdout=subprocess.PIPE,
        stderr=None,
        text=True,
        cwd=str(_BACKEND_ROOT),
        env=env,
    )

    try:
        stdout, _ = proc.communicate(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        logger.error("[AUTOMATION][WORKER] command=%s timed out after %ss", command, timeout_sec)
        return {
            "status": "error",
            "message": f"Worker timed out after {timeout_sec}s",
        }

    stdout = (stdout or "").strip()
    stderr_combined = ""

    if proc.returncode not in (0, 2) and stderr_combined:
        logger.warning(
            "[AUTOMATION][WORKER] command=%s exit=%s",
            command,
            proc.returncode,
        )

    if not stdout:
        message = stderr_combined or f"Worker exited with code {proc.returncode}"
        logger.error("[AUTOMATION][WORKER] empty stdout: %s", message[:500])
        return {"status": "error", "message": message}

    try:
        return json.loads(stdout.splitlines()[-1])
    except json.JSONDecodeError:
        logger.error(
            "[AUTOMATION][WORKER] invalid json stdout=%s",
            stdout[:500],
        )
        return {"status": "error", "message": "Invalid worker response"}


def _run_worker(
    command: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout_sec: int | None = None,
) -> dict[str, Any]:
    payload_json = json.dumps(payload or {})
    env = {**os.environ, "PYTHONPATH": str(_BACKEND_ROOT)}
    effective_timeout = timeout_sec if timeout_sec is not None else _DEFAULT_TIMEOUT_SEC

    completed = subprocess.run(
        _worker_argv(command, payload_json),
        capture_output=True,
        text=True,
        cwd=str(_BACKEND_ROOT),
        env=env,
        timeout=effective_timeout,
        check=False,
    )

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()

    for line in stderr.splitlines():
        _emit_worker_line(line)

    if not stdout:
        message = stderr or f"Worker exited with code {completed.returncode}"
        logger.error("[AUTOMATION][WORKER] empty stdout: %s", message)
        return {"status": "error", "message": message}

    try:
        data = json.loads(stdout.splitlines()[-1])
    except json.JSONDecodeError:
        logger.error(
            "[AUTOMATION][WORKER] invalid json stdout=%s stderr=%s",
            stdout[:500],
            stderr[:500],
        )
        return {"status": "error", "message": "Invalid worker response"}

    if completed.returncode not in (0, 2) and data.get("status") != "ok":
        logger.warning(
            "[AUTOMATION][WORKER] exit=%s stderr=%s",
            completed.returncode,
            stderr[:300],
        )

    return data


async def run_playwright(
    command: str,
    /,
    *,
    timeout_sec: int | None = None,
    **payload: Any,
) -> dict[str, Any]:
    """Run a Playwright worker command in a child process."""
    import asyncio

    from app.core.config import settings
    from app.core.runtime_diagnostics import log_memory_event

    if not settings.ENABLE_PLAYWRIGHT:
        logger.warning(
            "[AUTOMATION][WORKER] Playwright disabled (ENABLE_PLAYWRIGHT=false) command=%s",
            command,
            extra={"event": "playwright_disabled", "command": command},
        )
        return {"status": "error", "message": "Playwright disabled by configuration"}

    command = normalize_worker_command(command)
    logger.info("[AUTOMATION][WORKER] command=%s", command)

    effective_timeout = timeout_sec
    if effective_timeout is None and command == "open-session":
        effective_timeout = _OPEN_SESSION_TIMEOUT_SEC
    if effective_timeout is None and command == "prepare-session":
        effective_timeout = _PREPARE_SESSION_TIMEOUT_SEC
    if effective_timeout is None and command == "linkedin-discover":
        effective_timeout = _LINKEDIN_DISCOVER_TIMEOUT_SEC
    if effective_timeout is None and command == "linkedin-easy-apply":
        effective_timeout = _LINKEDIN_EASY_APPLY_TIMEOUT_SEC

    def _invoke() -> dict[str, Any]:
        if command in _STREAM_STDERR_COMMANDS:
            return _run_worker_streaming(
                command,
                payload,
                timeout_sec=effective_timeout or _PREPARE_SESSION_TIMEOUT_SEC,
            )
        return _run_worker(command, payload, timeout_sec=effective_timeout)

    log_memory_event("PLAYWRIGHT_MEMORY_USAGE", phase="before", command=command)
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _invoke)
    finally:
        log_memory_event("PLAYWRIGHT_MEMORY_USAGE", phase="after", command=command)


def shutdown_executor() -> None:
    """Close browser in worker subprocess if needed."""
    try:
        _run_worker("close", {})
    except Exception:
        logger.exception("[AUTOMATION][WORKER] shutdown close failed")

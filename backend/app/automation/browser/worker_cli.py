"""
Standalone Playwright worker (subprocess).

Invoked via `python -m app.automation.browser.worker_cli` from executor.py.
"""

import os
import sys
import traceback


def _trace(step: str) -> None:
    """stderr only; [WORKER] prefix so executor drain forwards to API logs."""
    print(f"[WORKER] {step}", file=sys.stderr, flush=True)


def _dispatch_prepare_session(payload: dict) -> dict:
    platform = payload.get("platform", "")
    if not platform:
        raise ValueError("prepare-session requires payload.platform")

    _trace(f"prepare-session: importing sync_runner platform={platform!r}")
    from app.automation.browser.sync_runner import prepare_platform_session_sync

    _trace("prepare-session: calling prepare_platform_session_sync")
    return prepare_platform_session_sync(platform, headless=payload.get("headless"))


def _dispatch_command(command: str, payload: dict) -> dict:
    if command == "health":
        from app.automation.browser.sync_runner import check_browser_health_sync

        return check_browser_health_sync()

    if command == "test-open":
        from app.automation.browser.sync_runner import test_open_url_sync

        return test_open_url_sync(
            payload["url"],
            platform=payload.get("platform", "generic"),
            headless=payload.get("headless"),
        )

    if command == "prepare-session":
        return _dispatch_prepare_session(payload)

    if command == "open-session":
        from app.automation.browser.sync_runner import open_session_sync

        return open_session_sync(payload["platform"])

    if command == "linkedin-discover":
        from app.services.job_sources.linkedin_playwright_source import (
            discover_linkedin_jobs_sync,
        )

        return discover_linkedin_jobs_sync(payload)

    if command == "linkedin-easy-apply":
        from app.services.auto_apply.linkedin_easy_apply import linkedin_easy_apply_sync

        return linkedin_easy_apply_sync(payload)

    if command == "close":
        from app.automation.browser.sync_runner import close_browser_sync

        close_browser_sync()
        return {"status": "ok"}

    raise ValueError(f"Unknown worker command: {command}")


def main() -> int:
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    import argparse
    import json

    _trace("worker_cli.main() entered")

    parser = argparse.ArgumentParser(description="Career OS Playwright worker")
    parser.add_argument(
        "command",
        choices=(
            "health",
            "test-open",
            "prepare-session",
            "open-session",
            "linkedin-discover",
            "linkedin-easy-apply",
            "close",
        ),
    )
    parser.add_argument("payload", nargs="?", default="{}")
    args = parser.parse_args()

    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as exc:
        print(json.dumps({"status": "error", "message": f"Invalid JSON payload: {exc}"}), flush=True)
        return 1

    if not isinstance(payload, dict):
        print(json.dumps({"status": "error", "message": "Payload must be a JSON object"}), flush=True)
        return 1

    _trace(f"dispatch command={args.command} platform={payload.get('platform', '')!r}")

    try:
        result = _dispatch_command(args.command, payload)
        print(json.dumps(result), flush=True)
        sys.stdout.flush()
        return 0 if result.get("status") != "error" else 2
    except Exception as exc:
        print(
            json.dumps({"status": "error", "message": f"{exc}\n\n{traceback.format_exc()}"}),
            flush=True,
        )
        sys.stdout.flush()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

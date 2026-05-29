#!/usr/bin/env python3
"""
Career OS automation worker entrypoint (Phase 1A).

Playwright/automation runtime preparation — no public HTTP API.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys


def main() -> None:
    backend_root = os.path.dirname(os.path.abspath(__file__))
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)

    from app.runtime.entrypoint import apply_entrypoint_defaults
    from app.runtime.service_mode import ServiceMode

    apply_entrypoint_defaults(ServiceMode.AUTOMATION_WORKER)

    from app.core.config import settings
    from app.core.logging_config import configure_logging
    from app.runtime.automation_worker_loop import run_automation_worker_loop
    from app.runtime.bootstrap import (
        bootstrap_automation_worker_subsystems,
        bootstrap_core,
        shutdown_worker_subsystems,
    )

    configure_logging(service="career-os-automation-worker", level=settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)

    async def _run() -> None:
        try:
            await bootstrap_core(run_migrations=False)
            await bootstrap_automation_worker_subsystems()
            logger.info(
                "[AUTOMATION_WORKER] ready — Playwright runtime mode",
                extra={"event": "automation_worker_ready"},
            )
            await run_automation_worker_loop()
        finally:
            await shutdown_worker_subsystems()

    asyncio.run(_run())


if __name__ == "__main__":
    main()

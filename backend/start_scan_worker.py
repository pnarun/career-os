#!/usr/bin/env python3
"""
Career OS scan worker entrypoint (Phase 1B).

Runs APScheduler + scan task processor loop. No HTTP API or WebSocket server.
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

    apply_entrypoint_defaults(ServiceMode.SCAN_WORKER)

    from app.core.config import settings
    from app.core.logging_config import configure_logging
    from app.runtime.bootstrap import bootstrap_core, bootstrap_scan_worker_subsystems, shutdown_worker_subsystems
    from app.scan_execution.worker_loop import run_scan_worker_loop

    configure_logging(service="career-os-scan-worker", level=settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)

    async def _run() -> None:
        try:
            await bootstrap_core(run_migrations=False)
            await bootstrap_scan_worker_subsystems()
            logger.info(
                "[SCAN_WORKER] ready — processing queued scan tasks",
                extra={"event": "scan_worker_ready"},
            )
            await run_scan_worker_loop()
        finally:
            await shutdown_worker_subsystems()

    asyncio.run(_run())


if __name__ == "__main__":
    main()

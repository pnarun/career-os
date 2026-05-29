#!/usr/bin/env python3
"""
Career OS automation worker entrypoint (Phase 1A).

Playwright/automation runtime preparation. Exposes a minimal HTTP health
server on PORT so Render Web Services (free tier) detect an open port.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
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
    from app.runtime.automation_worker_health_server import (
        create_health_uvicorn_server,
        serve_health_until_exit,
    )
    from app.runtime.automation_worker_loop import AutomationWorkerLoop
    from app.runtime.bootstrap import (
        bootstrap_automation_worker_subsystems,
        bootstrap_core,
        shutdown_worker_subsystems,
    )

    configure_logging(service="career-os-automation-worker", level=settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)

    async def _run() -> None:
        host = "0.0.0.0"
        port = int(os.getenv("PORT", "10000"))
        health_server = create_health_uvicorn_server(host=host, port=port)
        worker = AutomationWorkerLoop()

        def _request_shutdown(*_: object) -> None:
            worker.request_stop()
            health_server.should_exit = True

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _request_shutdown)
            except (ValueError, OSError):
                pass

        try:
            await bootstrap_core(run_migrations=False)
            await bootstrap_automation_worker_subsystems()
            logger.info(
                "[AUTOMATION_WORKER] ready — Playwright runtime mode",
                extra={"event": "automation_worker_ready"},
            )
            logger.info(
                "[HEALTH_SERVER_STARTED] host=%s port=%s",
                host,
                port,
                extra={"event": "HEALTH_SERVER_STARTED", "host": host, "port": port},
            )
            logger.info(
                "[HEALTH_SERVER_PORT] %s",
                port,
                extra={"event": "HEALTH_SERVER_PORT", "port": port},
            )

            await asyncio.gather(
                worker.run_forever(),
                serve_health_until_exit(health_server),
            )
        finally:
            health_server.should_exit = True
            await shutdown_worker_subsystems()

    asyncio.run(_run())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Career OS API entrypoint (Phase 1A).

Launches FastAPI with websocket enabled; scheduler disabled by default.
Existing `uvicorn app.main:app` remains valid for backward-compatible monolith deploys.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    backend_root = os.path.dirname(os.path.abspath(__file__))
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)

    from app.runtime.entrypoint import apply_entrypoint_defaults
    from app.runtime.service_mode import ServiceMode

    apply_entrypoint_defaults(ServiceMode.API)

    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("ENVIRONMENT", "development") == "development"

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()

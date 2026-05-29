"""Minimal HTTP health server for Render Web Service port binding (automation worker only)."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Single app instance — no docs, no middleware, no WebSocket/realtime.
_health_app = FastAPI(
    title="Career OS Automation Worker Health",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@_health_app.get("/health", include_in_schema=False)
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "automation-worker"})


def create_health_uvicorn_server(*, host: str, port: int) -> uvicorn.Server:
    """Build a lightweight uvicorn server bound to the module-level health app."""
    config = uvicorn.Config(
        _health_app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
        lifespan="off",
    )
    return uvicorn.Server(config)


async def serve_health_until_exit(server: uvicorn.Server) -> None:
    """Run the health server until ``server.should_exit`` is set."""
    await server.serve()

"""Minimal HTTP health server for Render Web Service port binding (scan worker only)."""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

logger = logging.getLogger(__name__)

# Single app instance — no docs, no middleware, no WebSocket/realtime.
_health_app = FastAPI(
    title="Career OS Scan Worker Health",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@_health_app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
async def root(request: Request) -> Response:
    logger.info("[HEALTH_CHECK] method=%s path=/", request.method)
    if request.method == "HEAD":
        return Response(status_code=200)
    return PlainTextResponse("career-os-scan-worker alive")


@_health_app.api_route("/health", methods=["GET", "HEAD"], include_in_schema=False)
async def health(request: Request) -> Response:
    logger.info("[HEALTH_CHECK] method=%s", request.method)
    if request.method == "HEAD":
        return Response(status_code=200)
    return JSONResponse({"status": "ok", "service": "scan_worker"})


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

"""Health and system endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_health_get():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert data["scheduler"] in ("running", "stopped")


@pytest.mark.anyio
async def test_health_head():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.head("/health")
    assert response.status_code == 200
    assert response.content == b""


@pytest.mark.anyio
async def test_system_status_endpoint():
    from unittest.mock import AsyncMock, patch

    with patch(
        "app.api.routes.system._mongo_health",
        AsyncMock(return_value={"status": "ok"}),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/system/status")
    assert response.status_code == 200
    data = response.json()
    assert "components" in data
    assert "mongodb" in data["components"]

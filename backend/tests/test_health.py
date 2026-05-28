"""Health and system endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_get():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert data["scheduler"] in ("running", "stopped")
    assert "redis_connected" in data
    assert isinstance(data["redis_connected"], bool)


@pytest.mark.asyncio
async def test_health_head():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.head("/health")
    assert response.status_code == 200
    assert response.content == b""


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_uptime_status_page():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/uptime")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "stats.uptimerobot.com" in response.text
    assert "/uptime/go" in response.text
    assert "refused to connect" in response.text.lower() or "iframe" in response.text.lower()

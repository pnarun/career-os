"""Health and system endpoint tests."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_health_endpoint():
    with patch(
        "app.api.routes.system._mongo_health",
        AsyncMock(return_value={"status": "ok"}),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "environment" in data


@pytest.mark.anyio
async def test_system_status_endpoint():
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

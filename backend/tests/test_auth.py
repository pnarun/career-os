"""Auth route smoke tests (no DB required for check-email validation)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_check_email_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/auth/check-email", json={"email": "not-an-email"})
    assert response.status_code == 422

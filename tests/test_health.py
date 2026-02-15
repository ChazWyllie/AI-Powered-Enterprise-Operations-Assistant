"""Tests for health endpoint.

WP1: Verify /health returns {"status": "ok"} with 200 status.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_health_returns_ok():
    """Health endpoint should return status ok."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "observability" in data


@pytest.mark.asyncio
async def test_health_response_content_type():
    """Health endpoint should return JSON content type."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.headers["content-type"] == "application/json"

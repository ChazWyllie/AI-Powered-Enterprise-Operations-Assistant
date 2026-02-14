"""WP11 — Deployment smoke tests.

Validates that the production deployment is healthy and functional.
These tests run against the live API using the test client.
"""

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def production_client():
    """Create async client for smoke testing."""
    from app.main import app

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestSmokeTests:
    """Production smoke tests — validates deployment readiness."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, production_client):
        """GET /health returns 200 with status=ok."""
        async with production_client as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_chat_plan_only(self, production_client):
        """POST /chat (plan_only) returns 200 with valid response."""
        async with production_client as client:
            resp = await client.post(
                "/chat",
                json={"message": "show system status", "mode": "plan_only"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "answer" in data
            assert "plan" in data
            assert "actions_taken" in data
            assert "audit" in data

    @pytest.mark.asyncio
    async def test_response_structure_complete(self, production_client):
        """Response contains all required fields with correct types."""
        async with production_client as client:
            resp = await client.post(
                "/chat",
                json={"message": "check logs", "mode": "plan_only"},
            )
            data = resp.json()

            # Top-level fields
            assert isinstance(data["answer"], str)
            assert isinstance(data["plan"], list)
            assert isinstance(data["actions_taken"], list)
            assert isinstance(data["audit"], dict)

            # Audit fields
            assert "trace_id" in data["audit"]
            assert "mode" in data["audit"]

    @pytest.mark.asyncio
    async def test_invalid_mode_rejected(self, production_client):
        """Invalid mode returns 422."""
        async with production_client as client:
            resp = await client.post(
                "/chat",
                json={"message": "hello", "mode": "invalid"},
            )
            assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_message_rejected(self, production_client):
        """Empty message returns 422."""
        async with production_client as client:
            resp = await client.post(
                "/chat",
                json={"message": "", "mode": "plan_only"},
            )
            assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_health_response_format(self, production_client):
        """Health response has correct JSON structure."""
        async with production_client as client:
            resp = await client.get("/health")
            data = resp.json()
            assert data == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_chat_returns_trace_id(self, production_client):
        """Chat response includes a trace_id in audit."""
        async with production_client as client:
            resp = await client.post(
                "/chat",
                json={"message": "status check", "mode": "plan_only"},
            )
            data = resp.json()
            assert len(data["audit"]["trace_id"]) > 0

    @pytest.mark.asyncio
    async def test_chat_plan_only_no_actions(self, production_client):
        """Plan-only mode returns empty actions_taken."""
        async with production_client as client:
            resp = await client.post(
                "/chat",
                json={"message": "check status", "mode": "plan_only"},
            )
            data = resp.json()
            assert data["actions_taken"] == []
            assert data["audit"]["mode"] == "plan_only"

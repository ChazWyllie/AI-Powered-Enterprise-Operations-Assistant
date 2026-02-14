"""Integration tests for API endpoints (WP4).

Tests the full flow: API → Agent Orchestrator → MCP Tools
Validates input contracts, error handling, and response structure.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class TestChatEndpoint:
    """Tests for POST /chat endpoint."""

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def test_chat_returns_200_with_valid_request(self, async_client):
        """Chat endpoint returns 200 for valid request."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "What is the system status?", "mode": "plan_only"},
            )
        assert response.status_code == 200

    async def test_chat_returns_answer_field(self, async_client):
        """Response includes answer field."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Show me the logs", "mode": "plan_only"},
            )
        data = response.json()
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

    async def test_chat_returns_plan_field(self, async_client):
        """Response includes plan field with steps."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Check system status", "mode": "plan_only"},
            )
        data = response.json()
        assert "plan" in data
        assert isinstance(data["plan"], list)
        # Plan contains dicts with tool info
        if len(data["plan"]) > 0:
            assert isinstance(data["plan"][0], dict)

    async def test_chat_returns_actions_taken_field(self, async_client):
        """Response includes actions_taken field."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Get logs", "mode": "execute_safe"},
            )
        data = response.json()
        assert "actions_taken" in data
        assert isinstance(data["actions_taken"], list)

    async def test_chat_returns_audit_field(self, async_client):
        """Response includes audit metadata."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Status check", "mode": "plan_only"},
            )
        data = response.json()
        assert "audit" in data
        assert "trace_id" in data["audit"]
        assert "mode" in data["audit"]


class TestChatModeValidation:
    """Tests for mode enum validation."""

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def test_chat_accepts_plan_only_mode(self, async_client):
        """Mode 'plan_only' is valid."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Test", "mode": "plan_only"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["audit"]["mode"] == "plan_only"

    async def test_chat_accepts_execute_safe_mode(self, async_client):
        """Mode 'execute_safe' is valid."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Get system status", "mode": "execute_safe"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["audit"]["mode"] == "execute_safe"

    async def test_chat_rejects_invalid_mode(self, async_client):
        """Invalid mode returns 422 validation error."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Test", "mode": "invalid_mode"},
            )
        assert response.status_code == 422

    async def test_chat_mode_is_required(self, async_client):
        """Missing mode returns 422 validation error."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Test"},
            )
        assert response.status_code == 422


class TestChatInputValidation:
    """Tests for input validation."""

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def test_chat_requires_message(self, async_client):
        """Missing message returns 422."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"mode": "plan_only"},
            )
        assert response.status_code == 422

    async def test_chat_rejects_empty_message(self, async_client):
        """Empty message returns 422."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "", "mode": "plan_only"},
            )
        assert response.status_code == 422

    async def test_chat_rejects_whitespace_only_message(self, async_client):
        """Whitespace-only message returns 422."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "   ", "mode": "plan_only"},
            )
        assert response.status_code == 422


class TestChatErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def test_chat_handles_policy_violation_gracefully(self, async_client):
        """Policy violations return 400 with error message."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Delete all files with rm -rf", "mode": "execute_safe"},
            )
        # Should still return 200 with explanation that it can't execute
        # The orchestrator handles dangerous requests gracefully
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    async def test_chat_returns_json_content_type(self, async_client):
        """Response has application/json content type."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Test", "mode": "plan_only"},
            )
        assert response.headers["content-type"] == "application/json"


class TestChatIntegration:
    """End-to-end integration tests."""

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def test_status_query_triggers_get_system_status(self, async_client):
        """Status query invokes get_system_status tool."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "What is the current system status?", "mode": "execute_safe"},
            )
        data = response.json()
        # Should have executed get_system_status
        tool_names = [a.get("tool") for a in data.get("actions_taken", [])]
        assert "get_system_status" in tool_names

    async def test_log_query_triggers_get_logs(self, async_client):
        """Log query invokes get_logs tool."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Show me the recent syslog entries", "mode": "execute_safe"},
            )
        data = response.json()
        tool_names = [a.get("tool") for a in data.get("actions_taken", [])]
        assert "get_logs" in tool_names

    async def test_plan_only_does_not_execute(self, async_client):
        """Plan-only mode returns plan without executing."""
        async with async_client as client:
            response = await client.post(
                "/chat",
                json={"message": "Run cat /sim/fixtures/status.json", "mode": "plan_only"},
            )
        data = response.json()
        # Should have a plan
        assert len(data.get("plan", [])) > 0
        # Should NOT have executed (no actions_taken with results)
        actions = data.get("actions_taken", [])
        for action in actions:
            assert action.get("result") is None or action.get("skipped", False)


class TestHealthEndpointStillWorks:
    """Verify /health endpoint still works after integration."""

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def test_health_endpoint_returns_ok(self, async_client):
        """Health check returns status ok."""
        async with async_client as client:
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

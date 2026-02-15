"""Tests for observability production features (WP13).

Verifies:
- Trace ID present in every chat response
- X-Trace-Id header returned on chat responses
- Health endpoint reports observability status
- Trace IDs are valid UUIDs
- Tool calls create child spans in traces
- Observability client selection based on environment
"""

import os
import uuid
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ---------------------------------------------------------------------------
# Trace ID in response
# ---------------------------------------------------------------------------


class TestTraceIdPresence:
    """Trace ID should be present and valid in every chat response."""

    @pytest.mark.asyncio
    async def test_trace_id_in_audit(self, client):
        """Chat response audit contains a trace_id."""
        async with client as c:
            resp = await c.post(
                "/chat",
                json={"message": "check status", "mode": "plan_only"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "audit" in data
        assert "trace_id" in data["audit"]
        assert len(data["audit"]["trace_id"]) > 0

    @pytest.mark.asyncio
    async def test_trace_id_is_valid_uuid(self, client):
        """Trace ID should be a valid UUID."""
        async with client as c:
            resp = await c.post(
                "/chat",
                json={"message": "check status", "mode": "plan_only"},
            )
        trace_id = resp.json()["audit"]["trace_id"]
        # Should not raise
        parsed = uuid.UUID(trace_id)
        assert str(parsed) == trace_id

    @pytest.mark.asyncio
    async def test_trace_id_unique_per_request(self, client):
        """Each request should get a unique trace ID."""
        trace_ids = []
        async with client as c:
            for _ in range(3):
                resp = await c.post(
                    "/chat",
                    json={"message": "check status", "mode": "plan_only"},
                )
                trace_ids.append(resp.json()["audit"]["trace_id"])
        assert len(set(trace_ids)) == 3, "All trace IDs should be unique"

    @pytest.mark.asyncio
    async def test_trace_id_in_execute_safe_mode(self, client):
        """Trace ID present in execute_safe responses too."""
        async with client as c:
            resp = await c.post(
                "/chat",
                json={"message": "check status", "mode": "execute_safe"},
            )
        assert resp.status_code == 200
        trace_id = resp.json()["audit"]["trace_id"]
        uuid.UUID(trace_id)  # validates format


# ---------------------------------------------------------------------------
# X-Trace-Id response header
# ---------------------------------------------------------------------------


class TestTraceIdHeader:
    """X-Trace-Id header should be returned on chat responses."""

    @pytest.mark.asyncio
    async def test_x_trace_id_header_present(self, client):
        """Chat response includes X-Trace-Id header."""
        async with client as c:
            resp = await c.post(
                "/chat",
                json={"message": "check status", "mode": "plan_only"},
            )
        assert "x-trace-id" in resp.headers
        assert len(resp.headers["x-trace-id"]) > 0

    @pytest.mark.asyncio
    async def test_x_trace_id_matches_body(self, client):
        """X-Trace-Id header should match the audit.trace_id in body."""
        async with client as c:
            resp = await c.post(
                "/chat",
                json={"message": "check status", "mode": "plan_only"},
            )
        header_trace_id = resp.headers["x-trace-id"]
        body_trace_id = resp.json()["audit"]["trace_id"]
        assert header_trace_id == body_trace_id

    @pytest.mark.asyncio
    async def test_health_no_trace_header(self, client):
        """Health endpoint should NOT have X-Trace-Id header."""
        async with client as c:
            resp = await c.get("/health")
        assert "x-trace-id" not in resp.headers


# ---------------------------------------------------------------------------
# Health endpoint observability status
# ---------------------------------------------------------------------------


class TestHealthObservability:
    """Health endpoint should report observability status."""

    @pytest.mark.asyncio
    async def test_health_includes_observability(self, client):
        """Health response includes observability field."""
        async with client as c:
            resp = await c.get("/health")
        data = resp.json()
        assert "observability" in data
        assert data["observability"] in ("langfuse", "mock", "disabled")

    @pytest.mark.asyncio
    async def test_health_mock_when_no_langfuse(self, client):
        """Without Langfuse keys, observability should be 'mock'."""
        async with client as c:
            resp = await c.get("/health")
        # Default test env has no Langfuse keys → mock client
        assert resp.json()["observability"] == "mock"


# ---------------------------------------------------------------------------
# Observability client selection
# ---------------------------------------------------------------------------


class TestObservabilityClientSelection:
    """Observability client should be selected based on environment."""

    def test_mock_client_when_no_env_vars(self):
        """Without LANGFUSE env vars, get_observability_client returns mock."""
        from app.observability import MockObservabilityClient, get_observability_client

        client = get_observability_client(use_mock=True)
        assert isinstance(client, MockObservabilityClient)

    def test_mock_client_explicit(self):
        """use_mock=True always returns MockObservabilityClient."""
        from app.observability import MockObservabilityClient, get_observability_client

        client = get_observability_client(use_mock=True)
        assert isinstance(client, MockObservabilityClient)

    def test_langfuse_client_when_env_vars_set(self):
        """With LANGFUSE env vars, should return LangfuseObservabilityClient."""
        from app.observability import LangfuseObservabilityClient, get_observability_client

        with patch.dict(os.environ, {
            "LANGFUSE_PUBLIC_KEY": "pk-test-123",
            "LANGFUSE_SECRET_KEY": "sk-test-456",
        }):
            client = get_observability_client(use_mock=False)
            assert isinstance(client, LangfuseObservabilityClient)

    def test_fallback_to_mock_when_no_env(self):
        """Without LANGFUSE env vars and use_mock=False, falls back to mock."""
        from app.observability import MockObservabilityClient, get_observability_client

        with patch.dict(os.environ, {}, clear=True):
            client = get_observability_client(use_mock=False)
            assert isinstance(client, MockObservabilityClient)


# ---------------------------------------------------------------------------
# Trace spans for tool calls
# ---------------------------------------------------------------------------


class TestTraceSpans:
    """Tool calls should create observable spans."""

    @pytest.mark.asyncio
    async def test_mock_client_records_traces(self):
        """MockObservabilityClient should record traces."""
        from app.observability import MockObservabilityClient

        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        assert trace.name == "test"
        assert trace.user_id == "test-user"
        assert len(client.traces) == 1

    @pytest.mark.asyncio
    async def test_trace_creates_child_spans(self):
        """Traces should support creating child spans."""
        from app.observability import MockObservabilityClient

        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="user")
        span = trace.create_span(name="tool-get_logs")
        assert span.name == "tool-get_logs"
        assert span.trace_id == trace.trace_id

    @pytest.mark.asyncio
    async def test_span_lifecycle(self):
        """Spans should track input, output, status, and end."""
        from app.observability import MockObservabilityClient

        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="user")
        span = trace.create_span(name="op")
        span.set_input({"key": "value"})
        span.set_output({"result": "done"})
        span.set_status("success")
        span.end()

        assert span.input_data == {"key": "value"}
        assert span.output_data == {"result": "done"}
        assert span.status == "success"
        assert span.ended is True
        assert span.end_time is not None

    @pytest.mark.asyncio
    async def test_generation_tracks_tokens(self):
        """Generation spans should track token usage."""
        from app.observability import MockObservabilityClient

        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="user")
        gen = trace.create_generation(
            name="llm-call",
            model="gpt-4",
            input_messages=[{"role": "user", "content": "hello"}],
        )
        gen.set_usage(prompt_tokens=10, completion_tokens=20)
        gen.end()

        assert gen.prompt_tokens == 10
        assert gen.completion_tokens == 20
        assert gen.total_tokens == 30
        assert gen.ended is True

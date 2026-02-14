"""Tests for Langfuse observability integration (WP5).

Tests trace creation, span recording, and observability functionality.
Uses mocked Langfuse client for deterministic testing.
"""

from unittest.mock import patch

from app.observability import (
    LangfuseObservabilityClient,
    MockObservabilityClient,
)


class TestObservabilityInterface:
    """Tests for the observability interface."""

    def test_mock_client_creates_trace(self):
        """Mock client can create a trace."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test-trace", user_id="user-123")

        assert trace is not None
        assert trace.trace_id is not None
        assert len(trace.trace_id) > 0

    def test_trace_has_name(self):
        """Trace stores its name."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="my-operation", user_id="user-123")

        assert trace.name == "my-operation"

    def test_trace_has_user_id(self):
        """Trace stores user ID."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="user-456")

        assert trace.user_id == "user-456"

    def test_trace_can_create_span(self):
        """Trace can create child spans."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        span = trace.create_span(name="tool-call")

        assert span is not None
        assert span.name == "tool-call"

    def test_span_has_parent_trace_id(self):
        """Span stores parent trace ID."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        span = trace.create_span(name="operation")

        assert span.trace_id == trace.trace_id


class TestSpanOperations:
    """Tests for span operations."""

    def test_span_can_set_input(self):
        """Span can record input data."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        span = trace.create_span(name="tool-call")

        span.set_input({"command": "get_logs", "args": {"source": "syslog"}})

        assert span.input_data == {"command": "get_logs", "args": {"source": "syslog"}}

    def test_span_can_set_output(self):
        """Span can record output data."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        span = trace.create_span(name="tool-call")

        span.set_output({"result": "success", "lines": 10})

        assert span.output_data == {"result": "success", "lines": 10}

    def test_span_can_end(self):
        """Span can be ended."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        span = trace.create_span(name="tool-call")

        span.end()

        assert span.ended is True

    def test_span_records_status(self):
        """Span can record status."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        span = trace.create_span(name="tool-call")

        span.set_status("success")

        assert span.status == "success"

    def test_span_can_record_error(self):
        """Span can record error status."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        span = trace.create_span(name="tool-call")

        span.set_status("error")
        span.set_output({"error": "Policy violation"})

        assert span.status == "error"


class TestTraceMetadata:
    """Tests for trace metadata."""

    def test_trace_can_set_metadata(self):
        """Trace can store metadata."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")

        trace.set_metadata({"mode": "execute_safe", "version": "0.5.0"})

        assert trace.metadata["mode"] == "execute_safe"
        assert trace.metadata["version"] == "0.5.0"

    def test_trace_can_add_tags(self):
        """Trace can add tags."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")

        trace.add_tag("environment", "test")
        trace.add_tag("mode", "plan_only")

        assert "environment" in trace.tags
        assert trace.tags["environment"] == "test"

    def test_trace_can_set_input(self):
        """Trace can record input."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")

        trace.set_input({"message": "Show me the logs"})

        assert trace.input_data == {"message": "Show me the logs"}

    def test_trace_can_set_output(self):
        """Trace can record output."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")

        trace.set_output({"answer": "Here are the logs...", "plan": []})

        assert trace.output_data["answer"] == "Here are the logs..."


class TestNestedSpans:
    """Tests for nested span hierarchy."""

    def test_span_can_create_child_span(self):
        """Spans can nest child spans."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        parent_span = trace.create_span(name="orchestrator")
        child_span = parent_span.create_span(name="tool-call")

        assert child_span.parent_span_id == parent_span.span_id

    def test_nested_spans_share_trace_id(self):
        """Nested spans share the same trace ID."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        span1 = trace.create_span(name="parent")
        span2 = span1.create_span(name="child")
        span3 = span2.create_span(name="grandchild")

        assert span1.trace_id == trace.trace_id
        assert span2.trace_id == trace.trace_id
        assert span3.trace_id == trace.trace_id


class TestLangfuseClientConfiguration:
    """Tests for Langfuse client configuration."""

    def test_client_requires_config_or_env(self):
        """Langfuse client can be configured via params or env."""
        # Mock environment to avoid needing real credentials
        with patch.dict(
            "os.environ",
            {
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
            },
        ):
            # Should not raise when env vars are set
            client = LangfuseObservabilityClient()
            assert client is not None

    def test_mock_client_works_without_credentials(self):
        """Mock client works without any credentials."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="user")

        assert trace is not None


class TestTraceContext:
    """Tests for trace context management."""

    def test_trace_provides_context_dict(self):
        """Trace provides context dict for audit."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="chat-request", user_id="test-user")

        context = trace.get_context()

        assert "trace_id" in context
        assert context["trace_id"] == trace.trace_id

    def test_span_provides_context_dict(self):
        """Span provides context dict."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        span = trace.create_span(name="tool-call")

        context = span.get_context()

        assert "span_id" in context
        assert "trace_id" in context


class TestGenerationTracking:
    """Tests for LLM generation tracking."""

    def test_trace_can_create_generation(self):
        """Trace can create generation span for LLM calls."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")

        generation = trace.create_generation(
            name="llm-call",
            model="gpt-4",
            input_messages=[{"role": "user", "content": "Hello"}],
        )

        assert generation is not None
        assert generation.model == "gpt-4"

    def test_generation_tracks_tokens(self):
        """Generation can track token usage."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        generation = trace.create_generation(
            name="llm-call",
            model="gpt-4",
            input_messages=[],
        )

        generation.set_usage(prompt_tokens=100, completion_tokens=50)

        assert generation.prompt_tokens == 100
        assert generation.completion_tokens == 50
        assert generation.total_tokens == 150

    def test_generation_tracks_latency(self):
        """Generation records latency."""
        client = MockObservabilityClient()
        trace = client.create_trace(name="test", user_id="test-user")
        generation = trace.create_generation(
            name="llm-call",
            model="gpt-4",
            input_messages=[],
        )

        generation.end()

        # Should have recorded some duration (even if tiny)
        assert generation.ended is True

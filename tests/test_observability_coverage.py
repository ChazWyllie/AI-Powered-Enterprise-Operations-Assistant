"""Targeted coverage tests for observability module (WP6).

Covers Span/Generation/Trace methods, Langfuse client paths,
and factory function branches.
"""

import os
from unittest.mock import MagicMock, patch

from app.observability import (
    Generation,
    LangfuseObservabilityClient,
    MockObservabilityClient,
    Span,
    Trace,
    get_observability_client,
)


class TestSpanMethods:
    """Tests for Span dataclass methods."""

    def test_set_input(self):
        """set_input stores data."""
        span = Span(name="test", trace_id="t1")
        span.set_input({"key": "value"})
        assert span.input_data == {"key": "value"}

    def test_set_output(self):
        """set_output stores data."""
        span = Span(name="test", trace_id="t1")
        span.set_output({"result": 42})
        assert span.output_data == {"result": 42}

    def test_set_status(self):
        """set_status stores status string."""
        span = Span(name="test", trace_id="t1")
        span.set_status("success")
        assert span.status == "success"

    def test_end_marks_ended(self):
        """end() sets ended=True and records end_time."""
        span = Span(name="test", trace_id="t1")
        assert span.ended is False
        assert span.end_time is None
        span.end()
        assert span.ended is True
        assert span.end_time is not None

    def test_create_child_span(self):
        """create_span creates a child with correct parent."""
        parent = Span(name="parent", trace_id="t1")
        child = parent.create_span("child")
        assert child.name == "child"
        assert child.trace_id == "t1"
        assert child.parent_span_id == parent.span_id

    def test_get_context(self):
        """get_context returns span_id, trace_id, name."""
        span = Span(name="test-span", trace_id="trace-123")
        ctx = span.get_context()
        assert ctx["name"] == "test-span"
        assert ctx["trace_id"] == "trace-123"
        assert "span_id" in ctx

    def test_set_input_with_langfuse_span(self):
        """set_input delegates to Langfuse span if present."""
        span = Span(name="test", trace_id="t1")
        mock_lf = MagicMock()
        span._langfuse_span = mock_lf
        span.set_input({"key": "val"})
        mock_lf.update.assert_called_once_with(input={"key": "val"})

    def test_set_output_with_langfuse_span(self):
        """set_output delegates to Langfuse span if present."""
        span = Span(name="test", trace_id="t1")
        mock_lf = MagicMock()
        span._langfuse_span = mock_lf
        span.set_output({"result": 1})
        mock_lf.update.assert_called_once_with(output={"result": 1})

    def test_set_status_with_langfuse_span_error(self):
        """set_status sends ERROR level to Langfuse on error."""
        span = Span(name="test", trace_id="t1")
        mock_lf = MagicMock()
        span._langfuse_span = mock_lf
        span.set_status("error")
        mock_lf.update.assert_called_once_with(level="ERROR")

    def test_set_status_with_langfuse_span_default(self):
        """set_status sends DEFAULT level for non-error."""
        span = Span(name="test", trace_id="t1")
        mock_lf = MagicMock()
        span._langfuse_span = mock_lf
        span.set_status("success")
        mock_lf.update.assert_called_once_with(level="DEFAULT")

    def test_end_with_langfuse_span(self):
        """end() calls Langfuse span.end()."""
        span = Span(name="test", trace_id="t1")
        mock_lf = MagicMock()
        span._langfuse_span = mock_lf
        span.end()
        mock_lf.end.assert_called_once()

    def test_create_span_with_langfuse_span(self):
        """create_span creates child with Langfuse child span."""
        parent = Span(name="parent", trace_id="t1")
        mock_lf = MagicMock()
        mock_child_lf = MagicMock()
        mock_lf.span.return_value = mock_child_lf
        parent._langfuse_span = mock_lf

        child = parent.create_span("child")
        mock_lf.span.assert_called_once_with(name="child")
        assert child._langfuse_span is mock_child_lf


class TestGenerationMethods:
    """Tests for Generation dataclass methods."""

    def test_total_tokens(self):
        """total_tokens sums prompt + completion."""
        gen = Generation(
            name="gen1",
            trace_id="t1",
            model="gpt-4",
            input_messages=[],
            prompt_tokens=10,
            completion_tokens=5,
        )
        assert gen.total_tokens == 15

    def test_set_output(self):
        """set_output stores the message."""
        gen = Generation(name="gen1", trace_id="t1", model="gpt-4", input_messages=[])
        gen.set_output({"content": "answer"})
        assert gen.output_message == {"content": "answer"}

    def test_set_usage(self):
        """set_usage updates token counts."""
        gen = Generation(name="gen1", trace_id="t1", model="gpt-4", input_messages=[])
        gen.set_usage(100, 50)
        assert gen.prompt_tokens == 100
        assert gen.completion_tokens == 50
        assert gen.total_tokens == 150

    def test_end(self):
        """end() marks generation as ended."""
        gen = Generation(name="gen1", trace_id="t1", model="gpt-4", input_messages=[])
        gen.end()
        assert gen.ended is True
        assert gen.end_time is not None

    def test_set_output_with_langfuse(self):
        """set_output delegates to Langfuse generation."""
        gen = Generation(name="gen1", trace_id="t1", model="gpt-4", input_messages=[])
        mock_lf = MagicMock()
        gen._langfuse_generation = mock_lf
        gen.set_output({"content": "test"})
        mock_lf.update.assert_called_once_with(output={"content": "test"})

    def test_set_usage_with_langfuse(self):
        """set_usage sends usage to Langfuse."""
        gen = Generation(name="gen1", trace_id="t1", model="gpt-4", input_messages=[])
        mock_lf = MagicMock()
        gen._langfuse_generation = mock_lf
        gen.set_usage(100, 50)
        mock_lf.update.assert_called_once_with(
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        )

    def test_end_with_langfuse(self):
        """end() calls Langfuse generation.end()."""
        gen = Generation(name="gen1", trace_id="t1", model="gpt-4", input_messages=[])
        mock_lf = MagicMock()
        gen._langfuse_generation = mock_lf
        gen.end()
        mock_lf.end.assert_called_once()


class TestTraceMethods:
    """Tests for Trace dataclass methods."""

    def test_set_metadata(self):
        """set_metadata updates trace metadata."""
        trace = Trace(name="t1", user_id="u1")
        trace.set_metadata({"env": "test"})
        assert trace.metadata["env"] == "test"

    def test_add_tag(self):
        """add_tag stores key-value tag."""
        trace = Trace(name="t1", user_id="u1")
        trace.add_tag("mode", "plan_only")
        assert trace.tags["mode"] == "plan_only"

    def test_set_input(self):
        """set_input stores input data."""
        trace = Trace(name="t1", user_id="u1")
        trace.set_input({"message": "hello"})
        assert trace.input_data == {"message": "hello"}

    def test_set_output(self):
        """set_output stores output data."""
        trace = Trace(name="t1", user_id="u1")
        trace.set_output({"answer": "world"})
        assert trace.output_data == {"answer": "world"}

    def test_create_span(self):
        """create_span creates child span with trace_id."""
        trace = Trace(name="t1", user_id="u1")
        span = trace.create_span("child")
        assert span.trace_id == trace.trace_id
        assert span.name == "child"

    def test_create_generation(self):
        """create_generation creates generation with correct fields."""
        trace = Trace(name="t1", user_id="u1")
        gen = trace.create_generation("llm-call", "gpt-4", [{"role": "user", "content": "hi"}])
        assert gen.trace_id == trace.trace_id
        assert gen.model == "gpt-4"
        assert gen.name == "llm-call"

    def test_get_context(self):
        """get_context returns trace_id and name."""
        trace = Trace(name="test-trace", user_id="u1")
        ctx = trace.get_context()
        assert ctx["name"] == "test-trace"
        assert "trace_id" in ctx

    def test_set_metadata_with_langfuse(self):
        """set_metadata delegates to Langfuse trace."""
        trace = Trace(name="t1", user_id="u1")
        mock_lf = MagicMock()
        trace._langfuse_trace = mock_lf
        trace.set_metadata({"env": "test"})
        mock_lf.update.assert_called_once()

    def test_add_tag_with_langfuse(self):
        """add_tag delegates to Langfuse trace."""
        trace = Trace(name="t1", user_id="u1")
        mock_lf = MagicMock()
        trace._langfuse_trace = mock_lf
        trace.add_tag("mode", "execute_safe")
        mock_lf.update.assert_called_once()

    def test_set_input_with_langfuse(self):
        """set_input delegates to Langfuse trace."""
        trace = Trace(name="t1", user_id="u1")
        mock_lf = MagicMock()
        trace._langfuse_trace = mock_lf
        trace.set_input({"msg": "hi"})
        mock_lf.update.assert_called_once_with(input={"msg": "hi"})

    def test_set_output_with_langfuse(self):
        """set_output delegates to Langfuse trace."""
        trace = Trace(name="t1", user_id="u1")
        mock_lf = MagicMock()
        trace._langfuse_trace = mock_lf
        trace.set_output({"ans": "hi"})
        mock_lf.update.assert_called_once_with(output={"ans": "hi"})

    def test_create_span_with_langfuse(self):
        """create_span creates Langfuse-backed span."""
        trace = Trace(name="t1", user_id="u1")
        mock_lf = MagicMock()
        mock_span_lf = MagicMock()
        mock_lf.span.return_value = mock_span_lf
        trace._langfuse_trace = mock_lf

        span = trace.create_span("child")
        mock_lf.span.assert_called_once_with(name="child")
        assert span._langfuse_span is mock_span_lf

    def test_create_generation_with_langfuse(self):
        """create_generation creates Langfuse-backed generation."""
        trace = Trace(name="t1", user_id="u1")
        mock_lf = MagicMock()
        mock_gen_lf = MagicMock()
        mock_lf.generation.return_value = mock_gen_lf
        trace._langfuse_trace = mock_lf

        msgs = [{"role": "user", "content": "test"}]
        gen = trace.create_generation("llm", "gpt-4", msgs)
        mock_lf.generation.assert_called_once_with(name="llm", model="gpt-4", input=msgs)
        assert gen._langfuse_generation is mock_gen_lf


class TestLangfuseObservabilityClient:
    """Tests for LangfuseObservabilityClient."""

    def test_init_no_credentials(self):
        """Client initializes without credentials (no crash)."""
        with patch.dict(os.environ, {}, clear=True):
            env = os.environ.copy()
            env.pop("LANGFUSE_PUBLIC_KEY", None)
            env.pop("LANGFUSE_SECRET_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                client = LangfuseObservabilityClient()
                assert client._langfuse is None

    def test_init_import_error(self):
        """Client handles missing langfuse package."""
        with (
            patch.dict(
                os.environ,
                {
                    "LANGFUSE_PUBLIC_KEY": "pk",
                    "LANGFUSE_SECRET_KEY": "sk",
                },
            ),
            patch("builtins.__import__", side_effect=ImportError("no langfuse")),
        ):
            client = LangfuseObservabilityClient(public_key="pk", secret_key="sk")
            assert client._langfuse is None

    def test_create_trace_without_langfuse(self):
        """create_trace works without Langfuse SDK."""
        with patch.dict(os.environ, {}, clear=True):
            env = os.environ.copy()
            env.pop("LANGFUSE_PUBLIC_KEY", None)
            env.pop("LANGFUSE_SECRET_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                client = LangfuseObservabilityClient()
                trace = client.create_trace("test", "user1")
                assert trace.name == "test"
                assert trace.user_id == "user1"

    def test_flush_without_langfuse(self):
        """flush() is no-op without Langfuse."""
        with patch.dict(os.environ, {}, clear=True):
            env = os.environ.copy()
            env.pop("LANGFUSE_PUBLIC_KEY", None)
            env.pop("LANGFUSE_SECRET_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                client = LangfuseObservabilityClient()
                client.flush()  # Should not raise


class TestGetObservabilityClient:
    """Tests for factory function."""

    def test_use_mock_flag(self):
        """use_mock=True returns MockObservabilityClient."""
        client = get_observability_client(use_mock=True)
        assert isinstance(client, MockObservabilityClient)

    def test_no_config_falls_back_to_mock(self):
        """No config falls back to mock."""
        with patch.dict(os.environ, {}, clear=True):
            env = os.environ.copy()
            env.pop("LANGFUSE_PUBLIC_KEY", None)
            env.pop("LANGFUSE_SECRET_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                client = get_observability_client(use_mock=False)
                assert isinstance(client, MockObservabilityClient)

    def test_with_langfuse_config(self):
        """With Langfuse config, returns LangfuseObservabilityClient."""
        with patch.dict(
            os.environ,
            {
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
            },
        ):
            client = get_observability_client(use_mock=False)
            assert isinstance(client, LangfuseObservabilityClient)

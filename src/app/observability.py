"""Observability module for Langfuse integration (WP5).

Provides tracing, span management, and LLM generation tracking for the
AI-Powered Enterprise Operations Assistant.

Classes:
    ObservabilityClient: Abstract base for observability clients
    MockObservabilityClient: Deterministic mock for testing
    LangfuseObservabilityClient: Production Langfuse integration
    Trace: Represents a trace (request lifecycle)
    Span: Represents a span (operation within a trace)
    Generation: Represents an LLM generation span
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Span:
    """Represents a span within a trace.

    Spans track individual operations like tool calls, LLM invocations,
    or other discrete units of work.
    """

    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: str | None = None
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    status: str | None = None
    ended: bool = False
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    _langfuse_span: Any = None

    def set_input(self, data: dict[str, Any]) -> None:
        """Set input data for this span."""
        self.input_data = data
        if self._langfuse_span:
            self._langfuse_span.update(input=data)

    def set_output(self, data: dict[str, Any]) -> None:
        """Set output data for this span."""
        self.output_data = data
        if self._langfuse_span:
            self._langfuse_span.update(output=data)

    def set_status(self, status: str) -> None:
        """Set status for this span."""
        self.status = status
        if self._langfuse_span:
            level = "ERROR" if status == "error" else "DEFAULT"
            self._langfuse_span.update(level=level)

    def end(self) -> None:
        """End this span."""
        self.ended = True
        self.end_time = time.time()
        if self._langfuse_span:
            self._langfuse_span.end()

    def create_span(self, name: str) -> Span:
        """Create a child span."""
        child = Span(
            name=name,
            trace_id=self.trace_id,
            parent_span_id=self.span_id,
        )
        if self._langfuse_span:
            child._langfuse_span = self._langfuse_span.span(name=name)
        return child

    def get_context(self) -> dict[str, str]:
        """Get context dict for this span."""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "name": self.name,
        }


@dataclass
class Generation:
    """Represents an LLM generation span.

    Tracks LLM-specific metadata like model, tokens, and latency.
    """

    name: str
    trace_id: str
    model: str
    input_messages: list[dict[str, Any]]
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    output_message: dict[str, Any] | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    ended: bool = False
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    _langfuse_generation: Any = None

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.prompt_tokens + self.completion_tokens

    def set_output(self, message: dict[str, Any]) -> None:
        """Set the output message."""
        self.output_message = message
        if self._langfuse_generation:
            self._langfuse_generation.update(output=message)

    def set_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Set token usage."""
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        if self._langfuse_generation:
            self._langfuse_generation.update(
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": self.total_tokens,
                }
            )

    def end(self) -> None:
        """End this generation span."""
        self.ended = True
        self.end_time = time.time()
        if self._langfuse_generation:
            self._langfuse_generation.end()


@dataclass
class Trace:
    """Represents a trace (request lifecycle).

    A trace encompasses an entire request from API entry to response,
    containing spans for individual operations.
    """

    name: str
    user_id: str
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    _langfuse_trace: Any = None

    def set_metadata(self, metadata: dict[str, Any]) -> None:
        """Set metadata for this trace."""
        self.metadata.update(metadata)
        if self._langfuse_trace:
            self._langfuse_trace.update(metadata=self.metadata)

    def add_tag(self, key: str, value: str) -> None:
        """Add a tag to this trace."""
        self.tags[key] = value
        if self._langfuse_trace:
            self._langfuse_trace.update(tags=list(self.tags.keys()))

    def set_input(self, data: dict[str, Any]) -> None:
        """Set input data for this trace."""
        self.input_data = data
        if self._langfuse_trace:
            self._langfuse_trace.update(input=data)

    def set_output(self, data: dict[str, Any]) -> None:
        """Set output data for this trace."""
        self.output_data = data
        if self._langfuse_trace:
            self._langfuse_trace.update(output=data)

    def create_span(self, name: str) -> Span:
        """Create a child span."""
        span = Span(name=name, trace_id=self.trace_id)
        if self._langfuse_trace:
            span._langfuse_span = self._langfuse_trace.span(name=name)
        return span

    def create_generation(
        self,
        name: str,
        model: str,
        input_messages: list[dict[str, Any]],
    ) -> Generation:
        """Create a generation span for LLM calls."""
        generation = Generation(
            name=name,
            trace_id=self.trace_id,
            model=model,
            input_messages=input_messages,
        )
        if self._langfuse_trace:
            generation._langfuse_generation = self._langfuse_trace.generation(
                name=name,
                model=model,
                input=input_messages,
            )
        return generation

    def get_context(self) -> dict[str, str]:
        """Get context dict for this trace."""
        return {
            "trace_id": self.trace_id,
            "name": self.name,
        }


class ObservabilityClient(ABC):
    """Abstract base class for observability clients."""

    @abstractmethod
    def create_trace(self, name: str, user_id: str) -> Trace:
        """Create a new trace."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush any pending data."""
        pass


class MockObservabilityClient(ObservabilityClient):
    """Mock observability client for testing.

    Provides full trace/span functionality without requiring
    Langfuse credentials or network access.
    """

    def __init__(self) -> None:
        """Initialize mock client."""
        self.traces: list[Trace] = []
        logger.info("MockObservabilityClient initialized")

    def create_trace(self, name: str, user_id: str) -> Trace:
        """Create a new trace."""
        trace = Trace(name=name, user_id=user_id)
        self.traces.append(trace)
        logger.debug(f"Created mock trace: {trace.trace_id}")
        return trace

    def flush(self) -> None:
        """Flush (no-op for mock)."""
        pass


class LangfuseObservabilityClient(ObservabilityClient):
    """Production Langfuse observability client.

    Integrates with Langfuse cloud for tracing, span management,
    and LLM generation tracking.
    """

    def __init__(
        self,
        public_key: str | None = None,
        secret_key: str | None = None,
        host: str | None = None,
    ) -> None:
        """Initialize Langfuse client.

        Args:
            public_key: Langfuse public key (or LANGFUSE_PUBLIC_KEY env var)
            secret_key: Langfuse secret key (or LANGFUSE_SECRET_KEY env var)
            host: Langfuse host URL (or LANGFUSE_HOST env var)
        """
        self.public_key = public_key or os.environ.get("LANGFUSE_PUBLIC_KEY")
        self.secret_key = secret_key or os.environ.get("LANGFUSE_SECRET_KEY")
        self.host = host or os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

        self._langfuse = None
        self._init_langfuse()

    def _init_langfuse(self) -> None:
        """Initialize Langfuse SDK if credentials are available."""
        if self.public_key and self.secret_key:
            try:
                from langfuse import Langfuse

                self._langfuse = Langfuse(
                    public_key=self.public_key,
                    secret_key=self.secret_key,
                    host=self.host,
                )
                logger.info(f"Langfuse client initialized (host: {self.host})")
            except ImportError:
                logger.warning("Langfuse SDK not installed, using mock")
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse: {e}")
        else:
            logger.warning("Langfuse credentials not configured, tracing disabled")

    def create_trace(self, name: str, user_id: str) -> Trace:
        """Create a new trace."""
        trace = Trace(name=name, user_id=user_id)

        if self._langfuse:
            trace._langfuse_trace = self._langfuse.trace(
                id=trace.trace_id,
                name=name,
                user_id=user_id,
            )
            logger.debug(f"Created Langfuse trace: {trace.trace_id}")
        else:
            logger.debug(f"Created local trace (no Langfuse): {trace.trace_id}")

        return trace

    def flush(self) -> None:
        """Flush pending data to Langfuse."""
        if self._langfuse:
            self._langfuse.flush()
            logger.debug("Flushed Langfuse data")


def get_observability_client(use_mock: bool = False) -> ObservabilityClient:
    """Factory function to get the appropriate observability client.

    Args:
        use_mock: If True, return mock client regardless of config.

    Returns:
        ObservabilityClient instance.
    """
    if use_mock:
        return MockObservabilityClient()

    # Check for Langfuse configuration
    if os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"):
        return LangfuseObservabilityClient()

    # Fall back to mock if no config
    logger.info("No Langfuse config found, using MockObservabilityClient")
    return MockObservabilityClient()

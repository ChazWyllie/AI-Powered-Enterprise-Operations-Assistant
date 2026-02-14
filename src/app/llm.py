"""LLM interface and stub for testing.

WP3: Provides a deterministic LLM stub for testing and an interface for real LLMs.
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a planned tool call."""

    tool: str
    args: dict[str, Any]
    reasoning: str = ""


@dataclass
class LLMResponse:
    """Response from an LLM."""

    answer: str
    tool_calls: list[ToolCall]
    raw_response: str = ""


class LLMInterface(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate(self, message: str, context: dict[str, Any] | None = None) -> LLMResponse:
        """Generate a response for the given message.

        Args:
            message: User message to process.
            context: Optional context including conversation history.

        Returns:
            LLMResponse with answer and planned tool calls.
        """
        pass


class LLMStub(LLMInterface):
    """Deterministic LLM stub for testing.

    Parses user messages and returns predictable tool call plans
    based on keyword matching.
    """

    # Intent patterns for deterministic routing
    INTENT_PATTERNS = {
        "status": [
            r"\bstatus\b",
            r"\bcpu\b",
            r"\bmemory\b",
            r"\bjobs?\b",
            r"\bhealth\b",
            r"\bmetrics?\b",
        ],
        "logs": [
            r"\blogs?\b",
            r"\bsyslog\b",
            r"\berror\b",
            r"\baudit\b",
            r"\bjoblog\b",
            r"\bentries\b",
        ],
        "command": [
            r"\blist\b",
            r"\bshow\b",
            r"\bcat\b",
            r"\bgrep\b",
            r"\bhead\b",
            r"\btail\b",
            r"\bfiles?\b",
            r"\bdirectory\b",
            r"\brun\b",
            r"\bexecute\b",
        ],
        "config": [
            r"\bconfig\b",
            r"\bset\b",
            r"\bupdate\b",
            r"\blevel\b",
            r"\bsetting\b",
            r"\bchange\b",
        ],
        "dangerous": [
            r"\bdelete\b",
            r"\bremove\b",
            r"\brm\b",
            r"\bdrop\b",
            r"\bkill\b",
            r"\bshutdown\b",
        ],
    }

    async def generate(
        self,
        message: str,
        context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> LLMResponse:
        """Generate deterministic response based on message patterns.

        Args:
            message: User message to analyze.
            context: Optional context (unused in stub, for interface compatibility).

        Returns:
            LLMResponse with deterministic tool calls based on intent.
        """
        message_lower = message.lower()
        intents = self._detect_intents(message_lower)

        logger.info(f"LLMStub detected intents: {intents} for message: {message!r}")

        tool_calls = []
        answer_parts = []

        # Generate tool calls based on detected intents
        if "dangerous" in intents:
            # For dangerous requests, acknowledge but don't plan harmful actions
            answer_parts.append(
                "I cannot execute destructive operations. I'll check the current status instead."
            )
            tool_calls.append(
                ToolCall(
                    tool="get_system_status",
                    args={},
                    reasoning="Checking system status instead of performing destructive action",
                )
            )
        else:
            if "status" in intents:
                tool_calls.append(
                    ToolCall(
                        tool="get_system_status",
                        args={},
                        reasoning="User requested system status information",
                    )
                )
                answer_parts.append("I'll check the current system status.")

            if "logs" in intents:
                # Determine which log source based on message
                source = self._detect_log_source(message_lower)
                tool_calls.append(
                    ToolCall(
                        tool="get_logs",
                        args={"source": source, "tail": 20},
                        reasoning=f"User requested {source} logs",
                    )
                )
                answer_parts.append(f"I'll retrieve the recent {source} logs.")

            if "command" in intents:
                # Generate appropriate command based on message
                command = self._generate_safe_command(message_lower)
                tool_calls.append(
                    ToolCall(
                        tool="run_command",
                        args={"command": command, "dry_run": True},
                        reasoning="User requested to run a command",
                    )
                )
                answer_parts.append(f"I'll plan to execute: {command}")

            if "config" in intents:
                # Detect config key and value from message
                key, value = self._detect_config_change(message_lower)
                tool_calls.append(
                    ToolCall(
                        tool="update_config",
                        args={"key": key, "value": value},
                        reasoning=f"User requested to update {key} configuration",
                    )
                )
                answer_parts.append(f"I'll update the {key} setting to {value}.")

        # If no specific intent detected, default to status check
        if not tool_calls:
            tool_calls.append(
                ToolCall(
                    tool="get_system_status",
                    args={},
                    reasoning="Default action: check system status",
                )
            )
            answer_parts.append("I'll check the system status to help answer your question.")

        answer = " ".join(answer_parts)

        return LLMResponse(
            answer=answer,
            tool_calls=tool_calls,
            raw_response=f"[STUB] Processed: {message}",
        )

    def _detect_intents(self, message: str) -> set[str]:
        """Detect intents from message using pattern matching."""
        intents = set()
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    intents.add(intent)
                    break
        return intents

    def _detect_log_source(self, message: str) -> str:
        """Detect which log source the user is asking about."""
        if "error" in message:
            return "error"
        if "audit" in message:
            return "audit"
        if "job" in message:
            return "joblog"
        return "syslog"

    def _generate_safe_command(self, message: str) -> str:
        """Generate a safe command based on the message."""
        if "list" in message or "files" in message or "directory" in message:
            return "ls /sim/"
        if "cat" in message:
            return "cat /sim/syslog.log"
        if "grep" in message:
            return "grep ERROR /sim/syslog.log"
        if "head" in message:
            return "head -n 10 /sim/syslog.log"
        if "tail" in message:
            return "tail -n 10 /sim/syslog.log"
        return "ls /sim/"

    def _detect_config_change(self, message: str) -> tuple[str, str]:
        """Detect config key and value from message."""
        # Check for log level changes
        if "debug" in message:
            return "log_level", "DEBUG"
        if "info" in message:
            return "log_level", "INFO"
        if "warn" in message:
            return "log_level", "WARN"
        if "error" in message and "level" in message:
            return "log_level", "ERROR"

        # Default config change
        return "log_level", "INFO"


class OpenAILLM(LLMInterface):
    """OpenAI GPT-4 LLM interface.

    Production implementation that calls OpenAI API.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4"):
        """Initialize OpenAI LLM.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
            model: Model to use (default: gpt-4).
        """
        import os

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate(self, message: str, context: dict[str, Any] | None = None) -> LLMResponse:
        """Generate response using OpenAI API.

        Args:
            message: User message to process.
            context: Optional context including conversation history.

        Returns:
            LLMResponse with answer and planned tool calls.
        """
        client = self._get_client()

        system_prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._get_tool_definitions(),
                tool_choice="auto",
            )

            # Parse response
            choice = response.choices[0]
            answer = choice.message.content or ""
            tool_calls = []

            if choice.message.tool_calls:
                import json

                for tc in choice.message.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            tool=tc.function.name,
                            args=json.loads(tc.function.arguments),
                            reasoning="LLM decided to call this tool",
                        )
                    )

            return LLMResponse(
                answer=answer,
                tool_calls=tool_calls,
                raw_response=str(response),
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fall back to stub behavior on error
            stub = LLMStub()
            return await stub.generate(message, context)

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        return """You are an AI operations assistant for IBM Z / enterprise mainframe systems.

Your role is to help operators:
1. Check system status (CPU, memory, jobs, subsystems)
2. Review logs (syslog, joblog, audit, error)
3. Execute safe diagnostic commands
4. Update configuration settings

IMPORTANT RULES:
- Only use the provided tools to interact with the system
- Never suggest or plan destructive operations (rm, delete, etc.)
- Always explain what you're doing and why
- For command execution, prefer dry_run=true first
- Only access paths under /sim/

Available tools:
- get_logs: Retrieve log entries
- get_system_status: Get system metrics
- run_command: Execute safe commands (with policy enforcement)
- update_config: Update configuration values"""

    def _get_tool_definitions(self) -> list[dict]:
        """Get OpenAI function/tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_logs",
                    "description": "Retrieve log entries from the system",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "enum": ["syslog", "joblog", "audit", "error"],
                                "description": "Log source to retrieve",
                            },
                            "tail": {
                                "type": "integer",
                                "description": "Number of lines to retrieve",
                                "default": 20,
                            },
                        },
                        "required": ["source"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_status",
                    "description": "Get current system status including CPU, memory, and jobs",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Execute a safe command on the system",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Command to execute",
                            },
                            "dry_run": {
                                "type": "boolean",
                                "description": "If true, validate but don't execute",
                                "default": True,
                            },
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "update_config",
                    "description": "Update a configuration value",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "Configuration key",
                            },
                            "value": {
                                "type": "string",
                                "description": "New value",
                            },
                        },
                        "required": ["key", "value"],
                    },
                },
            },
        ]

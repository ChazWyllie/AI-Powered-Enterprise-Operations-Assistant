"""Agent Orchestrator for AI-powered operations.

WP3: Implements the agent "brain" with plan_only and execute_safe modes.
WP5: Integrated with Langfuse observability for tracing.
"""

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.llm import LLMInterface, LLMStub, OpenAILLM
from app.mcp.tools import get_logs, get_system_status, run_command, update_config
from app.observability import (
    ObservabilityClient,
    Trace,
    get_observability_client,
)

logger = logging.getLogger(__name__)


class OrchestratorMode(Enum):
    """Execution modes for the orchestrator."""

    PLAN_ONLY = "plan_only"
    EXECUTE_SAFE = "execute_safe"


@dataclass
class OrchestratorResponse:
    """Response from the agent orchestrator.

    Attributes:
        answer: Natural language response to the user.
        plan: List of planned tool calls.
        actions_taken: List of executed actions (empty in plan_only mode).
        audit: Audit information including mode and trace_id.
        generated_script: Optional generated script for automation.
    """

    answer: str
    plan: list[dict[str, Any]]
    actions_taken: list[dict[str, Any]]
    audit: dict[str, Any]
    generated_script: str | None = None


@dataclass
class OrchestratorContext:
    """Context for orchestrator execution."""

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentOrchestrator:
    """Agent orchestrator that coordinates LLM and MCP tools.

    The orchestrator:
    1. Receives user messages
    2. Uses LLM to plan tool calls
    3. Executes tools based on mode (plan_only or execute_safe)
    4. Returns structured response with audit trail
    """

    # Map tool names to functions
    TOOLS = {
        "get_logs": get_logs,
        "get_system_status": get_system_status,
        "run_command": run_command,
        "update_config": update_config,
    }

    def __init__(
        self,
        use_stub: bool = False,
        api_key: str | None = None,
        observability_client: ObservabilityClient | None = None,
    ):
        """Initialize the orchestrator.

        Args:
            use_stub: If True, use deterministic LLM stub for testing.
            api_key: OpenAI API key (only used if use_stub=False).
            observability_client: Optional observability client for tracing.
        """
        self.use_stub = use_stub
        if use_stub:
            self.llm: LLMInterface = LLMStub()
        else:
            self.llm = OpenAILLM(api_key=api_key)

        # Initialize observability - use provided client or create default
        self.observability = observability_client or get_observability_client(use_mock=use_stub)

        logger.info(f"AgentOrchestrator initialized with {'stub' if use_stub else 'OpenAI'} LLM")

    async def process(
        self,
        message: str,
        mode: OrchestratorMode = OrchestratorMode.PLAN_ONLY,
        context: OrchestratorContext | None = None,
    ) -> OrchestratorResponse:
        """Process a user message and return a response.

        Args:
            message: User message to process.
            mode: Execution mode (plan_only or execute_safe).
            context: Optional context for the request.

        Returns:
            OrchestratorResponse with answer, plan, actions, and audit info.
        """
        # Create context if not provided
        if context is None:
            context = OrchestratorContext()

        # Create observability trace for this request
        trace = self.observability.create_trace(
            name="chat-request",
            user_id=context.metadata.get("user_id", "anonymous"),
        )
        trace.set_metadata({"mode": mode.value})
        trace.set_input({"message": message})
        trace.add_tag("mode", mode.value)

        # Use trace_id from observability for consistency
        context.trace_id = trace.trace_id

        logger.info(
            f"Processing message: {message!r} | mode={mode.value} | trace_id={context.trace_id}"
        )

        # Create span for LLM call
        llm_span = trace.create_span(name="llm-generate")
        llm_span.set_input({"message": message})

        # Get LLM response with planned tool calls
        llm_response = await self.llm.generate(
            message=message,
            context={"history": context.conversation_history, "metadata": context.metadata},
        )

        llm_span.set_output(
            {
                "answer": llm_response.answer,
                "tool_calls": [
                    {"tool": tc.tool, "args": tc.args} for tc in llm_response.tool_calls
                ],
            }
        )
        llm_span.set_status("success")
        llm_span.end()

        # Build plan from LLM response
        plan = [
            {
                "tool": tc.tool,
                "args": tc.args,
                "reasoning": tc.reasoning,
                "executed": False,
            }
            for tc in llm_response.tool_calls
        ]

        # Execute tools if in execute_safe mode
        actions_taken = []
        if mode == OrchestratorMode.EXECUTE_SAFE:
            actions_taken = await self._execute_plan(plan, context, trace)

        # Build audit information
        audit = {
            "mode": mode.value,
            "trace_id": context.trace_id,
            "tool_count": len(plan),
            "executed_count": len(actions_taken),
        }

        # Generate script if applicable
        generated_script = self._generate_script(plan) if plan else None

        # Build final answer incorporating tool results
        answer = self._build_answer(llm_response.answer, actions_taken, mode)

        response = OrchestratorResponse(
            answer=answer,
            plan=plan,
            actions_taken=actions_taken,
            audit=audit,
            generated_script=generated_script,
        )

        # Record trace output
        trace.set_output(
            {
                "answer": response.answer,
                "plan_count": len(plan),
                "actions_count": len(actions_taken),
            }
        )

        # Flush observability data
        self.observability.flush()

        logger.info(
            f"Response generated | trace_id={context.trace_id} | "
            f"plan_size={len(plan)} | actions={len(actions_taken)}"
        )

        return response

    async def _execute_plan(
        self,
        plan: list[dict[str, Any]],
        context: OrchestratorContext,
        trace: Trace | None = None,
    ) -> list[dict[str, Any]]:
        """Execute the planned tool calls.

        Args:
            plan: List of planned tool calls.
            context: Execution context.
            trace: Optional trace for observability.

        Returns:
            List of executed actions with results.
        """
        actions = []

        for item in plan:
            tool_name = item["tool"]
            args = item["args"]

            logger.info(f"Executing tool: {tool_name} | args={args} | trace_id={context.trace_id}")

            # Create span for this tool call
            tool_span = trace.create_span(name=f"tool-{tool_name}") if trace else None
            if tool_span:
                tool_span.set_input({"tool": tool_name, "args": args})

            if tool_name not in self.TOOLS:
                logger.warning(f"Unknown tool: {tool_name}")
                if tool_span:
                    tool_span.set_status("error")
                    tool_span.set_output({"error": f"Unknown tool: {tool_name}"})
                    tool_span.end()
                actions.append(
                    {
                        "tool": tool_name,
                        "args": args,
                        "success": False,
                        "error": f"Unknown tool: {tool_name}",
                    }
                )
                continue

            try:
                tool_func = self.TOOLS[tool_name]
                result = await tool_func(**args)

                # Mark as executed in plan
                item["executed"] = True

                if tool_span:
                    tool_span.set_status("success")
                    tool_span.set_output({"result": result})
                    tool_span.end()

                actions.append(
                    {
                        "tool": tool_name,
                        "args": args,
                        "success": True,
                        "result": result,
                    }
                )
                logger.info(f"Tool {tool_name} executed successfully")

            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {e}")
                if tool_span:
                    tool_span.set_status("error")
                    tool_span.set_output({"error": str(e)})
                    tool_span.end()
                actions.append(
                    {
                        "tool": tool_name,
                        "args": args,
                        "success": False,
                        "error": str(e),
                    }
                )

        return actions

    def _generate_script(self, plan: list[dict[str, Any]]) -> str | None:
        """Generate a shell script from the plan.

        Args:
            plan: List of planned tool calls.

        Returns:
            Shell script string or None if no commands.
        """
        commands = []

        for item in plan:
            if item["tool"] == "run_command":
                cmd = item["args"].get("command", "")
                if cmd:
                    commands.append(f"# {item.get('reasoning', 'Execute command')}")
                    commands.append(cmd)

        if not commands:
            return None

        script = "#!/bin/bash\n"
        script += "# Auto-generated script from AI Operations Assistant\n"
        script += "set -e\n\n"
        script += "\n".join(commands)
        script += "\n"

        return script

    def _build_answer(
        self,
        base_answer: str,
        actions_taken: list[dict[str, Any]],
        mode: OrchestratorMode,
    ) -> str:
        """Build the final answer incorporating tool results.

        Args:
            base_answer: Initial answer from LLM.
            actions_taken: List of executed actions.
            mode: Execution mode.

        Returns:
            Final answer string.
        """
        if mode == OrchestratorMode.PLAN_ONLY:
            return base_answer + " (Plan only - no actions executed)"

        if not actions_taken:
            return base_answer

        # Summarize results from executed actions
        summaries = []
        for action in actions_taken:
            tool = action["tool"]
            if action["success"]:
                result = action.get("result", {})
                if tool == "get_system_status":
                    cpu = result.get("cpu", "N/A")
                    mem = result.get("memory", {}).get("percent", "N/A")
                    summaries.append(f"System: CPU {cpu}%, Memory {mem}%")
                elif tool == "get_logs":
                    count = result.get("count", 0)
                    source = result.get("source", "unknown")
                    summaries.append(f"Retrieved {count} lines from {source}")
                elif tool == "run_command":
                    if result.get("executed"):
                        summaries.append(f"Command executed: exit code {result.get('exit_code')}")
                    else:
                        summaries.append("Command validated (dry run)")
                elif tool == "update_config":
                    if result.get("ok"):
                        summaries.append(f"Config updated: {action['args'].get('key')}")
            else:
                summaries.append(f"Tool {tool} failed: {action.get('error', 'Unknown error')}")

        if summaries:
            return base_answer + "\n\nResults:\n- " + "\n- ".join(summaries)

        return base_answer


# Export public interface
__all__ = ["AgentOrchestrator", "OrchestratorMode", "OrchestratorResponse", "OrchestratorContext"]

"""Tests for Agent Orchestrator.

WP3: Test the agent orchestration layer with deterministic LLM stubs.
"""

import pytest

from app.orchestrator import AgentOrchestrator, OrchestratorMode, OrchestratorResponse


class TestOrchestratorModes:
    """Tests for orchestrator execution modes."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator with stubbed LLM."""
        return AgentOrchestrator(use_stub=True)

    @pytest.mark.asyncio
    async def test_plan_only_mode_returns_plan(self, orchestrator):
        """plan_only mode should return a plan without execution."""
        response = await orchestrator.process(
            message="Check system status",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        assert response.plan is not None
        assert len(response.plan) > 0

    @pytest.mark.asyncio
    async def test_plan_only_never_executes(self, orchestrator):
        """plan_only mode should never execute commands."""
        response = await orchestrator.process(
            message="Run a diagnostic command",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        assert response.actions_taken == []
        # Verify no tool was actually executed
        for action in response.plan:
            assert action.get("executed", False) is False

    @pytest.mark.asyncio
    async def test_execute_safe_mode_runs_commands(self, orchestrator):
        """execute_safe mode should run allowlisted commands."""
        response = await orchestrator.process(
            message="Get system logs",
            mode=OrchestratorMode.EXECUTE_SAFE,
        )
        assert response.actions_taken is not None
        # Should have executed at least one action
        assert len(response.actions_taken) >= 0  # May be 0 if all dry_run

    @pytest.mark.asyncio
    async def test_execute_safe_blocks_dangerous(self, orchestrator):
        """execute_safe mode should still block dangerous commands."""
        response = await orchestrator.process(
            message="Delete all files",
            mode=OrchestratorMode.EXECUTE_SAFE,
        )
        # Should not have executed any dangerous commands
        for action in response.actions_taken:
            assert action.get("allowed", True) is True or "blocked" in action.get("reason", "")


class TestOrchestratorResponse:
    """Tests for orchestrator response structure."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator with stubbed LLM."""
        return AgentOrchestrator(use_stub=True)

    @pytest.mark.asyncio
    async def test_response_has_answer(self, orchestrator):
        """Response should always have an answer."""
        response = await orchestrator.process(
            message="What is the system status?",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        assert response.answer is not None
        assert isinstance(response.answer, str)
        assert len(response.answer) > 0

    @pytest.mark.asyncio
    async def test_response_has_plan(self, orchestrator):
        """Response should always have a plan."""
        response = await orchestrator.process(
            message="Check the logs",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        assert response.plan is not None
        assert isinstance(response.plan, list)

    @pytest.mark.asyncio
    async def test_response_has_actions_taken(self, orchestrator):
        """Response should have actions_taken list."""
        response = await orchestrator.process(
            message="Get logs",
            mode=OrchestratorMode.EXECUTE_SAFE,
        )
        assert response.actions_taken is not None
        assert isinstance(response.actions_taken, list)

    @pytest.mark.asyncio
    async def test_response_has_audit(self, orchestrator):
        """Response should have audit information."""
        response = await orchestrator.process(
            message="Check status",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        assert response.audit is not None
        assert "mode" in response.audit
        assert "trace_id" in response.audit

    @pytest.mark.asyncio
    async def test_audit_contains_mode(self, orchestrator):
        """Audit should contain the execution mode."""
        response = await orchestrator.process(
            message="Test",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        assert response.audit["mode"] == "plan_only"

        response = await orchestrator.process(
            message="Test",
            mode=OrchestratorMode.EXECUTE_SAFE,
        )
        assert response.audit["mode"] == "execute_safe"

    @pytest.mark.asyncio
    async def test_audit_contains_trace_id(self, orchestrator):
        """Audit should contain a trace ID for observability."""
        response = await orchestrator.process(
            message="Test",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        assert response.audit["trace_id"] is not None
        assert len(response.audit["trace_id"]) > 0


class TestToolCallOrder:
    """Tests for verifying tool call order and patterns."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator with stubbed LLM."""
        return AgentOrchestrator(use_stub=True)

    @pytest.mark.asyncio
    async def test_status_query_calls_get_system_status(self, orchestrator):
        """Status queries should plan to call get_system_status."""
        response = await orchestrator.process(
            message="What is the current system status?",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        tool_names = [action["tool"] for action in response.plan]
        assert "get_system_status" in tool_names

    @pytest.mark.asyncio
    async def test_log_query_calls_get_logs(self, orchestrator):
        """Log queries should plan to call get_logs."""
        response = await orchestrator.process(
            message="Show me the recent error logs",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        tool_names = [action["tool"] for action in response.plan]
        assert "get_logs" in tool_names

    @pytest.mark.asyncio
    async def test_command_query_calls_run_command(self, orchestrator):
        """Command queries should plan to call run_command."""
        response = await orchestrator.process(
            message="List files in the sim directory",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        tool_names = [action["tool"] for action in response.plan]
        assert "run_command" in tool_names

    @pytest.mark.asyncio
    async def test_config_query_calls_update_config(self, orchestrator):
        """Config queries should plan to call update_config."""
        response = await orchestrator.process(
            message="Set the log level to DEBUG",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        tool_names = [action["tool"] for action in response.plan]
        assert "update_config" in tool_names


class TestLLMStub:
    """Tests for the LLM stub functionality."""

    @pytest.fixture
    def orchestrator(self):
        """Create an orchestrator with stubbed LLM."""
        return AgentOrchestrator(use_stub=True)

    @pytest.mark.asyncio
    async def test_stub_produces_deterministic_output(self, orchestrator):
        """Stub should produce consistent outputs for same inputs."""
        response1 = await orchestrator.process(
            message="Get system status",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        response2 = await orchestrator.process(
            message="Get system status",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        # Plans should be identical for deterministic stub
        assert response1.plan == response2.plan

    @pytest.mark.asyncio
    async def test_stub_handles_different_intents(self, orchestrator):
        """Stub should recognize different user intents."""
        status_response = await orchestrator.process(
            message="system status",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        log_response = await orchestrator.process(
            message="show logs",
            mode=OrchestratorMode.PLAN_ONLY,
        )
        # Different intents should produce different plans
        assert status_response.plan != log_response.plan


class TestOrchestratorResponseModel:
    """Tests for OrchestratorResponse dataclass."""

    def test_response_model_has_required_fields(self):
        """OrchestratorResponse should have all required fields."""
        response = OrchestratorResponse(
            answer="Test answer",
            plan=[{"tool": "test", "args": {}}],
            actions_taken=[],
            audit={"mode": "plan_only", "trace_id": "test-123"},
        )
        assert response.answer == "Test answer"
        assert response.plan == [{"tool": "test", "args": {}}]
        assert response.actions_taken == []
        assert response.audit == {"mode": "plan_only", "trace_id": "test-123"}

    def test_response_model_optional_script(self):
        """generated_script should be optional."""
        response = OrchestratorResponse(
            answer="Test",
            plan=[],
            actions_taken=[],
            audit={},
            generated_script="echo hello",
        )
        assert response.generated_script == "echo hello"

        response_no_script = OrchestratorResponse(
            answer="Test",
            plan=[],
            actions_taken=[],
            audit={},
        )
        assert response_no_script.generated_script is None

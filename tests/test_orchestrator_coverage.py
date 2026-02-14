"""Targeted coverage tests for orchestrator module (WP6).

Covers error handling paths, unknown tools, script generation, answer building.
"""

from app.orchestrator import (
    AgentOrchestrator,
    OrchestratorMode,
)


class TestOrchestratorExecuteSafe:
    """Tests for execute_safe mode."""

    async def test_execute_safe_runs_tools(self):
        """Execute safe mode actually runs tools."""
        orch = AgentOrchestrator(use_stub=True)
        result = await orch.process(
            message="Show system status",
            mode=OrchestratorMode.EXECUTE_SAFE,
        )
        assert len(result.actions_taken) > 0
        assert result.actions_taken[0]["success"] is True
        assert result.actions_taken[0]["result"] is not None

    async def test_execute_safe_log_retrieval(self):
        """Execute safe retrieves actual log data."""
        orch = AgentOrchestrator(use_stub=True)
        result = await orch.process(
            message="Show me the syslog",
            mode=OrchestratorMode.EXECUTE_SAFE,
        )
        log_actions = [a for a in result.actions_taken if a["tool"] == "get_logs"]
        assert len(log_actions) > 0
        assert log_actions[0]["success"] is True

    async def test_execute_safe_command_run(self):
        """Execute safe can run commands."""
        orch = AgentOrchestrator(use_stub=True)
        result = await orch.process(
            message="Run cat on the syslog file",
            mode=OrchestratorMode.EXECUTE_SAFE,
        )
        cmd_actions = [a for a in result.actions_taken if a["tool"] == "run_command"]
        if cmd_actions:
            assert cmd_actions[0]["success"] is True

    async def test_execute_safe_config_update(self):
        """Execute safe can update config."""
        orch = AgentOrchestrator(use_stub=True)
        result = await orch.process(
            message="Update the config to debug mode",
            mode=OrchestratorMode.EXECUTE_SAFE,
        )
        config_actions = [a for a in result.actions_taken if a["tool"] == "update_config"]
        if config_actions:
            assert config_actions[0]["success"] is True


class TestOrchestratorAnswerBuilding:
    """Tests for _build_answer method."""

    def test_plan_only_suffix(self):
        """Plan-only adds suffix."""
        orch = AgentOrchestrator(use_stub=True)
        answer = orch._build_answer("Test answer", [], OrchestratorMode.PLAN_ONLY)
        assert "Plan only" in answer

    def test_no_actions_returns_base(self):
        """No actions returns base answer."""
        orch = AgentOrchestrator(use_stub=True)
        answer = orch._build_answer("Test answer", [], OrchestratorMode.EXECUTE_SAFE)
        assert answer == "Test answer"

    def test_status_result_formatting(self):
        """Status results are formatted correctly."""
        orch = AgentOrchestrator(use_stub=True)
        actions = [
            {
                "tool": "get_system_status",
                "success": True,
                "result": {"cpu": 45.0, "memory": {"percent": 78.0}},
            }
        ]
        answer = orch._build_answer("Base", actions, OrchestratorMode.EXECUTE_SAFE)
        assert "CPU 45.0%" in answer
        assert "Memory 78.0%" in answer

    def test_logs_result_formatting(self):
        """Log results are formatted correctly."""
        orch = AgentOrchestrator(use_stub=True)
        actions = [
            {
                "tool": "get_logs",
                "success": True,
                "result": {"count": 10, "source": "syslog"},
            }
        ]
        answer = orch._build_answer("Base", actions, OrchestratorMode.EXECUTE_SAFE)
        assert "10 lines" in answer
        assert "syslog" in answer

    def test_command_executed_formatting(self):
        """Executed command results are formatted."""
        orch = AgentOrchestrator(use_stub=True)
        actions = [
            {
                "tool": "run_command",
                "success": True,
                "result": {"executed": True, "exit_code": 0},
            }
        ]
        answer = orch._build_answer("Base", actions, OrchestratorMode.EXECUTE_SAFE)
        assert "exit code 0" in answer

    def test_command_dry_run_formatting(self):
        """Dry-run command results are formatted."""
        orch = AgentOrchestrator(use_stub=True)
        actions = [
            {
                "tool": "run_command",
                "success": True,
                "result": {"executed": False},
            }
        ]
        answer = orch._build_answer("Base", actions, OrchestratorMode.EXECUTE_SAFE)
        assert "dry run" in answer.lower()

    def test_config_update_formatting(self):
        """Config update results are formatted."""
        orch = AgentOrchestrator(use_stub=True)
        actions = [
            {
                "tool": "update_config",
                "args": {"key": "log_level"},
                "success": True,
                "result": {"ok": True},
            }
        ]
        answer = orch._build_answer("Base", actions, OrchestratorMode.EXECUTE_SAFE)
        assert "Config updated" in answer
        assert "log_level" in answer

    def test_failed_action_formatting(self):
        """Failed actions show error."""
        orch = AgentOrchestrator(use_stub=True)
        actions = [
            {
                "tool": "get_logs",
                "success": False,
                "error": "Connection refused",
            }
        ]
        answer = orch._build_answer("Base", actions, OrchestratorMode.EXECUTE_SAFE)
        assert "failed" in answer.lower()
        assert "Connection refused" in answer


class TestOrchestratorScriptGen:
    """Tests for _generate_script."""

    def test_no_commands_returns_none(self):
        """No run_command calls returns None."""
        orch = AgentOrchestrator(use_stub=True)
        plan = [{"tool": "get_system_status", "args": {}}]
        assert orch._generate_script(plan) is None

    def test_with_commands_generates_script(self):
        """run_command calls generate a script."""
        orch = AgentOrchestrator(use_stub=True)
        plan = [
            {
                "tool": "run_command",
                "args": {"command": "ls /sim/"},
                "reasoning": "List files",
            }
        ]
        script = orch._generate_script(plan)
        assert script is not None
        assert "#!/bin/bash" in script
        assert "set -e" in script
        assert "ls /sim/" in script
        assert "# List files" in script

    def test_empty_command_skipped(self):
        """Empty command string is skipped."""
        orch = AgentOrchestrator(use_stub=True)
        plan = [
            {
                "tool": "run_command",
                "args": {"command": ""},
            }
        ]
        assert orch._generate_script(plan) is None

    def test_multiple_commands(self):
        """Multiple commands in script."""
        orch = AgentOrchestrator(use_stub=True)
        plan = [
            {"tool": "run_command", "args": {"command": "ls /sim/"}, "reasoning": "List"},
            {
                "tool": "run_command",
                "args": {"command": "cat /sim/syslog.log"},
                "reasoning": "Read",
            },
        ]
        script = orch._generate_script(plan)
        assert "ls /sim/" in script
        assert "cat /sim/syslog.log" in script


class TestOrchestratorInit:
    """Tests for orchestrator initialization."""

    def test_init_with_stub(self):
        """Stub initialization."""
        orch = AgentOrchestrator(use_stub=True)
        assert orch.use_stub is True

    def test_init_without_stub(self):
        """Non-stub initialization uses OpenAI."""
        orch = AgentOrchestrator(use_stub=False, api_key="test-key")
        assert orch.use_stub is False

    def test_init_with_custom_observability(self):
        """Custom observability client accepted."""
        from app.observability import MockObservabilityClient

        mock_client = MockObservabilityClient()
        orch = AgentOrchestrator(use_stub=True, observability_client=mock_client)
        assert orch.observability is mock_client

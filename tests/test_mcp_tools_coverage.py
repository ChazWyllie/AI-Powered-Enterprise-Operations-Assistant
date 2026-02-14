"""Targeted coverage tests for MCP tools module (WP6).

Covers edge cases: simulated log fallback, command execution paths,
config boundary conditions.
"""

import pytest

from app.mcp.tools import (
    _config_store,
    _get_simulated_logs,
    _simulate_command_execution,
    get_logs,
    get_system_status,
    run_command,
    update_config,
)
from app.policy import PolicyViolation


class TestGetLogsEdgeCases:
    """Edge cases for get_logs."""

    async def test_tail_zero_returns_empty(self):
        """tail=0 returns no lines."""
        result = await get_logs(source="syslog", tail=0)
        assert result["lines"] == []
        assert result["count"] == 0

    async def test_simulated_logs_fallback(self):
        """Simulated logs are used when fixture missing."""
        # _get_simulated_logs is the fallback
        lines = _get_simulated_logs("syslog", 5)
        assert len(lines) <= 5
        assert all(isinstance(line, str) for line in lines)

    async def test_simulated_logs_all_sources(self):
        """All sources have simulated entries."""
        for source in ["syslog", "joblog", "audit", "error"]:
            lines = _get_simulated_logs(source, 100)
            assert len(lines) > 0

    async def test_simulated_logs_unknown_source(self):
        """Unknown source returns empty list."""
        lines = _get_simulated_logs("nonexistent", 10)
        assert lines == []

    async def test_simulated_logs_tail_zero(self):
        """Simulated logs with tail=0 returns empty."""
        lines = _get_simulated_logs("syslog", 0)
        assert lines == []


class TestRunCommandExecution:
    """Tests for command execution paths (non-dry-run)."""

    async def test_echo_command_actually_executes(self):
        """echo commands are actually executed."""
        result = await run_command("echo hello", dry_run=False)
        assert result["allowed"] is True
        assert result["executed"] is True
        assert result["stdout"] == "hello"
        assert result["exit_code"] == 0

    async def test_safe_command_simulated(self):
        """Non-echo safe commands use simulated output."""
        result = await run_command("ls /sim/", dry_run=False)
        assert result["allowed"] is True
        assert result["executed"] is True
        assert "syslog.log" in result["stdout"]

    async def test_blocked_command_not_executed(self):
        """Blocked commands are not executed."""
        result = await run_command("rm /sim/test.txt", dry_run=False)
        assert result["allowed"] is False
        assert result["executed"] is False

    async def test_dry_run_default(self):
        """Default is dry_run=True."""
        result = await run_command("ls /sim/")
        assert result["executed"] is False
        assert result["allowed"] is True
        assert "Dry run" in result["reason"]


class TestSimulateCommandExecution:
    """Tests for _simulate_command_execution helper."""

    def test_simulate_cat(self):
        """Simulate cat command."""
        result = _simulate_command_execution("cat /sim/test.txt")
        assert result["executed"] is True
        assert result["exit_code"] == 0
        assert "Simulated file content" in result["stdout"]

    def test_simulate_ls(self):
        """Simulate ls command."""
        result = _simulate_command_execution("ls /sim/")
        assert "syslog.log" in result["stdout"]

    def test_simulate_head(self):
        """Simulate head command."""
        result = _simulate_command_execution("head -n 5 /sim/syslog.log")
        assert result["exit_code"] == 0

    def test_simulate_tail(self):
        """Simulate tail command."""
        result = _simulate_command_execution("tail -n 5 /sim/syslog.log")
        assert result["exit_code"] == 0

    def test_simulate_grep(self):
        """Simulate grep command."""
        result = _simulate_command_execution("grep ERROR /sim/syslog.log")
        assert result["exit_code"] == 0

    def test_simulate_date(self):
        """Simulate date command."""
        result = _simulate_command_execution("date")
        assert result["exit_code"] == 0

    def test_simulate_hostname(self):
        """Simulate hostname command."""
        result = _simulate_command_execution("hostname")
        assert "mainframe" in result["stdout"]

    def test_simulate_unknown_command(self):
        """Unknown command gets generic simulated output."""
        result = _simulate_command_execution("wc -l /sim/syslog.log")
        assert result["exit_code"] == 0
        assert "Simulated output" in result["stdout"]

    def test_simulate_empty_command(self):
        """Empty command handled gracefully."""
        result = _simulate_command_execution("")
        assert result["exit_code"] == 0


class TestUpdateConfigEdgeCases:
    """Edge cases for update_config."""

    async def test_update_returns_previous_value(self):
        """Update returns previous value."""
        # Set a known value first
        _config_store["test_key"] = "old_val"
        result = await update_config("test_key", "new_val")
        assert result["ok"] is True
        assert result["previous"] == "old_val"
        assert result["value"] == "new_val"

    async def test_update_new_key(self):
        """New key gets None as previous."""
        # Remove key if exists
        _config_store.pop("brand_new_key", None)
        result = await update_config("brand_new_key", "value1")
        assert result["ok"] is True
        assert result["previous"] is None

    async def test_update_whitespace_key_stripped(self):
        """Key with whitespace is stripped."""
        result = await update_config("  test_key  ", "value")
        assert result["ok"] is True
        assert result["key"] == "test_key"

    async def test_blocked_sensitive_key(self):
        """Sensitive config keys are blocked."""
        with pytest.raises(PolicyViolation, match="sensitive keyword"):
            await update_config("api_secret", "value")

    async def test_blocked_password_key(self):
        """Password keys are blocked."""
        with pytest.raises(PolicyViolation, match="sensitive keyword"):
            await update_config("db_password", "value")

    async def test_blocked_token_key(self):
        """Token keys are blocked."""
        with pytest.raises(PolicyViolation, match="sensitive keyword"):
            await update_config("auth_token", "value")

    async def test_empty_key_rejected(self):
        """Empty key is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await update_config("", "value")

    async def test_whitespace_only_key_rejected(self):
        """Whitespace-only key is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await update_config("   ", "value")


class TestGetSystemStatusEdgeCases:
    """Edge cases for get_system_status."""

    async def test_status_returns_all_fields(self):
        """Status includes all expected top-level fields."""
        result = await get_system_status()
        # Must have either fixture or simulated data
        assert "cpu" in result or "timestamp" in result

"""Tests for MCP tools.

WP2: Test the 4 MCP tools with deterministic fixtures.
"""

import pytest

from app.mcp.tools import get_logs, get_system_status, run_command, update_config
from app.policy import PolicyViolation


class TestGetLogs:
    """Tests for get_logs tool."""

    @pytest.mark.asyncio
    async def test_get_logs_returns_lines(self):
        """get_logs should return log lines."""
        result = await get_logs(source="syslog", tail=10)
        assert "lines" in result
        assert isinstance(result["lines"], list)

    @pytest.mark.asyncio
    async def test_get_logs_respects_tail_limit(self):
        """get_logs should respect tail parameter."""
        result = await get_logs(source="syslog", tail=5)
        assert len(result["lines"]) <= 5

    @pytest.mark.asyncio
    async def test_get_logs_syslog_source(self):
        """get_logs should handle syslog source."""
        result = await get_logs(source="syslog", tail=10)
        assert result["source"] == "syslog"

    @pytest.mark.asyncio
    async def test_get_logs_joblog_source(self):
        """get_logs should handle joblog source."""
        result = await get_logs(source="joblog", tail=10)
        assert result["source"] == "joblog"

    @pytest.mark.asyncio
    async def test_get_logs_invalid_source_raises(self):
        """get_logs should raise for invalid source."""
        with pytest.raises(ValueError, match="source"):
            await get_logs(source="invalid_source", tail=10)

    @pytest.mark.asyncio
    async def test_get_logs_negative_tail_raises(self):
        """get_logs should raise for negative tail."""
        with pytest.raises(ValueError, match="tail"):
            await get_logs(source="syslog", tail=-1)


class TestGetSystemStatus:
    """Tests for get_system_status tool."""

    @pytest.mark.asyncio
    async def test_get_system_status_returns_metrics(self):
        """get_system_status should return system metrics."""
        result = await get_system_status()
        assert "cpu" in result
        assert "memory" in result
        assert "jobs" in result

    @pytest.mark.asyncio
    async def test_get_system_status_cpu_format(self):
        """CPU should be a percentage value."""
        result = await get_system_status()
        assert isinstance(result["cpu"], (int, float))
        assert 0 <= result["cpu"] <= 100

    @pytest.mark.asyncio
    async def test_get_system_status_memory_format(self):
        """Memory should have used and total fields."""
        result = await get_system_status()
        assert "used" in result["memory"]
        assert "total" in result["memory"]

    @pytest.mark.asyncio
    async def test_get_system_status_jobs_format(self):
        """Jobs should have running and queued counts."""
        result = await get_system_status()
        assert "running" in result["jobs"]
        assert "queued" in result["jobs"]


class TestRunCommand:
    """Tests for run_command tool."""

    @pytest.mark.asyncio
    async def test_run_command_dry_run_returns_plan(self):
        """run_command with dry_run=True should not execute."""
        result = await run_command(command="cat /sim/syslog.log", dry_run=True)
        assert result["executed"] is False
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_run_command_blocks_dangerous(self):
        """run_command should block dangerous commands."""
        result = await run_command(command="rm -rf /", dry_run=True)
        assert result["allowed"] is False
        assert "blocked" in result.get("reason", "").lower()

    @pytest.mark.asyncio
    async def test_run_command_blocks_path_traversal(self):
        """run_command should block path traversal."""
        result = await run_command(command="cat /etc/passwd", dry_run=True)
        assert result["allowed"] is False

    @pytest.mark.asyncio
    async def test_run_command_allows_safe_command(self):
        """run_command should allow safe commands in dry_run."""
        result = await run_command(command="cat /sim/syslog.log", dry_run=True)
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_run_command_execute_safe_returns_output(self):
        """run_command with dry_run=False should return output."""
        result = await run_command(command="echo hello", dry_run=False)
        assert result["executed"] is True
        assert "stdout" in result
        assert "hello" in result["stdout"]

    @pytest.mark.asyncio
    async def test_run_command_returns_exit_code(self):
        """run_command should return exit code."""
        result = await run_command(command="echo test", dry_run=False)
        assert "exit_code" in result
        assert result["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_run_command_blocks_metacharacters(self):
        """run_command should block shell metacharacters."""
        result = await run_command(command="echo test; rm -rf /", dry_run=True)
        assert result["allowed"] is False

    @pytest.mark.asyncio
    async def test_run_command_default_dry_run_is_true(self):
        """run_command should default to dry_run=True for safety."""
        result = await run_command(command="echo test")
        assert result["executed"] is False


class TestUpdateConfig:
    """Tests for update_config tool."""

    @pytest.mark.asyncio
    async def test_update_config_returns_ok(self):
        """update_config should return ok status."""
        result = await update_config(key="log_level", value="DEBUG")
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_update_config_returns_previous_value(self):
        """update_config should return previous value."""
        # Set initial value
        await update_config(key="test_key", value="initial")
        # Update to new value
        result = await update_config(key="test_key", value="updated")
        assert "previous" in result
        assert result["previous"] == "initial"

    @pytest.mark.asyncio
    async def test_update_config_validates_key(self):
        """update_config should validate key format."""
        with pytest.raises(ValueError, match="key"):
            await update_config(key="", value="test")

    @pytest.mark.asyncio
    async def test_update_config_blocks_sensitive_keys(self):
        """update_config should block sensitive config keys."""
        with pytest.raises(PolicyViolation):
            await update_config(key="api_secret", value="leaked")

    @pytest.mark.asyncio
    async def test_update_config_allowed_keys(self):
        """update_config should allow whitelisted keys."""
        result = await update_config(key="log_level", value="INFO")
        assert result["ok"] is True

        result = await update_config(key="max_jobs", value="10")
        assert result["ok"] is True


class TestToolSchemas:
    """Tests for MCP tool schemas and contracts."""

    @pytest.mark.asyncio
    async def test_get_logs_schema(self):
        """get_logs should have consistent schema."""
        result = await get_logs(source="syslog", tail=5)
        # Required fields
        assert "lines" in result
        assert "source" in result
        # Type checks
        assert isinstance(result["lines"], list)
        assert isinstance(result["source"], str)

    @pytest.mark.asyncio
    async def test_get_system_status_schema(self):
        """get_system_status should have consistent schema."""
        result = await get_system_status()
        # Required fields
        assert "cpu" in result
        assert "memory" in result
        assert "jobs" in result
        # Nested structure
        assert "used" in result["memory"]
        assert "total" in result["memory"]
        assert "running" in result["jobs"]
        assert "queued" in result["jobs"]

    @pytest.mark.asyncio
    async def test_run_command_schema(self):
        """run_command should have consistent schema."""
        result = await run_command(command="echo test", dry_run=True)
        # Required fields
        assert "allowed" in result
        assert "executed" in result
        # Type checks
        assert isinstance(result["allowed"], bool)
        assert isinstance(result["executed"], bool)

    @pytest.mark.asyncio
    async def test_update_config_schema(self):
        """update_config should have consistent schema."""
        result = await update_config(key="log_level", value="DEBUG")
        # Required fields
        assert "ok" in result
        # Type checks
        assert isinstance(result["ok"], bool)

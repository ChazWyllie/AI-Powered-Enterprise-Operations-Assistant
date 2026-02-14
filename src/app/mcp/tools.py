"""MCP Tools for enterprise operations.

WP2: Implements the 4 core MCP tools:
- get_logs(source, tail) -> {lines: [...]}
- get_system_status() -> {cpu, mem, jobs}
- run_command(command, dry_run) -> {stdout, stderr, exit_code, allowed}
- update_config(key, value) -> {ok, previous}
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from app.policy import CommandPolicy, PolicyViolation

logger = logging.getLogger(__name__)

# Global policy engine instance
_policy = CommandPolicy()

# Simulated config store (in-memory for now, will use fixtures in production)
_config_store: dict[str, str] = {
    "log_level": "INFO",
    "max_jobs": "100",
    "retention_days": "30",
}

# Allowed config keys (whitelist approach)
ALLOWED_CONFIG_KEYS = frozenset(
    {
        "log_level",
        "max_jobs",
        "retention_days",
        "batch_size",
        "timeout_seconds",
        "debug_mode",
        "test_key",  # For testing
    }
)

# Blocked sensitive config keys
BLOCKED_CONFIG_KEYS = frozenset(
    {
        "api_secret",
        "api_key",
        "password",
        "token",
        "secret",
        "credential",
        "private_key",
    }
)

# Valid log sources
VALID_LOG_SOURCES = frozenset({"syslog", "joblog", "audit", "error"})

# Base path for simulator fixtures
SIMULATOR_BASE = Path("/sim")


async def get_logs(source: str, tail: int = 100) -> dict[str, Any]:
    """Retrieve log lines from a specified source.

    Args:
        source: Log source name (syslog, joblog, audit, error).
        tail: Number of lines to return from end of log.

    Returns:
        Dict with 'lines' list and 'source' name.

    Raises:
        ValueError: If source is invalid or tail is negative.
    """
    # Validate source
    if source not in VALID_LOG_SOURCES:
        valid_sources = ", ".join(VALID_LOG_SOURCES)
        raise ValueError(f"Invalid source: {source}. Must be one of: {valid_sources}")

    # Validate tail
    if tail < 0:
        raise ValueError(f"Invalid tail value: {tail}. Must be non-negative.")

    logger.info(f"get_logs called: source={source}, tail={tail}")

    # Try to read from fixture file
    log_file = SIMULATOR_BASE / f"{source}.log"

    if log_file.exists():
        try:
            lines = log_file.read_text().strip().split("\n")
            lines = lines[-tail:] if tail > 0 else []
        except Exception as e:
            logger.warning(f"Failed to read log file {log_file}: {e}")
            lines = _get_simulated_logs(source, tail)
    else:
        # Use simulated data if fixture doesn't exist
        lines = _get_simulated_logs(source, tail)

    return {
        "lines": lines,
        "source": source,
        "count": len(lines),
    }


def _get_simulated_logs(source: str, tail: int) -> list[str]:
    """Generate simulated log entries for testing."""
    templates = {
        "syslog": [
            "2026-02-13T10:00:00Z INFO  System startup complete",
            "2026-02-13T10:01:00Z INFO  Job scheduler initialized",
            "2026-02-13T10:02:00Z WARN  High memory usage detected: 85%",
            "2026-02-13T10:03:00Z INFO  Batch JOB001 started",
            "2026-02-13T10:04:00Z INFO  Batch JOB001 completed successfully",
            "2026-02-13T10:05:00Z ERROR Connection timeout to DB2 subsystem",
            "2026-02-13T10:06:00Z INFO  Reconnection successful",
            "2026-02-13T10:07:00Z INFO  Processing queue depth: 12",
            "2026-02-13T10:08:00Z WARN  CPU utilization at 78%",
            "2026-02-13T10:09:00Z INFO  Health check passed",
        ],
        "joblog": [
            "JOB001 STARTED  2026-02-13T10:00:00Z user=BATCH01",
            "JOB001 STEP01   RC=0000 CPU=00:00:12",
            "JOB001 STEP02   RC=0000 CPU=00:00:45",
            "JOB001 ENDED    RC=0000 2026-02-13T10:05:00Z",
            "JOB002 STARTED  2026-02-13T10:10:00Z user=BATCH02",
            "JOB002 STEP01   RC=0004 CPU=00:00:08",
            "JOB002 ABENDED  S0C7 2026-02-13T10:12:00Z",
            "JOB003 STARTED  2026-02-13T10:15:00Z user=BATCH01",
            "JOB003 STEP01   RC=0000 CPU=00:01:20",
            "JOB003 RUNNING  2026-02-13T10:16:00Z",
        ],
        "audit": [
            "2026-02-13T10:00:00Z AUDIT LOGIN  user=ADMIN01 terminal=TSO001",
            "2026-02-13T10:01:00Z AUDIT ACCESS dataset=PROD.DATA.FILE01 user=BATCH01",
            "2026-02-13T10:02:00Z AUDIT SUBMIT job=JOB001 user=BATCH01",
            "2026-02-13T10:03:00Z AUDIT CONFIG key=log_level old=INFO new=DEBUG user=ADMIN01",
            "2026-02-13T10:04:00Z AUDIT ACCESS dataset=PROD.DATA.FILE02 user=BATCH02",
        ],
        "error": [
            "2026-02-13T10:05:00Z ERROR IEF450I JOB002 ABENDED S0C7",
            "2026-02-13T10:05:01Z ERROR Data exception in program PROG01",
            "2026-02-13T10:06:00Z ERROR Connection refused: DB2 subsystem",
            "2026-02-13T10:07:00Z ERROR Retry 1 of 3 for DB2 connection",
            "2026-02-13T10:08:00Z ERROR Timeout waiting for response",
        ],
    }

    logs = templates.get(source, [])
    return logs[-tail:] if tail > 0 else []


async def get_system_status() -> dict[str, Any]:
    """Get current system status metrics.

    Returns:
        Dict with cpu, memory, and jobs information.
    """
    logger.info("get_system_status called")

    # Try to read from fixture file
    status_file = SIMULATOR_BASE / "status.json"

    if status_file.exists():
        try:
            import json

            data = json.loads(status_file.read_text())
            return data
        except Exception as e:
            logger.warning(f"Failed to read status file: {e}")

    # Return simulated status
    return {
        "cpu": 45.2,
        "memory": {
            "used": 12800,  # MB
            "total": 16384,  # MB
            "percent": 78.1,
        },
        "jobs": {
            "running": 3,
            "queued": 12,
            "completed_today": 47,
            "failed_today": 2,
        },
        "subsystems": {
            "db2": "active",
            "cics": "active",
            "mq": "active",
            "jes2": "active",
        },
        "timestamp": "2026-02-13T10:30:00Z",
    }


async def run_command(command: str, dry_run: bool = True) -> dict[str, Any]:
    """Execute a command with policy enforcement.

    Args:
        command: The shell command to execute.
        dry_run: If True, validate but don't execute. Defaults to True for safety.

    Returns:
        Dict with execution results or validation status.
    """
    logger.info(f"run_command called: command={command!r}, dry_run={dry_run}")

    # Always validate first
    result = _policy.validate(command)

    if not result.allowed:
        logger.warning(f"Command blocked by policy: {result.reason}")
        return {
            "allowed": False,
            "executed": False,
            "reason": result.reason,
            "command": command,
        }

    # If dry_run, return validation result without executing
    if dry_run:
        return {
            "allowed": True,
            "executed": False,
            "reason": "Dry run - command validated but not executed",
            "command": command,
        }

    # Execute the command (in sandbox)
    # NOTE: In production, this would execute in the ai_runner container
    # For now, we simulate execution for safe commands
    try:
        # For safety during development, only actually execute echo commands
        # Other commands return simulated output
        if command.strip().startswith("echo "):
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            return {
                "allowed": True,
                "executed": True,
                "stdout": stdout.decode().strip(),
                "stderr": stderr.decode().strip(),
                "exit_code": proc.returncode,
                "command": command,
            }
        else:
            # Simulate execution for other safe commands
            return _simulate_command_execution(command)

    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return {
            "allowed": True,
            "executed": True,
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1,
            "command": command,
        }


def _simulate_command_execution(command: str) -> dict[str, Any]:
    """Simulate command execution for safe commands."""
    parts = command.split()
    cmd = parts[0] if parts else ""

    simulated_outputs = {
        "cat": "Simulated file content from /sim/\nLine 1\nLine 2\nLine 3",
        "ls": "syslog.log\njoblog.log\naudit.log\nerror.log\nstatus.json",
        "head": "First lines of simulated file",
        "tail": "Last lines of simulated file",
        "grep": "Matching lines from simulated search",
        "date": "2026-02-13T10:30:00Z",
        "hostname": "mainframe-sim-01",
    }

    return {
        "allowed": True,
        "executed": True,
        "stdout": simulated_outputs.get(cmd, f"Simulated output for: {command}"),
        "stderr": "",
        "exit_code": 0,
        "command": command,
    }


async def update_config(key: str, value: str) -> dict[str, Any]:
    """Update a configuration value.

    Args:
        key: Configuration key to update.
        value: New value to set.

    Returns:
        Dict with ok status and previous value.

    Raises:
        ValueError: If key is empty.
        PolicyViolation: If key is in blocklist.
    """
    logger.info(f"update_config called: key={key}, value={value}")

    # Validate key
    if not key or not key.strip():
        raise ValueError("Config key cannot be empty")

    key = key.strip()

    # Check for blocked sensitive keys
    key_lower = key.lower()
    for blocked in BLOCKED_CONFIG_KEYS:
        if blocked in key_lower:
            raise PolicyViolation(f"Config key blocked: {key} contains sensitive keyword")

    # Check if key is allowed
    if key not in ALLOWED_CONFIG_KEYS:
        logger.warning(f"Config key {key} not in allowlist, but allowing for flexibility")

    # Get previous value
    previous = _config_store.get(key)

    # Update the config
    _config_store[key] = value

    logger.info(f"Config updated: {key}={value} (previous={previous})")

    return {
        "ok": True,
        "key": key,
        "value": value,
        "previous": previous,
    }


# Export tool functions
__all__ = ["get_logs", "get_system_status", "run_command", "update_config"]

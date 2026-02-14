"""Command policy engine for safe command execution.

WP2: Implements strict guardrails for command validation.
- Allowlist of safe commands
- Block dangerous binaries
- Block shell metacharacters
- Path jail to /sim/**
"""

import re
from dataclasses import dataclass
from pathlib import PurePosixPath


class PolicyViolationError(Exception):
    """Raised when a command violates security policy."""

    pass


# Alias for backward compatibility
PolicyViolation = PolicyViolationError


@dataclass
class ValidationResult:
    """Result of command validation."""

    allowed: bool
    reason: str
    command: str


class CommandPolicy:
    """Policy engine for validating commands before execution.

    Enforces:
    - Command allowlist (only safe read-only commands)
    - Dangerous binary blocklist
    - Shell metacharacter blocking
    - Path jail (only /sim/** paths allowed)
    """

    # Commands that are safe for read operations
    ALLOWED_COMMANDS = frozenset(
        {
            "cat",
            "head",
            "tail",
            "grep",
            "ls",
            "echo",
            "wc",
            "sort",
            "uniq",
            "cut",
            "awk",
            "sed",
            "find",
            "stat",
            "file",
            "date",
            "hostname",
            "env",
            "printenv",
        }
    )

    # Dangerous commands that must never be allowed
    BLOCKED_COMMANDS = frozenset(
        {
            # File modification
            "rm",
            "rmdir",
            "mv",
            "cp",
            "touch",
            "mkdir",
            "chmod",
            "chown",
            "chgrp",
            "ln",
            # Network
            "curl",
            "wget",
            "nc",
            "netcat",
            "ncat",
            "telnet",
            "ssh",
            "scp",
            "rsync",
            "ftp",
            "sftp",
            # Shells and interpreters
            "bash",
            "sh",
            "zsh",
            "csh",
            "tcsh",
            "ksh",
            "fish",
            "python",
            "python3",
            "perl",
            "ruby",
            "node",
            "php",
            # Privilege escalation
            "sudo",
            "su",
            "doas",
            "pkexec",
            # System modification
            "kill",
            "killall",
            "pkill",
            "reboot",
            "shutdown",
            "halt",
            "poweroff",
            "init",
            "systemctl",
            "service",
            # Package management
            "apt",
            "apt-get",
            "yum",
            "dnf",
            "rpm",
            "pip",
            "npm",
            # Other dangerous
            "dd",
            "mkfs",
            "fdisk",
            "mount",
            "umount",
            "chroot",
            "nohup",
            "eval",
            "exec",
            "xargs",
        }
    )

    # Shell metacharacters that enable command injection
    METACHARACTER_PATTERNS = [
        (r";", "semicolon"),
        (r"\|", "pipe"),
        (r"&", "ampersand"),
        (r"`", "backtick"),
        (r"\$\(", "command substitution"),
        (r"\$\{", "variable expansion"),
        (r">", "redirect output"),
        (r"<", "redirect input"),
        (r"\n", "newline"),
        (r"\x00", "null byte"),
    ]

    # Path jail - only these prefixes are allowed
    ALLOWED_PATH_PREFIXES = ("/sim/", "/sim")

    def validate(self, command: str) -> ValidationResult:
        """Validate a command against security policy.

        Args:
            command: The shell command to validate.

        Returns:
            ValidationResult with allowed status and reason.
        """
        # Check empty/whitespace
        if not command or not command.strip():
            return ValidationResult(
                allowed=False, reason="Empty command not allowed", command=command
            )

        command = command.strip()

        # Check for metacharacters first (highest priority)
        for pattern, name in self.METACHARACTER_PATTERNS:
            if re.search(pattern, command):
                return ValidationResult(
                    allowed=False,
                    reason=f"Metacharacter blocked: {name}",
                    command=command,
                )

        # Parse the command
        parts = command.split()
        if not parts:
            return ValidationResult(
                allowed=False, reason="Empty command not allowed", command=command
            )

        base_command = parts[0]

        # Extract just the binary name if it's a path
        if "/" in base_command:
            base_command = PurePosixPath(base_command).name

        # Check against blocklist first (explicit deny)
        if base_command in self.BLOCKED_COMMANDS:
            return ValidationResult(
                allowed=False,
                reason=f"Command blocked: {base_command} is not allowed",
                command=command,
            )

        # Check against allowlist (explicit allow)
        if base_command not in self.ALLOWED_COMMANDS:
            return ValidationResult(
                allowed=False,
                reason=f"Command blocked: {base_command} is not in allowlist",
                command=command,
            )

        # Check all path arguments
        for part in parts[1:]:
            # Skip flags
            if part.startswith("-"):
                continue

            # Check if it looks like a path
            if ("/" in part or part.startswith(".")) and not self._is_path_allowed(part):
                return ValidationResult(
                    allowed=False,
                    reason=f"Path not allowed: {part} is outside /sim/",
                    command=command,
                )

        return ValidationResult(allowed=True, reason="Command passed all checks", command=command)

    def _is_path_allowed(self, path: str) -> bool:
        """Check if a path is within the allowed jail.

        Args:
            path: The path to check.

        Returns:
            True if path is within /sim/, False otherwise.
        """
        # Check for path traversal attempts
        if ".." in path:
            return False

        # Normalize the path
        try:
            normalized = str(PurePosixPath(path))
        except Exception:
            return False

        # Check if it's within allowed prefixes
        for prefix in self.ALLOWED_PATH_PREFIXES:
            # Double-check no traversal after normalization
            if normalized.startswith(prefix) and ".." not in normalized:
                return True

        return False

    def enforce(self, command: str) -> None:
        """Validate command and raise if not allowed.

        Args:
            command: The shell command to validate.

        Raises:
            PolicyViolation: If the command is not allowed.
        """
        result = self.validate(command)
        if not result.allowed:
            raise PolicyViolation(result.reason)

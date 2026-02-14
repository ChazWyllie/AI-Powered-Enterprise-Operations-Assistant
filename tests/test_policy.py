"""Tests for command policy engine.

WP2: Policy must block dangerous commands, metacharacters, and paths outside /sim/.
"""

import pytest

from app.policy import CommandPolicy, PolicyViolation


class TestCommandPolicy:
    """Tests for CommandPolicy validation."""

    @pytest.fixture
    def policy(self):
        """Create a CommandPolicy instance."""
        return CommandPolicy()

    # === Allowlist Tests ===

    def test_allows_cat_command(self, policy):
        """cat command should be allowed."""
        result = policy.validate("cat /sim/syslog.log")
        assert result.allowed is True

    def test_allows_grep_command(self, policy):
        """grep command should be allowed."""
        result = policy.validate("grep ERROR /sim/syslog.log")
        assert result.allowed is True

    def test_allows_head_command(self, policy):
        """head command should be allowed."""
        result = policy.validate("head -n 10 /sim/syslog.log")
        assert result.allowed is True

    def test_allows_tail_command(self, policy):
        """tail command should be allowed."""
        result = policy.validate("tail -n 20 /sim/syslog.log")
        assert result.allowed is True

    def test_allows_ls_command(self, policy):
        """ls command should be allowed."""
        result = policy.validate("ls /sim/")
        assert result.allowed is True

    def test_allows_echo_command(self, policy):
        """echo command should be allowed."""
        result = policy.validate("echo hello")
        assert result.allowed is True

    # === Dangerous Binary Tests ===

    def test_blocks_rm_command(self, policy):
        """rm command should be blocked."""
        result = policy.validate("rm /sim/file.txt")
        assert result.allowed is False
        assert "blocked" in result.reason.lower()

    def test_blocks_chmod_command(self, policy):
        """chmod command should be blocked."""
        result = policy.validate("chmod 777 /sim/file.txt")
        assert result.allowed is False

    def test_blocks_chown_command(self, policy):
        """chown command should be blocked."""
        result = policy.validate("chown root /sim/file.txt")
        assert result.allowed is False

    def test_blocks_curl_command(self, policy):
        """curl command should be blocked (network)."""
        result = policy.validate("curl http://example.com")
        assert result.allowed is False

    def test_blocks_wget_command(self, policy):
        """wget command should be blocked (network)."""
        result = policy.validate("wget http://example.com")
        assert result.allowed is False

    def test_blocks_nc_command(self, policy):
        """nc (netcat) command should be blocked."""
        result = policy.validate("nc -l 8080")
        assert result.allowed is False

    def test_blocks_python_command(self, policy):
        """python command should be blocked (arbitrary code)."""
        result = policy.validate("python -c 'import os; os.system(\"rm -rf /\")'")
        assert result.allowed is False

    def test_blocks_bash_command(self, policy):
        """bash command should be blocked."""
        result = policy.validate("bash -c 'echo pwned'")
        assert result.allowed is False

    def test_blocks_sh_command(self, policy):
        """sh command should be blocked."""
        result = policy.validate("sh -c 'id'")
        assert result.allowed is False

    def test_blocks_sudo_command(self, policy):
        """sudo command should be blocked."""
        result = policy.validate("sudo cat /etc/passwd")
        assert result.allowed is False

    def test_blocks_su_command(self, policy):
        """su command should be blocked."""
        result = policy.validate("su root")
        assert result.allowed is False

    # === Metacharacter Tests ===

    def test_blocks_semicolon_injection(self, policy):
        """Semicolon command chaining should be blocked."""
        result = policy.validate("cat /sim/file.txt; rm -rf /")
        assert result.allowed is False
        assert "metacharacter" in result.reason.lower()

    def test_blocks_pipe_to_dangerous(self, policy):
        """Pipe to dangerous command should be blocked."""
        result = policy.validate("cat /sim/file.txt | bash")
        assert result.allowed is False

    def test_blocks_ampersand_background(self, policy):
        """Background execution with & should be blocked."""
        result = policy.validate("cat /sim/file.txt &")
        assert result.allowed is False

    def test_blocks_double_ampersand(self, policy):
        """&& command chaining should be blocked."""
        result = policy.validate("cat /sim/file.txt && rm -rf /")
        assert result.allowed is False

    def test_blocks_double_pipe(self, policy):
        """|| command chaining should be blocked."""
        result = policy.validate("cat /sim/file.txt || rm -rf /")
        assert result.allowed is False

    def test_blocks_backtick_substitution(self, policy):
        """Backtick command substitution should be blocked."""
        result = policy.validate("cat `whoami`")
        assert result.allowed is False

    def test_blocks_dollar_paren_substitution(self, policy):
        """$() command substitution should be blocked."""
        result = policy.validate("cat $(whoami)")
        assert result.allowed is False

    def test_blocks_redirect_output(self, policy):
        """Output redirection > should be blocked."""
        result = policy.validate("echo pwned > /sim/file.txt")
        assert result.allowed is False

    def test_blocks_redirect_append(self, policy):
        """Output append >> should be blocked."""
        result = policy.validate("echo pwned >> /sim/file.txt")
        assert result.allowed is False

    def test_blocks_redirect_input(self, policy):
        """Input redirection < should be blocked."""
        result = policy.validate("cat < /etc/passwd")
        assert result.allowed is False

    # === Path Jail Tests ===

    def test_blocks_absolute_path_outside_sim(self, policy):
        """Paths outside /sim/ should be blocked."""
        result = policy.validate("cat /etc/passwd")
        assert result.allowed is False
        assert "path" in result.reason.lower()

    def test_blocks_relative_path_escape(self, policy):
        """Relative path escape attempts should be blocked."""
        result = policy.validate("cat /sim/../etc/passwd")
        assert result.allowed is False

    def test_blocks_double_dot_traversal(self, policy):
        """.. directory traversal should be blocked."""
        result = policy.validate("cat /sim/logs/../../etc/passwd")
        assert result.allowed is False

    def test_allows_path_within_sim(self, policy):
        """Paths within /sim/ should be allowed."""
        result = policy.validate("cat /sim/logs/app.log")
        assert result.allowed is True

    def test_allows_sim_subdirectories(self, policy):
        """Subdirectories within /sim/ should be allowed."""
        result = policy.validate("ls /sim/jobs/")
        assert result.allowed is True

    # === Edge Cases ===

    def test_blocks_empty_command(self, policy):
        """Empty command should be blocked."""
        result = policy.validate("")
        assert result.allowed is False

    def test_blocks_whitespace_only(self, policy):
        """Whitespace-only command should be blocked."""
        result = policy.validate("   ")
        assert result.allowed is False

    def test_handles_command_with_flags(self, policy):
        """Commands with valid flags should work."""
        result = policy.validate("tail -n 50 -f /sim/syslog.log")
        assert result.allowed is True

    def test_blocks_null_byte_injection(self, policy):
        """Null byte injection attempts should be blocked."""
        result = policy.validate("cat /sim/file.txt\x00/etc/passwd")
        assert result.allowed is False


class TestPolicyViolation:
    """Tests for PolicyViolation exception."""

    def test_policy_violation_has_message(self):
        """PolicyViolation should have a descriptive message."""
        violation = PolicyViolation("Command blocked: rm not allowed")
        assert "rm" in str(violation)

    def test_policy_violation_is_exception(self):
        """PolicyViolation should be raisable as an exception."""
        with pytest.raises(PolicyViolation):
            raise PolicyViolation("test violation")

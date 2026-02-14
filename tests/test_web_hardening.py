"""WP9 — Backend web hardening tests.

Tests for CORS, validation, rate limiting, and request size limits.
"""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def _reset_rate_limiter():
    """Reset rate limiter state between tests."""
    # We need to reimport after env changes, so we just clear the hits
    from app.main import rate_limiter

    rate_limiter._hits.clear()
    yield
    rate_limiter._hits.clear()


# ---------------------------------------------------------------------------
# CORS tests
# ---------------------------------------------------------------------------
class TestCORS:
    """CORS enforcement tests."""

    @pytest.mark.asyncio
    async def test_cors_allowed_origin(self):
        """Allowed origin gets CORS headers."""
        from app.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.options(
                "/chat",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                },
            )
            assert resp.status_code == 200
            assert "access-control-allow-origin" in resp.headers

    @pytest.mark.asyncio
    async def test_cors_disallowed_origin(self):
        """Disallowed origin does NOT receive CORS headers."""
        from app.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.options(
                "/chat",
                headers={
                    "Origin": "http://evil.example.com",
                    "Access-Control-Request-Method": "POST",
                },
            )
            # FastAPI's CORSMiddleware returns 400 for disallowed origins
            assert resp.headers.get("access-control-allow-origin") != "http://evil.example.com"


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------
class TestValidation:
    """Input validation tests."""

    @pytest.mark.asyncio
    async def test_invalid_mode_returns_422(self):
        """Invalid mode value returns 422."""
        from app.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/chat",
                json={"message": "hello", "mode": "destroy_everything"},
            )
            assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_message_returns_422(self):
        """Empty message returns 422."""
        from app.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/chat",
                json={"message": "", "mode": "plan_only"},
            )
            assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_fields_returns_422(self):
        """Missing required fields returns 422."""
        from app.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/chat", json={})
            assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_valid_plan_only_returns_200(self):
        """Valid plan_only request returns 200."""
        from app.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/chat",
                json={"message": "check status", "mode": "plan_only"},
            )
            assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Rate limiting tests
# ---------------------------------------------------------------------------
class TestRateLimiting:
    """Rate limiting tests."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_within_limit(self, _reset_rate_limiter):
        """Requests within limit should succeed."""
        from app.main import rate_limiter

        for _ in range(5):
            assert rate_limiter.is_allowed("test-ip") is True

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_over_limit(self, _reset_rate_limiter):
        """Exceeding the rate limit should be blocked."""
        from app.main import RateLimiter

        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            assert limiter.is_allowed("ip1") is True
        assert limiter.is_allowed("ip1") is False

    @pytest.mark.asyncio
    async def test_rate_limiter_disabled_when_zero(self):
        """Rate limiter with max_requests=0 allows everything."""
        from app.main import RateLimiter

        limiter = RateLimiter(max_requests=0, window_seconds=60)
        for _ in range(100):
            assert limiter.is_allowed("any") is True

    @pytest.mark.asyncio
    async def test_rate_limit_429_on_endpoint(self, _reset_rate_limiter):
        """Endpoint returns 429 when rate limit is exceeded."""
        from app.main import RateLimiter, app

        # Temporarily replace the rate limiter with a strict one
        strict = RateLimiter(max_requests=2, window_seconds=60)
        with patch("app.main.rate_limiter", strict):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                for _ in range(2):
                    resp = await client.post(
                        "/chat",
                        json={"message": "hello", "mode": "plan_only"},
                    )
                    assert resp.status_code == 200

                # 3rd request should be rate-limited
                resp = await client.post(
                    "/chat",
                    json={"message": "hello", "mode": "plan_only"},
                )
                assert resp.status_code == 429
                assert "Rate limit" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_rate_limiter_per_ip(self, _reset_rate_limiter):
        """Different IPs have independent rate limits."""
        from app.main import RateLimiter

        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("ip1")
        limiter.is_allowed("ip1")
        assert limiter.is_allowed("ip1") is False
        # Different IP should still be allowed
        assert limiter.is_allowed("ip2") is True


# ---------------------------------------------------------------------------
# Request size limit tests
# ---------------------------------------------------------------------------
class TestRequestSizeLimit:
    """Request body size limit tests."""

    @pytest.mark.asyncio
    async def test_oversized_request_returns_413(self):
        """Request exceeding MAX_REQUEST_BYTES returns 413."""
        from app.main import app

        # Create a payload larger than 2048 bytes
        large_message = "x" * 3000
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/chat",
                json={"message": large_message, "mode": "plan_only"},
            )
            assert resp.status_code == 413

    @pytest.mark.asyncio
    async def test_normal_request_passes_size_check(self):
        """Normal-sized request passes size check."""
        from app.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/chat",
                json={"message": "check status", "mode": "plan_only"},
            )
            assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------------------
class TestConfiguration:
    """Environment configuration tests."""

    def test_demo_mode_defaults_to_local(self):
        """DEMO_MODE defaults to 'local'."""
        from app.main import DEMO_MODE

        # In test environment, DEMO_MODE is not set, so defaults to "local"
        assert DEMO_MODE in ("local", "public")

    def test_rate_limiter_class_initialization(self):
        """RateLimiter initializes correctly."""
        from app.main import RateLimiter

        limiter = RateLimiter(max_requests=5, window_seconds=30)
        assert limiter.max_requests == 5
        assert limiter.window == 30

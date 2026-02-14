"""AI-Powered Enterprise Operations Assistant API.

FastAPI application providing:
- /health endpoint for service health checks
- /chat endpoint for AI-powered operations assistance (WP4)
- CORS, rate limiting, request size validation (WP9)
"""

import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from app.orchestrator import AgentOrchestrator, OrchestratorMode

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
DEMO_MODE = os.environ.get("DEMO_MODE", "local")  # "public" or "local"
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")
RATE_LIMIT_RPM = int(os.environ.get("RATE_LIMIT_RPM", "0" if DEMO_MODE == "local" else "10"))
MAX_REQUEST_BYTES = int(os.environ.get("MAX_REQUEST_BYTES", "2048"))


# ---------------------------------------------------------------------------
# Rate limiter (in-memory, per-IP)
# ---------------------------------------------------------------------------
class RateLimiter:
    """Simple in-memory sliding-window rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check whether a request from *key* is within the rate limit."""
        if self.max_requests <= 0:
            return True  # disabled
        now = time.time()
        window_start = now - self.window
        # Prune old hits
        self._hits[key] = [t for t in self._hits[key] if t > window_start]
        if len(self._hits[key]) >= self.max_requests:
            return False
        self._hits[key].append(now)
        return True


rate_limiter = RateLimiter(max_requests=RATE_LIMIT_RPM, window_seconds=60)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str


class ChatMode(str, Enum):
    """Valid chat modes."""

    PLAN_ONLY = "plan_only"
    EXECUTE_SAFE = "execute_safe"


class ChatRequest(BaseModel):
    """Chat request model with validation."""

    message: str = Field(..., min_length=1, description="User message to process")
    mode: ChatMode = Field(..., description="Processing mode: plan_only or execute_safe")

    @field_validator("message")
    @classmethod
    def message_not_whitespace(cls, v: str) -> str:
        """Validate message is not just whitespace."""
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v


class AuditInfo(BaseModel):
    """Audit metadata for response."""

    trace_id: str
    mode: str


class ChatResponse(BaseModel):
    """Chat response model."""

    answer: str
    plan: list[dict[str, Any]]
    actions_taken: list[dict[str, Any]]
    script: str | None = None
    audit: AuditInfo


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager."""
    logger.info(
        f"Starting AI Enterprise Operations Assistant | "
        f"DEMO_MODE={DEMO_MODE} | RATE_LIMIT_RPM={RATE_LIMIT_RPM}"
    )
    yield
    logger.info("Shutting down AI Enterprise Operations Assistant")


app = FastAPI(
    title="AI Enterprise Operations Assistant",
    description="AI-powered assistant for IBM Z / enterprise infrastructure operations",
    version="0.9.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS middleware (WP9)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Initialize orchestrator with LLMStub for deterministic behavior
# Set use_stub=False and provide api_key for production OpenAI usage
orchestrator = AgentOrchestrator(use_stub=True)


# ---------------------------------------------------------------------------
# Middleware: request size limit (WP9)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def limit_request_size(request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
    """Reject requests whose body exceeds MAX_REQUEST_BYTES."""
    if request.method in ("POST", "PUT", "PATCH"):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_BYTES:
            return Response(
                content='{"detail":"Request body too large"}',
                status_code=413,
                media_type="application/json",
            )
    return await call_next(request)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return service health status.

    Returns:
        HealthResponse with status "ok" when service is healthy.
    """
    return HealthResponse(status="ok")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, raw_request: Request) -> ChatResponse:
    """Process a chat message through the AI agent.

    Args:
        request: ChatRequest with message and mode.
        raw_request: Raw HTTP request for IP-based rate limiting.

    Returns:
        ChatResponse with answer, plan, actions_taken, and audit info.

    Raises:
        HTTPException: 400 for policy violations, 422 for validation errors,
                       429 for rate limit exceeded.
    """
    # Rate limiting (WP9)
    client_ip = raw_request.client.host if raw_request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Demo mode gate (WP10): reject execute_safe in public mode
    if DEMO_MODE == "public" and request.mode == ChatMode.EXECUTE_SAFE:
        raise HTTPException(
            status_code=403,
            detail="execute_safe is not available in public demo mode",
        )

    logger.info(f"Processing chat request: mode={request.mode}, message={request.message!r}")

    # Map API mode to orchestrator mode
    mode_map = {
        ChatMode.PLAN_ONLY: OrchestratorMode.PLAN_ONLY,
        ChatMode.EXECUTE_SAFE: OrchestratorMode.EXECUTE_SAFE,
    }
    orchestrator_mode = mode_map[request.mode]

    try:
        # Process through orchestrator
        result = await orchestrator.process(
            message=request.message,
            mode=orchestrator_mode,
        )

        # Build response
        return ChatResponse(
            answer=result.answer,
            plan=result.plan,
            actions_taken=result.actions_taken,
            script=result.generated_script,
            audit=AuditInfo(
                trace_id=result.audit.get("trace_id", ""),
                mode=result.audit.get("mode", request.mode.value),
            ),
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

"""AI-Powered Enterprise Operations Assistant API.

FastAPI application providing:
- /health endpoint for service health checks
- /chat endpoint for AI-powered operations assistance (WP4)
"""

import logging
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.orchestrator import AgentOrchestrator, OrchestratorMode

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


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
    logger.info("Starting AI Enterprise Operations Assistant")
    yield
    logger.info("Shutting down AI Enterprise Operations Assistant")


app = FastAPI(
    title="AI Enterprise Operations Assistant",
    description="AI-powered assistant for IBM Z / enterprise infrastructure operations",
    version="0.4.0",
    lifespan=lifespan,
)

# Initialize orchestrator with LLMStub for deterministic behavior
# Set use_stub=False and provide api_key for production OpenAI usage
orchestrator = AgentOrchestrator(use_stub=True)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return service health status.

    Returns:
        HealthResponse with status "ok" when service is healthy.
    """
    return HealthResponse(status="ok")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message through the AI agent.

    Args:
        request: ChatRequest with message and mode.

    Returns:
        ChatResponse with answer, plan, actions_taken, and audit info.

    Raises:
        HTTPException: 400 for policy violations, 422 for validation errors.
    """
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

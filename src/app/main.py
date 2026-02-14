"""AI-Powered Enterprise Operations Assistant API.

FastAPI application providing:
- /health endpoint for service health checks
- /chat endpoint for AI-powered operations assistance (WP4)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting AI Enterprise Operations Assistant")
    yield
    logger.info("Shutting down AI Enterprise Operations Assistant")


app = FastAPI(
    title="AI Enterprise Operations Assistant",
    description="AI-powered assistant for IBM Z / enterprise infrastructure operations",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return service health status.

    Returns:
        HealthResponse with status "ok" when service is healthy.
    """
    return HealthResponse(status="ok")

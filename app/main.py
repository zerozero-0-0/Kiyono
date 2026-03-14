"""FastAPI application entrypoint for the LLMO content generator."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    app: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")


APP_TITLE = "LLMO Content Generator API"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = (
    "Backend API for generating LLMO-optimized titles and articles for the internship project."
)

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["system"],
)
def health() -> HealthResponse:
    """Return service health and basic application metadata."""
    return HealthResponse(
        status="ok",
        app=APP_TITLE,
        version=APP_VERSION,
    )

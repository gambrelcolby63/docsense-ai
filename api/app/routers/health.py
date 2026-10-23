"""Liveness and which provider the process is actually using."""

from fastapi import APIRouter, Request

from app.database import database_kind
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    provider = request.app.state.provider
    model = settings.openai_model if provider.name == "openai" else None
    return HealthResponse(
        status="ok",
        provider=provider.name,
        embedding_provider=settings.embedding_provider,
        database=database_kind(settings.database_url),
        model=model,
    )

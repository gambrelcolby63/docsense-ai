"""FastAPI application factory.

Uvicorn starts it with `uvicorn app.main:create_app --factory`. Building the
app inside a factory keeps tests from opening a database at import time.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.database import make_engine, make_session_factory
from app.models import Base
from app.routers import documents, health
from app.services.llm import build_provider

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    logging.basicConfig(level=logging.INFO)
    settings = settings or get_settings()
    provider = build_provider(settings)
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(engine)
        logger.info(
            "DocSense API ready provider=%s embeddings=%s",
            provider.name,
            settings.embedding_provider,
        )
        yield
        closer = getattr(provider, "close", None)
        if callable(closer):
            closer()
        engine.dispose()

    app = FastAPI(
        title="DocSense AI",
        version="1.0.0",
        summary="Upload a PDF or image, summarize it, and ask questions with cited passages.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.provider = provider
    app.state.engine = engine
    app.state.session_factory = session_factory

    origins = settings.cors_origin_list or ["http://localhost:3000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if origins == ["*"] else origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")

    @app.get("/", tags=["health"])
    def root() -> dict[str, str]:
        return {"name": "DocSense AI", "health": "/api/health", "docs": "/docs"}

    return app

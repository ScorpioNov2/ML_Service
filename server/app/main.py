"""
FastAPI application factory.

Starting point
──────────────
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    API_PREFIX,
    API_TITLE,
    API_VERSION,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_ORIGINS,
)
from app.routers.prediction_router import router as prediction_router


def create_app() -> FastAPI:
    """Application factory — makes the app testable without side effects."""

    application = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ───────────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOW_ORIGINS,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )

    # ── Routers ────────────────────────────────────────────────────────────────
    application.include_router(prediction_router, prefix=API_PREFIX)

    # ── Health-check (no business logic, pure infrastructure) ─────────────────
    @application.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": API_VERSION}

    return application


app = create_app()

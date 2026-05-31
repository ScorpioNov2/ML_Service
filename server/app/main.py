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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    """Фабрика приложения — упрощает тестирование без побочных эффектов."""

    application = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    application.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOW_ORIGINS,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )

    # ── Роутеры ───────────────────────────────────────────────────────────────
    application.include_router(prediction_router, prefix=API_PREFIX)

    # ── Проверка работоспособности (только инфраструктура, без бизнес-логики) ─
    @application.get("/health", tags=["Система"])
    async def health() -> dict[str, str]:
        """Проверить, что сервер запущен и готов к работе."""
        return {"status": "ok", "version": API_VERSION}

    return application


app = create_app()
# uvicorn app.main:app --reload

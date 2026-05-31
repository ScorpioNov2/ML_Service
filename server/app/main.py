"""
Модуль создания приложения FastAPI.

Настраивает CORS, включает роутеры, добавляет эндпоинт /health.
Инициализирует логирование.
"""

import logging

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

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mortgage-api")


def create_app() -> FastAPI:
    """Создаёт и настраивает экземпляр FastAPI."""

    application = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    logger.info("Starting Mortgage Prediction API")

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOW_ORIGINS,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )
    logger.debug("CORS middleware configured")

    # Роутеры
    application.include_router(prediction_router, prefix=API_PREFIX)
    logger.debug(f"Router included with prefix {API_PREFIX}")

    # Эндпоинт для проверки работоспособности
    @application.get("/health", tags=["Система"])
    async def health() -> dict[str, str]:
        """Проверяет, что сервер запущен и готов к работе."""
        return {"status": "ok", "version": API_VERSION}

    logger.info("Application setup complete")
    return application


app = create_app()

"""
Pydantic-схемы для запросов и ответов.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Optional

from pydantic import BaseModel


class AppStatusCode(IntEnum):
    """Коды статуса приложения (отделены от HTTP)."""

    SUCCESS = 200
    BAD_REQUEST = 400
    NOT_FOUND = 404
    UNPROCESSABLE = 422
    SERVER_ERROR = 500


class PredictionResponse(BaseModel):
    """Единый формат ответа для всех эндпоинтов."""

    status_code: int
    message: str
    data: Optional[Any] = None

    @classmethod
    def ok(cls, message: str, data: Any = None) -> "PredictionResponse":
        """Успешный ответ (200)."""
        return cls(status_code=AppStatusCode.SUCCESS, message=message, data=data)

    @classmethod
    def bad_request(cls, message: str) -> "PredictionResponse":
        """Ошибка запроса (400)."""
        return cls(status_code=AppStatusCode.BAD_REQUEST, message=message)

    @classmethod
    def not_found(cls, message: str) -> "PredictionResponse":
        """Ресурс не найден (404)."""
        return cls(status_code=AppStatusCode.NOT_FOUND, message=message)

    @classmethod
    def unprocessable(cls, message: str) -> "PredictionResponse":
        """Ошибка валидации данных (422)."""
        return cls(status_code=AppStatusCode.UNPROCESSABLE, message=message)

    @classmethod
    def server_error(cls, message: str) -> "PredictionResponse":
        """Внутренняя ошибка сервера (500)."""
        return cls(status_code=AppStatusCode.SERVER_ERROR, message=message)

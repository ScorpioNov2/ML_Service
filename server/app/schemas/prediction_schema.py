"""
Pydantic schemas — single source of truth for all request / response shapes.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Any, Optional

from pydantic import BaseModel


class AppStatusCode(IntEnum):
    """
    Application-level status codes kept separate from HTTP status codes so the
    HTTP layer and the business layer can evolve independently.
    """
    SUCCESS = 200
    BAD_REQUEST = 400
    NOT_FOUND = 404
    UNPROCESSABLE = 422
    SERVER_ERROR = 500


class PredictionResponse(BaseModel):
    """Unified envelope returned by every prediction endpoint."""

    status_code: int
    message: str
    data: Optional[Any] = None

    @classmethod
    def ok(cls, message: str, data: Any = None) -> "PredictionResponse":
        return cls(
            status_code=AppStatusCode.SUCCESS,
            message=message,
            data=data,
        )

    @classmethod
    def bad_request(cls, message: str) -> "PredictionResponse":
        return cls(
            status_code=AppStatusCode.BAD_REQUEST,
            message=message,
            data=None,
        )

    @classmethod
    def not_found(cls, message: str) -> "PredictionResponse":
        return cls(
            status_code=AppStatusCode.NOT_FOUND,
            message=message,
            data=None,
        )

    @classmethod
    def server_error(cls, message: str) -> "PredictionResponse":
        return cls(
            status_code=AppStatusCode.SERVER_ERROR,
            message=message,
            data=None,
        )

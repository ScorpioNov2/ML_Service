"""
PredictionController
────────────────────
Orchestrates the three services (Model → Data → Prediction) and maps
business results to HTTP responses.

This class is the only place that knows about both the HTTP layer and the
business layer, keeping services clean and independently testable.
"""

from __future__ import annotations

import io
from typing import Any, Optional

import pandas as pd
from fastapi import UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import (
    MSG_DEFAULT_MODEL_NOT_FOUND,
    MSG_NO_DATA,
    MSG_PREDICTION_SUCCESS,
    MSG_UNSUPPORTED_DATA_FILE,
    MSG_UNSUPPORTED_MODEL_FILE,
    OUTPUT_CSV_FILENAME,
)
from app.schemas.prediction_schema import AppStatusCode, PredictionResponse
from app.services.data_service import DataService
from app.services.model_service import ModelService
from app.services.prediction_service import PredictionService


class PredictionController:
    """
    Coordinates model loading, data ingestion, and prediction; returns
    appropriate HTTP responses for every outcome.
    """

    def __init__(
        self,
        model_service: ModelService,
        data_service: DataService,
        prediction_service: PredictionService,
    ) -> None:
        self._model_svc = model_service
        self._data_svc = data_service
        self._pred_svc = prediction_service

    # ── Main entry point ───────────────────────────────────────────────────────

    async def handle_prediction(
        self,
        model_file: Optional[UploadFile],
        data_file: Optional[UploadFile],
        form_data: Optional[list[dict[str, Any]]],
    ) -> Any:
        """
        Full pipeline:
          1. Validate & load model.
          2. Validate & parse input data.
          3. Run prediction.
          4. Return CSV streaming response.
        """

        # ── Step 1: resolve model ──────────────────────────────────────────────
        model_result = await self._resolve_model(model_file)
        if isinstance(model_result, JSONResponse):
            return model_result          # early-exit on error
        model = model_result

        # ── Step 2: resolve data ───────────────────────────────────────────────
        data_result = await self._resolve_data(data_file, form_data)
        if isinstance(data_result, JSONResponse):
            return data_result           # early-exit on error
        df: pd.DataFrame = data_result

        # ── Step 3: predict ────────────────────────────────────────────────────
        try:
            result_df = self._pred_svc.predict(model, df)
        except ValueError as exc:
            return self._json_error(AppStatusCode.SERVER_ERROR, str(exc))

        # ── Step 4: stream CSV back to client ──────────────────────────────────
        csv_bytes = self._data_svc.dataframe_to_csv_bytes(result_df)
        return StreamingResponse(
            content=io.BytesIO(csv_bytes),
            status_code=AppStatusCode.SUCCESS,
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{OUTPUT_CSV_FILENAME}"'
                ),
                "X-Status-Code": str(AppStatusCode.SUCCESS),
                "X-Message": MSG_PREDICTION_SUCCESS,
            },
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    async def _resolve_model(
        self, model_file: Optional[UploadFile]
    ) -> Any:
        """Return a loaded model or a JSONResponse error."""

        if model_file is not None:
            # Validate extension
            if not self._model_svc.is_supported(model_file.filename or ""):
                return self._json_error(
                    AppStatusCode.BAD_REQUEST,
                    MSG_UNSUPPORTED_MODEL_FILE.format(
                        extensions=self._model_svc.supported_extensions_display()
                    ),
                )
            # Load uploaded model
            try:
                raw = await model_file.read()
                return self._model_svc.load_from_bytes(
                    model_file.filename or "model.pkl", raw
                )
            except ValueError as exc:
                return self._json_error(AppStatusCode.SERVER_ERROR, str(exc))

        # No model file → fall back to default
        try:
            return self._model_svc.load_default()
        except FileNotFoundError as exc:
            return self._json_error(AppStatusCode.NOT_FOUND, str(exc))
        except ValueError as exc:
            return self._json_error(AppStatusCode.SERVER_ERROR, str(exc))

    async def _resolve_data(
        self,
        data_file: Optional[UploadFile],
        form_data: Optional[list[dict[str, Any]]],
    ) -> Any:
        """Return a DataFrame or a JSONResponse error."""

        # Priority: CSV file > form data
        if data_file is not None:
            if not self._data_svc.is_supported_file(data_file.filename or ""):
                return self._json_error(
                    AppStatusCode.BAD_REQUEST,
                    MSG_UNSUPPORTED_DATA_FILE.format(
                        extensions=self._data_svc.supported_extensions_display()
                    ),
                )
            try:
                raw = await data_file.read()
                return self._data_svc.read_csv_bytes(raw)
            except ValueError as exc:
                return self._json_error(AppStatusCode.UNPROCESSABLE, str(exc))

        if form_data:
            try:
                return self._data_svc.read_form_data(form_data)
            except ValueError as exc:
                return self._json_error(AppStatusCode.UNPROCESSABLE, str(exc))

        # Nothing provided
        return self._json_error(AppStatusCode.BAD_REQUEST, MSG_NO_DATA)

    @staticmethod
    def _json_error(status_code: int, message: str) -> JSONResponse:
        payload = PredictionResponse(
            status_code=status_code, message=message, data=None
        )
        return JSONResponse(
            status_code=status_code,
            content=payload.model_dump(),
        )

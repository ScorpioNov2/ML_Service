from __future__ import annotations

from typing import Any, Optional

import pandas as pd
from app.config import (
    MSG_AMBIGUOUS_DATA_SOURCE,
    MSG_NO_DATA,
    MSG_PREDICTION_SUCCESS,
    MSG_UNSUPPORTED_DATA_FILE,
    MSG_UNSUPPORTED_MODEL_FILE,
)
from app.schemas.prediction_schema import AppStatusCode, PredictionResponse
from app.services.data_service import DataService
from app.services.model_service import ModelService
from app.services.prediction_service import PredictionService
from app.services.validation_service import DataValidationService
from fastapi import UploadFile
from fastapi.responses import JSONResponse


class PredictionController:
    """
    Связывает HTTP-слой с бизнес-сервисами.
    Три публичных обработчика — по одному на каждый эндпоинт.
    """

    def __init__(
        self,
        model_service: ModelService,
        data_service: DataService,
        prediction_service: PredictionService,
        validation_service: DataValidationService,
    ) -> None:
        self._model_svc = model_service
        self._data_svc = data_service
        self._pred_svc = prediction_service
        self._validation_svc = validation_service

    async def handle_form(
        self,
        form_data: list[dict[str, Any]],
    ) -> JSONResponse:
        """
        /predict/form
        Входные данные  : JSON-массив строк.
        Модель          : Модель по умолчанию с сервера.
        """
        model = self._load_default_model()
        if isinstance(model, JSONResponse):
            return model

        # [2] Разобрать данные формы
        try:
            df = self._data_svc.read_form_data(form_data)
        except ValueError as exc:
            return self._error(AppStatusCode.UNPROCESSABLE, str(exc))

        return self._run_pipeline(model, df)

    async def handle_csv(
        self,
        data_file: UploadFile,
    ) -> JSONResponse:
        """
        /predict/csv
        Входные данные  : CSV-файл.
        Модель          : Модель по умолчанию с сервера.
        """
        model = self._load_default_model()
        if isinstance(model, JSONResponse):
            return model

        # [2] Разобрать CSV-файл
        data_result = await self._parse_csv(data_file)
        if isinstance(data_result, JSONResponse):
            return data_result

        return self._run_pipeline(model, data_result)

    async def handle_custom(
        self,
        model_file: UploadFile,
        data_file: Optional[UploadFile] = None,
        form_data: Optional[list[dict[str, Any]]] = None,
    ) -> JSONResponse:
        """
        /predict/custom
        Входные данные  : CSV-файл ИЛИ JSON-форма (CSV имеет приоритет).
        Модель          : Обязательный загружаемый .pkl-файл.
        """
        # [1] Загрузить пользовательскую модель (обязательно)
        if not self._model_svc.is_supported(model_file.filename or ""):
            return self._error(
                AppStatusCode.BAD_REQUEST,
                MSG_UNSUPPORTED_MODEL_FILE.format(extensions=self._model_svc.show_supported_extensions()),
            )
        try:
            raw = await model_file.read()
            model = self._model_svc.load_from_bytes(model_file.filename or "model.pkl", raw)
        except ValueError as exc:
            return self._error(AppStatusCode.SERVER_ERROR, str(exc))

        # [2] Данные: пользователь использует одновременно form and csv
        if data_file is not None and form_data:
            return self._error(
                AppStatusCode.BAD_REQUEST,
                MSG_AMBIGUOUS_DATA_SOURCE,
            )
        if data_file is not None:
            data_result = await self._parse_csv(data_file)
            if isinstance(data_result, JSONResponse):
                return data_result
            df = data_result
        elif form_data:
            try:
                df = self._data_svc.read_form_data(form_data)
            except ValueError as exc:
                return self._error(AppStatusCode.UNPROCESSABLE, str(exc))
        else:
            return self._error(AppStatusCode.BAD_REQUEST, MSG_NO_DATA)

        return self._run_pipeline(model, df)

    # Общий pipeline: валидация → предсказание → JSON-ответ
    def _run_pipeline(self, model: Any, df: pd.DataFrame) -> JSONResponse:
        """
        [3] Валидация схемы данных
        [4] Предсказание
        [5] Формирование JSON-ответа
        """
        # [3] Валидация
        validation = self._validation_svc.validate(df)
        if not validation.is_valid:
            return self._error(AppStatusCode.UNPROCESSABLE, validation.summary())

        # [4] Предсказание
        try:
            result_df = self._pred_svc.predict(model, df)
        except ValueError as exc:
            return self._error(AppStatusCode.SERVER_ERROR, str(exc))

        # [5] JSON-ответ: список словарей
        records = self._data_svc.dataframe_to_records(result_df)
        payload = PredictionResponse.ok(
            message=MSG_PREDICTION_SUCCESS.format(count=len(records)),
            data=records,
        )
        return JSONResponse(
            status_code=AppStatusCode.SUCCESS,
            content=payload.model_dump(),
        )

    # Приватные вспомогательные методы
    def _load_default_model(self) -> Any:
        """Загрузить модель по умолчанию. Вернуть объект или JSONResponse с ошибкой."""
        try:
            return self._model_svc.load_default()
        except FileNotFoundError as exc:
            return self._error(AppStatusCode.NOT_FOUND, str(exc))
        except ValueError as exc:
            return self._error(AppStatusCode.SERVER_ERROR, str(exc))

    async def _parse_csv(self, data_file: UploadFile) -> pd.DataFrame | JSONResponse:
        """Проверить расширение и разобрать CSV в DataFrame. Вернуть DataFrame или ошибку."""
        if not self._data_svc.is_supported_file(data_file.filename or ""):
            return self._error(
                AppStatusCode.BAD_REQUEST,
                MSG_UNSUPPORTED_DATA_FILE.format(extensions=self._data_svc.show_supported_extensions()),
            )
        try:
            raw = await data_file.read()
            return self._data_svc.read_csv_bytes(raw)
        except ValueError as exc:
            return self._error(AppStatusCode.UNPROCESSABLE, str(exc))

    @staticmethod
    def _error(status_code: int, message: str) -> JSONResponse:
        """Сформировать JSONResponse с описанием ошибки."""
        payload = PredictionResponse(status_code=status_code, message=message, data=None)
        return JSONResponse(
            status_code=status_code,
            content=payload.model_dump(),
        )

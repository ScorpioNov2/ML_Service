from __future__ import annotations

import json
from typing import Any, Optional

from app.controllers.prediction_controller import PredictionController
from app.schemas.prediction_schema import AppStatusCode, PredictionResponse
from app.services.data_service import DataService
from app.services.model_service import ModelService
from app.services.prediction_service import PredictionService
from app.services.validation_service import DataValidationService
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/predict", tags=["Предсказание"])

# ── Ручное внедрение зависимостей ─────────────────────────────────────────────
_controller = PredictionController(
    model_service=ModelService(),
    data_service=DataService(),
    prediction_service=PredictionService(),
    validation_service=DataValidationService(),
)


def _decode_form_data(raw: str) -> tuple[list[dict], None] | tuple[None, JSONResponse]:
    """
    Декодировать строку form_data из JSON в список Python.
    Возвращает (данные, None) при успехе или (None, JSONResponse) при ошибке.
    """
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            raise TypeError(f"Ожидается JSON-массив, получен: {type(parsed).__name__}")
        return parsed, None
    except (json.JSONDecodeError, TypeError) as exc:
        err = PredictionResponse.bad_request(f"Некорректный form_data: {exc}")
        return None, JSONResponse(
            status_code=AppStatusCode.BAD_REQUEST,
            content=err.model_dump(),
        )


#   POST /predict/form    — данные из JSON-формы,  модель по умолчанию (без загрузки)
@router.post(
    "/form",
    summary="Предсказание по полям формы (модель по умолчанию)",
    description=(
        "Принимает данные в виде **JSON-массива строк**. "
        "Всегда использует модель по умолчанию (`./models/model.pkl`). "
        "Возвращает JSON-массив с добавленным полем `predicted`."
    ),
    response_model=PredictionResponse,
    responses={
        400: {"model": PredictionResponse, "description": "Некорректный запрос"},
        404: {"model": PredictionResponse, "description": "Модель по умолчанию не найдена"},
        422: {"model": PredictionResponse, "description": "Ошибка валидации данных"},
        500: {"model": PredictionResponse, "description": "Внутренняя ошибка сервера"},
    },
)
async def predict_form(
    form_data: str = Form(
        ...,
        description=("JSON-массив объектов-строк. Пример: " '[{"person_age": 35.0, "person_gender": "male", ...}]'),
    ),
) -> Any:
    parsed, err = _decode_form_data(form_data)
    if err:
        return err
    return await _controller.handle_form(form_data=parsed)


#     /predict/csv     — данные из CSV-файла,   модель по умолчанию (без загрузки)
@router.post(
    "/csv",
    summary="Предсказание по CSV-файлу (модель по умолчанию)",
    description=(
        "Принимает данные в виде **CSV-файла**. "
        "Всегда использует модель по умолчанию (`./models/model.pkl`). "
        "Возвращает JSON-массив с добавленным полем `predicted`."
    ),
    response_model=PredictionResponse,
    responses={
        400: {"model": PredictionResponse, "description": "Некорректный запрос"},
        404: {"model": PredictionResponse, "description": "Модель по умолчанию не найдена"},
        422: {"model": PredictionResponse, "description": "Ошибка валидации данных"},
        500: {"model": PredictionResponse, "description": "Внутренняя ошибка сервера"},
    },
)
async def predict_csv(
    data_file: UploadFile = File(
        ...,
        description="CSV-файл с колонками согласно схеме данных (DATA_SCHEMA).",
    ),
) -> Any:
    return await _controller.handle_csv(data_file=data_file)


#   /predict/custom  — данные из формы ИЛИ CSV, обязательная загрузка .pkl-модели
@router.post(
    "/custom",
    summary="Предсказание с пользовательской моделью",
    description=(
        "Принимает **обязательный файл модели `.pkl`** и данные. "
        "Данные можно передать в виде CSV-файла ИЛИ JSON-массива "
        "(при передаче обоих — CSV имеет приоритет). "
        "Возвращает JSON-массив с добавленным полем `predicted`."
    ),
    response_model=PredictionResponse,
    responses={
        400: {"model": PredictionResponse, "description": "Некорректный запрос или формат файла"},
        422: {"model": PredictionResponse, "description": "Ошибка валидации данных"},
        500: {"model": PredictionResponse, "description": "Внутренняя ошибка сервера"},
    },
)
async def predict_custom(
    model_file: UploadFile = File(
        ...,
        description="Обязательный файл модели (.pkl).",
    ),
    data_file: Optional[UploadFile] = File(
        None,
        description="CSV-файл с данными (имеет приоритет над form_data).",
    ),
    form_data: Optional[str] = Form(
        None,
        description=("JSON-массив объектов-строк. Пример: " '[{"person_age": 35.0, "person_gender": "male", ...}]'),
    ),
) -> Any:
    parsed_form: Optional[list[dict]] = None
    if form_data:
        parsed_form, err = _decode_form_data(form_data)
        if err:
            return err

    return await _controller.handle_custom(
        model_file=model_file,
        data_file=data_file,
        form_data=parsed_form,
    )

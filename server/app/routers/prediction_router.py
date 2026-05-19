"""
Prediction router — HTTP boundary only.

Responsibilities
────────────────
* Declare endpoints and their parameter types.
* Decode the raw `form_data` JSON string into a Python list.
* Delegate all business logic to PredictionController.

Nothing else lives here.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from app.controllers.prediction_controller import PredictionController
from app.schemas.prediction_schema import AppStatusCode, PredictionResponse
from app.services.data_service import DataService
from app.services.model_service import ModelService
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predict", tags=["Prediction"])

# ── Dependency wiring (simple manual DI; replace with FastAPI Depends if
#    you later add async DB sessions, caches, etc.) ───────────────────────────
_controller = PredictionController(
    model_service=ModelService(),
    data_service=DataService(),
    prediction_service=PredictionService(),
)


@router.post(
    "",
    summary="Run ML prediction",
    description=(
        "Upload an optional `.pkl` model and either a `.csv` file or a JSON "
        "list of form-field rows.  Returns a CSV with a `predicted` column "
        "appended, or a JSON error envelope."
    ),
    responses={
        200: {"description": "CSV file with predictions", "content": {"text/csv": {}}},
        400: {"model": PredictionResponse},
        404: {"model": PredictionResponse},
        422: {"model": PredictionResponse},
        500: {"model": PredictionResponse},
    },
)
async def predict(
    model_file: Optional[UploadFile] = File(
        None,
        description="Model file (.pkl). Leave empty to use the backend default.",
    ),
    data_file: Optional[UploadFile] = File(
        None,
        description="Data file (.csv). Takes priority over form_data.",
    ),
    form_data: Optional[str] = Form(
        None,
        description=(
            'JSON-encoded list of row objects, e.g. '
            '[{"col1": 1, "col2": 2}, {"col1": 3, "col2": 4}]'
        ),
    ),
) -> Any:
    parsed_form: Optional[list[dict[str, Any]]] = None

    if form_data:
        try:
            parsed_form = json.loads(form_data)
            if not isinstance(parsed_form, list):
                raise TypeError("form_data must be a JSON array.")
        except (json.JSONDecodeError, TypeError) as exc:
            payload = PredictionResponse.bad_request(
                f"form_data is not valid: {exc}"
            )
            return JSONResponse(
                status_code=AppStatusCode.BAD_REQUEST,
                content=payload.model_dump(),
            )

    return await _controller.handle_prediction(
        model_file=model_file,
        data_file=data_file,
        form_data=parsed_form,
    )

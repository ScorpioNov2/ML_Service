"""
PredictionService — Single Responsibility: run the model and attach results.

It knows nothing about HTTP, file formats, or model serialisation; it just
calls model.predict() and appends the output column.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.config import MSG_PREDICTION_ERROR, PREDICTED_COLUMN_NAME


class PredictionService:
    """Run inference and return an enriched DataFrame."""

    def predict(self, model: Any, df: pd.DataFrame) -> pd.DataFrame:
        """
        Call *model*.predict(df), append predictions as a new column, and
        return the enriched copy.

        Raises
        ------
        ValueError
            When the underlying model raises any exception.
        """
        try:
            predictions = model.predict(df)
        except Exception as exc:
            raise ValueError(
                MSG_PREDICTION_ERROR.format(detail=str(exc))
            ) from exc

        result = df.copy()
        result[PREDICTED_COLUMN_NAME] = predictions
        return result

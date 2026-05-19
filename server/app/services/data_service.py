"""
Data reading layer.

Design decisions
────────────────
* DataReader     — abstract base (DIP / ISP)
* CSVDataReader  — reads bytes → DataFrame
* FormDataReader — reads List[dict] → DataFrame
* DataService    — façade that hides reader selection from callers

To add a new data source (Excel, Parquet, …):
  1. Create a new DataReader subclass.
  2. Add an entry to DataService._reader_registry.
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from app.config import MSG_DATA_PARSE_ERROR, SUPPORTED_DATA_EXTENSIONS
from app.utils.file_validator import FileValidator


# ── Abstract reader ────────────────────────────────────────────────────────────

class DataReader(ABC):
    """Parse an arbitrary source into a pandas DataFrame."""

    @abstractmethod
    def read(self, source: Any) -> pd.DataFrame:
        """Convert *source* into a DataFrame."""


# ── Concrete readers ───────────────────────────────────────────────────────────

class CSVDataReader(DataReader):
    """Read raw CSV bytes into a DataFrame."""

    def read(self, source: bytes) -> pd.DataFrame:  # noqa: D102
        try:
            return pd.read_csv(io.BytesIO(source))
        except Exception as exc:
            raise ValueError(
                MSG_DATA_PARSE_ERROR.format(detail=str(exc))
            ) from exc


class FormDataReader(DataReader):
    """Convert a list of dicts (form fields) into a DataFrame."""

    def read(self, source: list[dict[str, Any]]) -> pd.DataFrame:  # noqa: D102
        try:
            return pd.DataFrame(source)
        except Exception as exc:
            raise ValueError(
                MSG_DATA_PARSE_ERROR.format(detail=str(exc))
            ) from exc


# ── Service ────────────────────────────────────────────────────────────────────

class DataService:
    """
    Façade that selects the correct DataReader and exposes a uniform API.
    """

    def __init__(self) -> None:
        self._csv_reader = CSVDataReader()
        self._form_reader = FormDataReader()
        self._csv_validator = FileValidator(SUPPORTED_DATA_EXTENSIONS)

    # ── Public API ─────────────────────────────────────────────────────────────

    def is_supported_file(self, filename: str) -> bool:
        return self._csv_validator.is_supported(filename)

    def supported_extensions_display(self) -> str:
        return self._csv_validator.extensions_display()

    def read_csv_bytes(self, csv_bytes: bytes) -> pd.DataFrame:
        """Parse uploaded CSV bytes."""
        return self._csv_reader.read(csv_bytes)

    def read_form_data(self, rows: list[dict[str, Any]]) -> pd.DataFrame:
        """Build a DataFrame from JSON form rows."""
        return self._form_reader.read(rows)

    @staticmethod
    def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
        """Serialise a DataFrame to CSV bytes (UTF-8, no BOM)."""
        return df.to_csv(index=False).encode("utf-8")

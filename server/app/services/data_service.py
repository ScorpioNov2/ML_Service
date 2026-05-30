"""
* DataReader      — абстрактный базовый класс (DIP / ISP)
* CSVDataReader   — читает байты CSV → DataFrame
* FormDataReader  — преобразует List[dict] → DataFrame
* DataService     — фасад, скрывающий выбор читателя от вызывающего кода

Добавление нового источника данных (Excel, Parquet и т.д.):
  1. Создать новый подкласс DataReader.
  2. Добавить соответствующий метод в DataService.
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from app.config import MSG_DATA_PARSE_ERROR, SUPPORTED_DATA_EXTENSIONS
from app.utils.file_validator import FileValidator


# ── Абстрактный читатель ──────────────────────────────────────────────────────

class DataReader(ABC):
    """Преобразует произвольный источник данных в pandas DataFrame."""

    @abstractmethod
    def read(self, source: Any) -> pd.DataFrame:
        """Конвертировать source в DataFrame."""


# ── Конкретные читатели ───────────────────────────────────────────────────────

class CSVDataReader(DataReader):
    """Читает сырые байты CSV в DataFrame."""

    def read(self, source: bytes) -> pd.DataFrame:
        try:
            return pd.read_csv(io.BytesIO(source))
        except Exception as exc:
            raise ValueError(MSG_DATA_PARSE_ERROR.format(detail=str(exc))) from exc


class FormDataReader(DataReader):
    """Преобразует список словарей (поля формы) в DataFrame."""

    def read(self, source: list[dict[str, Any]]) -> pd.DataFrame:
        try:
            return pd.DataFrame(source)
        except Exception as exc:
            raise ValueError(MSG_DATA_PARSE_ERROR.format(detail=str(exc))) from exc


# ── Сервис ────────────────────────────────────────────────────────────────────

class DataService:
    """
    Фасад: выбирает правильный DataReader и предоставляет единый API.
    """

    def __init__(self) -> None:
        self._csv_reader   = CSVDataReader()
        self._form_reader  = FormDataReader()
        self._csv_validator = FileValidator(SUPPORTED_DATA_EXTENSIONS)

    # ── Публичный интерфейс ───────────────────────────────────────────────────

    def is_supported_file(self, filename: str) -> bool:
        """Проверить, поддерживается ли расширение файла данных."""
        return self._csv_validator.is_supported(filename)

    def show_supported_extensions(self) -> str:
        """Вернуть строку допустимых расширений для вывода пользователю."""
        return self._csv_validator.show_supported_extensions()

    def read_csv_bytes(self, csv_bytes: bytes) -> pd.DataFrame:
        """Разобрать загруженные байты CSV."""
        return self._csv_reader.read(csv_bytes)

    def read_form_data(self, rows: list[dict[str, Any]]) -> pd.DataFrame:
        """Построить DataFrame из JSON-строк формы."""
        return self._form_reader.read(rows)

    @staticmethod
    def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
        """Сериализовать DataFrame в список словарей для JSON-ответа."""
        return df.to_dict(orient="records")

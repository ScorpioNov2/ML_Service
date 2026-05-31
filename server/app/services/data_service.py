"""
Сервис для чтения данных из различных источников.

Реализованы:
    - чтение из CSV-файла (байты - DataFrame)
    - чтение из JSON-формы (список словарей - DataFrame)

Добавление нового источника данных (Excel и т.д.):
  1. Создать новый подкласс DataReader.
  2. Добавить соответствующий метод в DataService.
"""

from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from app.config import MSG_DATA_PARSE_ERROR, SUPPORTED_DATA_EXTENSIONS
from app.utils.file_validator import FileValidator

# Настройка логгера
logger = logging.getLogger(__name__)


# Абстрактный читатель


class DataReader(ABC):
    """Абстрактный базовый класс для всех читателей данных."""

    @abstractmethod
    def read(self, source: Any) -> pd.DataFrame:
        """Преобразование источника данных в pandas DataFrame."""


# Конкретные читатели


class CSVDataReader(DataReader):
    """Чтение CSV из байтов."""

    def read(self, source: bytes) -> pd.DataFrame:
        """
        Преобразование байтов CSV в DataFrame.

        Raises: ValueError - Если чтение не удалось
        """
        try:
            df = pd.read_csv(io.BytesIO(source))
            logger.info(f"Successfully read CSV: {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as exc:
            logger.error(f"Failed to read CSV: {exc}")
            raise ValueError(MSG_DATA_PARSE_ERROR.format(detail=str(exc))) from exc


class FormDataReader(DataReader):
    """Преобразует список словарей (поля формы) в DataFrame."""

    def read(self, source: list[dict[str, Any]]) -> pd.DataFrame:
        """
        Преобразование списка словарей в DataFrame.

        Raises: ValueError - Если преобразование не удалось
        """
        try:
            df = pd.DataFrame(source)
            logger.info(f"Successfully converted form data: {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as exc:
            logger.error(f"Failed to convert form data: {exc}")
            raise ValueError(MSG_DATA_PARSE_ERROR.format(detail=str(exc))) from exc


# Сервис


class DataService:
    """
    Фасад для работы с данными: выбор подходящего читателя и единый API.

    Используется в контроллерах для загрузки данных из разных источников.
    """

    def __init__(self) -> None:
        self._csv_reader = CSVDataReader()
        self._form_reader = FormDataReader()
        self._csv_validator = FileValidator(SUPPORTED_DATA_EXTENSIONS)
        logger.info("DataService initialized")

    # Публичный интерфейс

    def is_supported_file(self, filename: str) -> bool:
        """Проверка, поддерживается ли расширение файла данных."""
        supported = self._csv_validator.is_supported(filename)
        if not supported:
            logger.warning(f"Unsupported data file: {filename}")
        return supported

    def show_supported_extensions(self) -> str:
        """Возврат строки допустимых расширений для вывода пользователю."""
        return self._csv_validator.show_supported_extensions()

    def read_csv_bytes(self, csv_bytes: bytes) -> pd.DataFrame:
        """Чтение CSV из байтов."""
        logger.debug("Reading CSV from bytes")
        return self._csv_reader.read(csv_bytes)

    def read_form_data(self, rows: list[dict[str, Any]]) -> pd.DataFrame:
        """Преобразование данные формы (список словарей) в DataFrame."""
        logger.debug(f"Converting form data with {len(rows)} rows")
        return self._form_reader.read(rows)

    @staticmethod
    def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
        """Преобразование DataFrame в список словарей для JSON-ответа."""
        records = df.to_dict(orient="records")
        logger.debug(f"Converted DataFrame to {len(records)} records")
        return records

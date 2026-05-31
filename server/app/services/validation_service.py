"""
DataValidationService — единственная ответственность: валидация DataFrame
по схеме проекта DATA_SCHEMA.

Выполняемые проверки (по порядку)
──────────────────────────────────
  1. DataFrame не пустой.
  2. Все обязательные колонки присутствуют.
  3. Числовые колонки (float64 / int64) приводятся к числу без ошибок.
  4. Категориальные колонки содержат только допустимые значения.

Расширение
──────────
  Добавить новый тип проверки → создать метод _check_*, Example: _check_name, _check_age, ...
  вызвать его в validate(). Остальной код не трогать.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Final

import pandas as pd
from app.config import (
    MSG_EMPTY_DATAFRAME,
    MSG_INVALID_CATEGORY,
    MSG_INVALID_DTYPE,
    MSG_MISSING_COLUMNS,
    MSG_VALIDATION_FAILED,
)
from app.schemas.data_schema import DATA_SCHEMA, ColumnDtype

# Максимальное количество примеров плохих значений в сообщении об ошибке
_MAX_BAD_SAMPLES: Final[int] = 5

# Настройка логгера
logger = logging.getLogger(__name__)


# ── Структуры данных результата ───────────────────────────────────────────────


@dataclass
class FieldError:
    """Одна ошибка валидации для одной колонки."""

    column: str
    message: str


@dataclass
class ValidationResult:
    """Агрегированный результат, возвращаемый DataValidationService.validate()."""

    is_valid: bool
    errors: list[FieldError] = field(default_factory=list)

    def summary(self) -> str:
        """Читаемый список всех ошибок в виде строки."""
        lines = "\n".join(f"  • {e.column}: {e.message}" for e in self.errors)
        return MSG_VALIDATION_FAILED.format(details=lines)


# ── Сервис ────────────────────────────────────────────────────────────────────


class DataValidationService:
    """
    Валидирует pandas DataFrame по DATA_SCHEMA.

    Использование::
        svc = DataValidationService()
        result = svc.validate(df)
        if not result.is_valid:
            raise ValueError(result.summary())
    """

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        logger.info(f"Starting validation of DataFrame with {len(df)} rows, {len(df.columns)} columns")
        errors: list[FieldError] = []

        # ── Проверка 1: DataFrame не пустой ───────────────────────────────────
        if df.empty:
            logger.warning("Validation failed: DataFrame is empty")
            errors.append(FieldError(column="*", message=MSG_EMPTY_DATAFRAME))
            return ValidationResult(is_valid=False, errors=errors)

        # ── Проверка 2: все обязательные колонки присутствуют ─────────────────
        missing = self._check_missing_columns(df)
        if missing:
            logger.warning(f"Validation failed: missing columns {missing}")
            errors.append(
                FieldError(
                    column="*",
                    message=MSG_MISSING_COLUMNS.format(columns=", ".join(f"'{c}'" for c in missing)),
                )
            )
            # Ранний выход — нельзя проверить типы/значения без колонок
            return ValidationResult(is_valid=False, errors=errors)

        # ── Проверка 3: числовые типы данных ──────────────────────────────────
        numeric_errors = self._check_numeric_columns(df)
        if numeric_errors:
            logger.debug(f"Numeric validation found {len(numeric_errors)} issues")
        errors.extend(numeric_errors)

        # ── Проверка 4: категориальные значения ───────────────────────────────
        categorical_errors = self._check_categorical_columns(df)
        if categorical_errors:
            logger.debug(f"Categorical validation found {len(categorical_errors)} issues")
        errors.extend(categorical_errors)

        is_valid = len(errors) == 0
        logger.info(f"Validation completed. Valid: {is_valid}, errors count: {len(errors)}")
        if not is_valid:
            for err in errors:
                logger.debug(f"  - {err.column}: {err.message}")

        return ValidationResult(is_valid=is_valid, errors=errors)

    # ── Приватные проверки ────────────────────────────────────────────────────

    @staticmethod
    def _check_missing_columns(df: pd.DataFrame) -> list[str]:
        """Вернуть список обязательных колонок, отсутствующих в df."""
        required = {spec.name for spec in DATA_SCHEMA}
        present = set(df.columns)
        missing = sorted(required - present)
        if missing:
            logger.debug(f"Missing columns: {missing}")
        return missing

    @staticmethod
    def _check_numeric_columns(df: pd.DataFrame) -> list[FieldError]:
        """
        Для каждой колонки float64/int64 попытаться привести значения к числу.
        Строки, которые не удаётся привести → помечаются как ошибка.
        """
        errors: list[FieldError] = []
        for spec in DATA_SCHEMA:
            if spec.dtype not in (ColumnDtype.FLOAT, ColumnDtype.INT):
                continue
            if spec.name not in df.columns:
                continue  # уже поймано проверкой на отсутствующие колонки

            coerced = pd.to_numeric(df[spec.name], errors="coerce")
            bad_mask = coerced.isna()
            if not spec.nullable:
                bad_mask = bad_mask | df[spec.name].isna()

            if bad_mask.any():
                bad_vals = df.loc[bad_mask, spec.name].astype(str).unique()[:_MAX_BAD_SAMPLES].tolist()
                logger.debug(f"Numeric column '{spec.name}' has invalid values: {bad_vals}")
                errors.append(
                    FieldError(
                        column=spec.name,
                        message=MSG_INVALID_DTYPE.format(
                            column=spec.name,
                            expected=spec.dtype.value,
                            values=", ".join(f"'{v}'" for v in bad_vals),
                        ),
                    )
                )
        return errors

    @staticmethod
    def _check_categorical_columns(df: pd.DataFrame) -> list[FieldError]:
        """
        Для каждой колонки object с allowed_values найти значения вне допустимого множества.
        """
        errors: list[FieldError] = []
        for spec in DATA_SCHEMA:
            if spec.dtype != ColumnDtype.OBJECT or not spec.allowed_values:
                continue
            if spec.name not in df.columns:
                continue

            allowed_set = set(spec.allowed_values)
            col_vals = df[spec.name].dropna().astype(str)
            invalid = col_vals[~col_vals.isin(allowed_set)].unique()

            if len(invalid) > 0:
                logger.debug(f"Categorical column '{spec.name}' has invalid values: {invalid}")
                errors.append(
                    FieldError(
                        column=spec.name,
                        message=MSG_INVALID_CATEGORY.format(
                            column=spec.name,
                            invalid=", ".join(f"'{v}'" for v in invalid[:_MAX_BAD_SAMPLES]),
                            allowed=", ".join(f"'{v}'" for v in sorted(allowed_set)),
                        ),
                    )
                )
        return errors

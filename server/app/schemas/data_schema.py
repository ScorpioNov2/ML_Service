"""
Data Schema — единственное место описания всех колонок датасета.

Чтобы добавить новую колонку:
  1. Добавить ColumnSpec в DATA_SCHEMA.
  2. Ничего больше менять не нужно — ValidationService читает схему автоматически.

ColumnDtype соответствует pandas dtype:
  FLOAT  → float64 (принимает int тоже)
  INT    → int64
  OBJECT → object / str (если задан allowed_values — проверяется список)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

# ── Dtype enum ─────────────────────────────────────────────────────────────────


class ColumnDtype(str, Enum):
    FLOAT = "float64"
    INT = "int64"
    OBJECT = "object"


# ── Column specification ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ColumnSpec:
    """Describes a single expected column in the input DataFrame."""

    name: str
    dtype: ColumnDtype
    # None → принимать любые строки; list → жёсткое перечисление допустимых значений
    allowed_values: Optional[tuple[str, ...]] = None
    nullable: bool = False  # True → разрешить NaN в этой колонке


# ── Schema definition ───────────────────────────────────────────────────────────
# Порядок колонок соответствует порядку признаков модели.

DATA_SCHEMA: tuple[ColumnSpec, ...] = (
    # ── Личная информация ───────────────────────────────────────
    ColumnSpec("person_age", ColumnDtype.FLOAT),
    ColumnSpec("person_gender", ColumnDtype.OBJECT, allowed_values=("female", "male")),
    ColumnSpec(
        "person_education",
        ColumnDtype.OBJECT,
        allowed_values=("High School", "Associate", "Bachelor", "Master", "Doctorate"),
    ),
    ColumnSpec("person_income", ColumnDtype.FLOAT),
    ColumnSpec("person_emp_exp", ColumnDtype.INT),
    ColumnSpec(
        "person_home_ownership",
        ColumnDtype.OBJECT,
        allowed_values=("RENT", "OWN", "MORTGAGE", "OTHER"),
    ),
    # ── Информация о кредите ────────────────────────────────────
    ColumnSpec("loan_amnt", ColumnDtype.FLOAT),
    ColumnSpec(
        "loan_intent",
        ColumnDtype.OBJECT,
        allowed_values=(
            "PERSONAL",
            "EDUCATION",
            "MEDICAL",
            "VENTURE",
            "HOMEIMPROVEMENT",
            "DEBTCONSOLIDATION",
        ),
    ),
    ColumnSpec("loan_int_rate", ColumnDtype.FLOAT),
    ColumnSpec("loan_percent_income", ColumnDtype.FLOAT),
    # ── Кредитная история ───────────────────────────────────────
    ColumnSpec("cb_person_cred_hist_length", ColumnDtype.FLOAT),
    ColumnSpec("credit_score", ColumnDtype.INT),
    ColumnSpec(
        "previous_loan_defaults_on_file",
        ColumnDtype.OBJECT,
        allowed_values=("No", "Yes"),
    ),
)

# Быстрый поиск по имени колонки: { "person_age": ColumnSpec(...), ... }
SCHEMA_MAP: dict[str, ColumnSpec] = {spec.name: spec for spec in DATA_SCHEMA}

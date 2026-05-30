"""
generate_sample_model.py
────────────────────────
Создаёт демонстрационную модель sklearn, совместимую с DATA_SCHEMA проекта
(13 признаков: числовые + категориальные), и сохраняет её как ./models/model.pkl.

Запустить один раз перед стартом сервера:
    python generate_sample_model.py
"""

import pickle
import sys
from pathlib import Path

# Добавить корень проекта в sys.path для импорта app.*
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder, StandardScaler

from app.schemas.data_schema import DATA_SCHEMA, ColumnDtype

MODELS_DIR    = Path("./models")
OUTPUT_PATH   = MODELS_DIR / "model.pkl"
RANDOM_STATE  = 42
N_SAMPLES     = 500


def _generate_sample_data() -> pd.DataFrame:
    """Сгенерировать синтетический датасет, совместимый со схемой DATA_SCHEMA."""
    rng = np.random.default_rng(RANDOM_STATE)
    rows = {}

    for spec in DATA_SCHEMA:
        if spec.dtype == ColumnDtype.FLOAT:
            rows[spec.name] = rng.uniform(1, 100, N_SAMPLES).astype(float)
        elif spec.dtype == ColumnDtype.INT:
            rows[spec.name] = rng.integers(1, 50, N_SAMPLES).astype(int)
        elif spec.dtype == ColumnDtype.OBJECT and spec.allowed_values:
            rows[spec.name] = rng.choice(list(spec.allowed_values), N_SAMPLES)
        else:
            rows[spec.name] = [f"value_{i % 5}" for i in range(N_SAMPLES)]

    return pd.DataFrame(rows)


def _build_pipeline(df: pd.DataFrame) -> Pipeline:
    """Построить sklearn Pipeline с предобработкой и классификатором."""
    numeric_cols     = [s.name for s in DATA_SCHEMA if s.dtype in (ColumnDtype.FLOAT, ColumnDtype.INT)]
    categorical_cols = [s.name for s in DATA_SCHEMA if s.dtype == ColumnDtype.OBJECT]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(),   numeric_cols),
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), categorical_cols),
        ],
        remainder="drop",
    )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier",   LogisticRegression(random_state=RANDOM_STATE, max_iter=200)),
    ])


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print("⏳ Генерация синтетических данных...")
    df = _generate_sample_data()

    # Синтетическая целевая переменная (одобрение кредита)
    # Используем комбинацию признаков для гарантии двух классов
    score_norm = (df["credit_score"] - df["credit_score"].mean()) / df["credit_score"].std()
    income_norm = (df["person_income"] - df["person_income"].mean()) / df["person_income"].std()
    y = (score_norm + income_norm > 0).astype(int).values

    print("⏳ Обучение модели Pipeline (предобработка + LogisticRegression)...")
    pipeline = _build_pipeline(df)
    pipeline.fit(df, y)

    with OUTPUT_PATH.open("wb") as fh:
        pickle.dump(pipeline, fh)

    print(f"✅  Модель сохранена: {OUTPUT_PATH}")
    print(f"   Признаков: {len(DATA_SCHEMA)}")
    print(f"   Числовых:  {sum(1 for s in DATA_SCHEMA if s.dtype in (ColumnDtype.FLOAT, ColumnDtype.INT))}")
    print(f"   Категориальных: {sum(1 for s in DATA_SCHEMA if s.dtype == ColumnDtype.OBJECT)}")


if __name__ == "__main__":
    main()

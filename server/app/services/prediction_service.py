"""
PredictionService — единственная ответственность: выполнение предсказания.

Ничего не знает о HTTP, форматах файлов или сериализации моделей.
Просто вызывает model.predict() и добавляет результаты как новую колонку.
"""

from __future__ import annotations

from typing import Dict, Any

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

from app.config import MSG_PREDICTION_ERROR, PREDICTED_COLUMN_NAME, PROBABILITY_COLUMN_NAME


class PredictionService:
    """Запускает инференс и возвращает обогащённый DataFrame."""
    def __init__(self):
        self._loan_data_processor = LoanDataProcessor()

    def predict(self, model: Dict | Any, df: pd.DataFrame) -> pd.DataFrame:
        try:
            if isinstance(model, dict):
                if 'scaler' in model:
                    self._loan_data_processor.scaler = model['scaler']
                features = model.get('features', self._loan_data_processor.selected_features)
                self._loan_data_processor.selected_features = features
                base_model = model["model"]
                processed_data = self._loan_data_processor.process_raw_data(df)
            else:
                base_model = model
                processed_data = df
                
            predictions = base_model.predict(processed_data)
            prob_matrix = base_model.predict_proba(processed_data)
            probability = np.round(np.max(prob_matrix, axis=1), 4)

        except Exception as exc:
            raise ValueError(
                MSG_PREDICTION_ERROR.format(detail=str(exc))
            ) from exc

        result = df.copy()
        result[PREDICTED_COLUMN_NAME] = predictions
        result[PROBABILITY_COLUMN_NAME] = (pd.Series(probability) * 100).apply('{:.2f}'.format).values

        return result
    
    def _preprocess_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._loan_data_processor.process_raw_data(df)

class LoanDataProcessor:
    def __init__(self):
        self.selected_features = [
            "person_age",
            "person_income",
            "person_emp_exp",
            "person_home_ownership",
            "loan_amnt",
            "loan_int_rate",
            "loan_percent_income",
            "cb_person_cred_hist_length",
            "credit_score",
            "previous_loan_defaults_on_file"
        ]

        self.education_order = {
            "High School": 0,
            "Associate": 1,
            "Bachelor": 2,
            "Master": 3,
            "Doctorate": 4
        }

        self.home_ownership_map = {
            "RENT": 1,
            "MORTGAGE": 2,
            "OWN": 3,
            "OTHER": 4
        }

        self.loan_intent_map = {
            "PERSONAL": 1,
            "EDUCATION": 2,
            "MEDICAL": 3,
            "VENTURE": 4,
            "HOMEIMPROVEMENT": 5,
            "DEBTCONSOLIDATION": 6
        }

        self.gender_map = {
            "male": 1,
            "female": 0
        }

        self.previous_defaults_map = {
            "Yes": 1,
            "No": 0
        }

        self.scaler = StandardScaler()
        self.is_fitted = False

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df = df[df["person_age"].between(18, 100)]
        df = df[df["person_emp_exp"] < df["person_age"]]
        df = df[df["credit_score"].between(300, 850)]
        df = df[df["person_income"] > 0]

        return df.reset_index(drop=True)

    def encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        if "person_gender" in df.columns:
            df["person_gender"] = df["person_gender"].map(self.gender_map)

        if "person_education" in df.columns:
            df["person_education"] = df["person_education"].map(self.education_order)

        if "person_home_ownership" in df.columns:
            df["person_home_ownership"] = df["person_home_ownership"].map(
                self.home_ownership_map
            )

        if "loan_intent" in df.columns:
            df["loan_intent"] = df["loan_intent"].map(self.loan_intent_map)

        if "previous_loan_defaults_on_file" in df.columns:
            df["previous_loan_defaults_on_file"] = df[
                "previous_loan_defaults_on_file"
            ].map(self.previous_defaults_map)

        return df

    def select_features(self, df: pd.DataFrame) -> pd.DataFrame:
        missing_columns = [
            column for column in self.selected_features
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        return df[self.selected_features]

    def process_raw_data(self, data):
        """
        raw data -> clean -> encode -> select features -> scale -> processed data
        """

        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            raise ValueError(
                "Input data must be dict, list of dicts, or pandas DataFrame"
            )

        if "loan_status" in df.columns:
            df = df.drop(columns=["loan_status"])

        df = self.clean_data(df)

        if df.empty:
            raise ValueError(
                "No valid rows after cleaning. Check person_age, credit_score, person_income and person_emp_exp."
            )

        df = self.encode_categorical_features(df)
        df = self.select_features(df)

        processed_data = self.scaler.transform(df)

        return processed_data

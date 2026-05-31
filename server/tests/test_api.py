"""
Модульные тесты API.

Проверяют эндпоинты /health, /predict/form, /predict/csv, /predict/custom.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    """Проверка эндпоинта /health."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_form_missing_data():
    """Отправка пустого form_data -> ожидание 422."""
    response = client.post("/api/v1/predict/form", data={"form_data": "[]"})
    assert response.status_code == 422


def test_predict_form_with_valid_data():
    """Корректные данные формы -> статус 200, поле predicted присутствует."""
    sample = [
        {
            "person_age": 35.0,
            "person_gender": "male",
            "person_education": "Bachelor",
            "person_income": 60000.0,
            "person_emp_exp": 5,
            "person_home_ownership": "RENT",
            "loan_amnt": 10000.0,
            "loan_intent": "PERSONAL",
            "loan_int_rate": 12.5,
            "loan_percent_income": 0.25,
            "cb_person_cred_hist_length": 3.0,
            "credit_score": 650,
            "previous_loan_defaults_on_file": "No",
        }
    ]
    response = client.post("/api/v1/predict/form", data={"form_data": json.dumps(sample)})
    assert response.status_code == 200
    data = response.json()
    assert data["status_code"] == 200
    assert "predicted" in data["data"][0]


def test_predict_form_invalid_json():
    """Некорректный JSON в form_data -> ожидание 400."""
    response = client.post("/api/v1/predict/form", data={"form_data": "not a json"})
    assert response.status_code == 400


def test_predict_csv_valid():
    """Загрузка корректного CSV -> статус 200, поле predicted присутствует."""
    csv_content = """person_age,person_gender,person_education,person_income,person_emp_exp,person_home_ownership,loan_amnt,loan_intent,loan_int_rate,loan_percent_income,cb_person_cred_hist_length,credit_score,previous_loan_defaults_on_file
35,male,Bachelor,60000,5,RENT,10000,PERSONAL,12.5,0.25,3,650,No"""
    files = {"data_file": ("data.csv", csv_content, "text/csv")}
    response = client.post("/api/v1/predict/csv", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status_code"] == 200
    assert "predicted" in data["data"][0]


def test_predict_custom_with_model_and_form(tmp_path):
    """Загрузка своей модели и данных формы -> статус 200."""
    model_path = tmp_path / "model.pkl"
    import shutil
    from pathlib import Path

    default_model = Path("models/model.pkl")
    if default_model.exists():
        shutil.copy(default_model, model_path)
    else:
        pytest.skip("No default model found for custom test")

    sample = [
        {
            "person_age": 35.0,
            "person_gender": "male",
            "person_education": "Bachelor",
            "person_income": 60000.0,
            "person_emp_exp": 5,
            "person_home_ownership": "RENT",
            "loan_amnt": 10000.0,
            "loan_intent": "PERSONAL",
            "loan_int_rate": 12.5,
            "loan_percent_income": 0.25,
            "cb_person_cred_hist_length": 3.0,
            "credit_score": 650,
            "previous_loan_defaults_on_file": "No",
        }
    ]
    with open(model_path, "rb") as f:
        files = {"model_file": ("model.pkl", f, "application/octet-stream")}
        data = {"form_data": json.dumps(sample)}
        response = client.post("/api/v1/predict/custom", files=files, data=data)
    assert response.status_code == 200
    assert response.json()["status_code"] == 200


def test_predict_custom_missing_model():
    """Отправка запроса без model_file -> ожидание 422 (валидация данных)."""
    sample = [{"person_age": 35}]
    response = client.post("/api/v1/predict/custom", data={"form_data": json.dumps(sample)})
    assert response.status_code == 422

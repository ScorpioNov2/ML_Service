import json

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_form_missing_data():
    response = client.post("/api/v1/predict/form", data={"form_data": "[]"})
    assert response.status_code == 422  # пустой массив не пройдёт валидацию


def test_predict_form_with_valid_data():
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

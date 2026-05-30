# ML Prediction API — FastAPI

## Структура проекта

```
fastapi_ml_predictor/
├── app/
│   ├── main.py                              # Фабрика приложения + CORS + роутеры
│   ├── config.py                            # Все константы и сообщения
│   ├── controllers/
│   │   └── prediction_controller.py        # Три обработчика + общий pipeline
│   ├── routers/
│   │   └── prediction_router.py            # Три HTTP-эндпоинта (тонкий слой)
│   ├── services/
│   │   ├── model_service.py                # Загрузка модели (.pkl, расширяемо)
│   │   ├── data_service.py                 # Чтение CSV / JSON-формы → DataFrame
│   │   ├── prediction_service.py           # model.predict() + колонка predicted
│   │   └── validation_service.py           # Валидация DataFrame (4 проверки)
│   ├── schemas/
│   │   ├── prediction_schema.py            # Pydantic-модели HTTP-ответов
│   │   └── data_schema.py                  # Схема 13 колонок (DATA_SCHEMA)
│   └── utils/
│       └── file_validator.py               # Проверка допустимых расширений
├── models/
│   └── model.pkl                           # Модель по умолчанию (Pipeline sklearn)
├── generate_sample_model.py                # Генерация демо-модели под DATA_SCHEMA
├── requirements.txt
└── README.md
```

---

## Быстрый старт

```bash
pip install -r requirements.txt
python generate_sample_model.py   # создать модель по умолчанию
uvicorn app.main:app --reload
```

Swagger UI:   **http://localhost:8000/docs**
Health check: **http://localhost:8000/health**

---

## Три эндпоинта

Логика разделения проста: **что ты загружаешь → на тот эндпоинт и идёшь**.

```
Есть только данные (форма)?     →  POST /api/v1/predict/form
Есть только данные (CSV)?       →  POST /api/v1/predict/csv
Есть своя модель + данные?      →  POST /api/v1/predict/custom
```

---

### `POST /api/v1/predict/form`
Данные вводятся вручную. Модель по умолчанию.

| Поле      | Тип           | Обяз. | Описание                              |
|-----------|---------------|-------|---------------------------------------|
| form_data | строка (JSON) | ✅    | `[{"person_age": 35.0, ...}]`         |

---

### `POST /api/v1/predict/csv`
Данные загружаются из файла. Модель по умолчанию.

| Поле      | Тип         | Обяз. | Описание                              |
|-----------|-------------|-------|---------------------------------------|
| data_file | файл (.csv) | ✅    | CSV с колонками согласно DATA_SCHEMA  |

---

### `POST /api/v1/predict/custom`
Пользователь загружает свою модель. Данные — форма или CSV.

| Поле       | Тип           | Обяз. | Описание                                          |
|------------|---------------|-------|---------------------------------------------------|
| model_file | файл (.pkl)   | ✅    | Своя модель sklearn                               |
| data_file  | файл (.csv)   | ❌ *  | CSV-файл (приоритет над form_data)                |
| form_data  | строка (JSON) | ❌ *  | `[{"person_age": 35.0, ...}]`                     |

\* Необходимо передать хотя бы одно из двух.

---

## Формат ответа (JSON)

Все три эндпоинта возвращают единый конверт:

**Успех (200):**
```json
{
  "status_code": 200,
  "message": "Предсказание выполнено успешно. Обработано строк: 1.",
  "data": [
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
      "predicted": 1
    }
  ]
}
```

**Ошибка валидации (422):**
```json
{
  "status_code": 422,
  "message": "Данные не прошли валидацию:\n  • person_gender: Недопустимые значения: 'robot'. Разрешённые: 'female', 'male'\n  • person_age: Тип float64, нечисловые значения: 'abc'",
  "data": null
}
```

---

## Коды ответов

| Код | Когда возникает                                         |
|-----|---------------------------------------------------------|
| 200 | Предсказание выполнено — JSON-массив с `predicted`      |
| 400 | Данные не переданы / неверный формат файла / JSON       |
| 404 | Модель по умолчанию не найдена в `./models/`            |
| 422 | Данные не прошли валидацию схемы                        |
| 500 | Ошибка загрузки модели / ошибка `predict()`             |

---

## Pipeline обработки (одинаков для всех трёх эндпоинтов)

```
[1] Загрузка модели
    ├── /form, /csv  → ./models/model.pkl (по умолчанию)
    └── /custom      → загруженный .pkl файл (обязателен)

[2] Парсинг данных
    ├── CSV  → pd.read_csv()
    └── JSON → pd.DataFrame()

[3] Валидация DataFrame
    ├── DataFrame не пустой?
    ├── Все 13 колонок присутствуют?
    ├── Числовые колонки → float64 / int64?
    └── Категориальные → входят в allowed_values?

[4] Предсказание
    └── model.predict(df) → добавить колонку "predicted"

[5] JSON-ответ
    └── { status_code, message, data: list[dict] }
```

---

## Схема данных (`app/schemas/data_schema.py`)

Единственное место описания всех колонок.
**Добавить колонку** = добавить один `ColumnSpec`, больше ничего менять не нужно.

| # | Колонка                           | Dtype   | Допустимые значения                                                                    |
|---|-----------------------------------|---------|----------------------------------------------------------------------------------------|
| 0 | person_age                        | float64 | любое число                                                                            |
| 1 | person_gender                     | object  | `female`, `male`                                                                       |
| 2 | person_education                  | object  | `High School`, `Associate`, `Bachelor`, `Master`, `Doctorate`                          |
| 3 | person_income                     | float64 | любое число                                                                            |
| 4 | person_emp_exp                    | int64   | любое целое                                                                            |
| 5 | person_home_ownership             | object  | `RENT`, `OWN`, `MORTGAGE`, `OTHER`                                                     |
| 6 | loan_amnt                         | float64 | любое число                                                                            |
| 7 | loan_intent                       | object  | `PERSONAL`, `EDUCATION`, `MEDICAL`, `VENTURE`, `HOMEIMPROVEMENT`, `DEBTCONSOLIDATION`  |
| 8 | loan_int_rate                     | float64 | любое число                                                                            |
| 9 | loan_percent_income               | float64 | любое число                                                                            |
|10 | cb_person_cred_hist_length        | float64 | любое число                                                                            |
|11 | credit_score                      | int64   | любое целое                                                                            |
|12 | previous_loan_defaults_on_file    | object  | `No`, `Yes`                                                                            |

---

## Расширение

### Добавить новую колонку

```python
# app/schemas/data_schema.py — только здесь, больше ничего не трогать
DATA_SCHEMA = (
    ...
    ColumnSpec("debt_to_income",  ColumnDtype.FLOAT),
    ColumnSpec("region", ColumnDtype.OBJECT, allowed_values=("NORTH", "SOUTH")),
)
```

### Добавить формат модели (например, joblib)

```python
# 1. Новый загрузчик в app/services/model_service.py
class JobLibModelLoader(ModelLoader):
    def load(self, stream): import joblib; return joblib.load(stream)

_loader_registry = {".pkl": PickleModelLoader, ".joblib": JobLibModelLoader}

# 2. Зарегистрировать расширение в app/config.py
SUPPORTED_MODEL_EXTENSIONS = [".pkl", ".joblib"]
```

---

## Примеры cURL

```bash
# /predict/form — JSON-форма, модель по умолчанию
curl -X POST http://localhost:8000/api/v1/predict/form \
  -F 'form_data=[{
    "person_age":35.0,"person_gender":"male","person_education":"Bachelor",
    "person_income":60000.0,"person_emp_exp":5,"person_home_ownership":"RENT",
    "loan_amnt":10000.0,"loan_intent":"PERSONAL","loan_int_rate":12.5,
    "loan_percent_income":0.25,"cb_person_cred_hist_length":3.0,
    "credit_score":650,"previous_loan_defaults_on_file":"No"
  }]'

# /predict/csv — CSV-файл, модель по умолчанию
curl -X POST http://localhost:8000/api/v1/predict/csv \
  -F "data_file=@data.csv"

# /predict/custom — своя модель + CSV
curl -X POST http://localhost:8000/api/v1/predict/custom \
  -F "model_file=@my_model.pkl" \
  -F "data_file=@data.csv"

# /predict/custom — своя модель + JSON-форма
curl -X POST http://localhost:8000/api/v1/predict/custom \
  -F "model_file=@my_model.pkl" \
  -F 'form_data=[{"person_age":28.0,"person_gender":"female",...}]'
```

---

## SOLID

| Принцип | Применение                                                                                                  |
|---------|-------------------------------------------------------------------------------------------------------------|
| **S**RP | Каждый класс — одна задача: `ModelService` грузит, `DataValidationService` валидирует, `PredictionService` предсказывает |
| **O**CP | Новый формат → новый подкласс + одна строка в реестре, без правок существующего кода                        |
| **L**SP | Все загрузчики и читатели взаимозаменяемы через абстрактный базовый класс                                   |
| **I**SP | `ModelLoader.load()` — минимальный интерфейс                                                                |
| **D**IP | `PredictionController` зависит от абстракций, не от конкретных реализаций                                   |

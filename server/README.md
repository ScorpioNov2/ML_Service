# ML Prediction API — FastAPI

## Структура проекта

```
fastapi_ml_predictor/
├── app/
│   ├── main.py                          # Фабрика приложения + CORS + подключение роутеров
│   ├── config.py                        # Все константы (без magic strings/numbers)
│   ├── controllers/
│   │   └── prediction_controller.py     # Оркестрация (HTTP ↔ сервисы)
│   ├── routers/
│   │   └── prediction_router.py         # HTTP-эндпоинты (тонкий слой)
│   ├── services/
│   │   ├── model_service.py             # Загрузка модели (.pkl, расширяемо)
│   │   ├── data_service.py              # Чтение CSV / полей формы
│   │   └── prediction_service.py        # Вызов model.predict()
│   ├── schemas/
│   │   └── prediction_schema.py         # Pydantic-модели ответов
│   └── utils/
│       └── file_validator.py            # Проверка допустимых расширений файлов
├── models/                              # Директория с моделью по умолчанию
│   └── model.pkl                        # (создаётся через generate_sample_model.py)
├── generate_sample_model.py             # Генерация демо-модели
├── requirements.txt
└── README.md
```

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Создание модели по умолчанию (демо)

```bash
python generate_sample_model.py
```

## Запуск сервера

```bash
uvicorn app.main:app --reload
```

Swagger UI: http://localhost:8000/docs

---

## API Endpoints

### `POST /api/v1/predict`

Загрузите модель и данные — получите CSV-файл с предсказаниями.

**Поля формы (multipart/form-data):**

| Поле        | Тип           | Обязательно | Описание                                                              |
|-------------|---------------|-------------|-----------------------------------------------------------------------|
| model_file  | файл (.pkl)   | Нет         | Модель sklearn. Если не загружена — используется `./models/model.pkl` |
| data_file   | файл (.csv)   | Нет*        | Входной CSV-файл. Приоритет над form_data                             |
| form_data   | строка (JSON) | Нет*        | JSON-массив строк, например `[{"col1":1,"col2":2}]`                   |

\* Необходимо передать хотя бы одно из двух: `data_file` или `form_data`.

**Успешный ответ:** потоковый файл `.csv` с добавленным столбцом `predicted`.

**Ответ при ошибке (JSON):**
```json
{
  "status_code": 400,
  "message": "Описание ошибки",
  "data": null
}
```

---

## Обрабатываемые сценарии

| Сценарий                                    | HTTP-статус | Результат                                              |
|---------------------------------------------|-------------|--------------------------------------------------------|
| model_file не является .pkl                 | 400         | JSON-ошибка — формат файла не поддерживается           |
| model_file не передан                       | —           | Используется модель по умолчанию `./models/model.pkl`  |
| Модель по умолчанию отсутствует             | 404         | JSON-ошибка — модель не найдена                        |
| Не переданы data_file и form_data           | 400         | JSON-ошибка — нет данных для предсказания              |
| data_file не является .csv                  | 400         | JSON-ошибка — формат файла не поддерживается           |
| Предсказание выполнено успешно              | 200         | CSV-поток со столбцом `predicted`                      |

---

## Расширение (Scaleable)

### Добавление нового формата модели (например: joblib)

```python
# app/services/model_service.py
class JobLibModelLoader(ModelLoader):
    def load(self, stream):
        import joblib, io
        return joblib.load(stream)

# Добавить в реестр:
_loader_registry = {
    ".pkl":    PickleModelLoader,
    ".joblib": JobLibModelLoader,   # ← добавить эту строку
}

# app/config.py
SUPPORTED_MODEL_EXTENSIONS = [".pkl", ".joblib"]  # ← добавить расширение
```

### Добавление нового формата данных (например: Excel)

```python
# app/services/data_service.py
class ExcelDataReader(DataReader):
    def read(self, source: bytes) -> pd.DataFrame:
        return pd.read_excel(io.BytesIO(source))
```

---

## Примеры cURL

### Загрузка CSV + пользовательская модель
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -F "model_file=@my_model.pkl" \
  -F "data_file=@data.csv" \
  --output result.csv
```

### Только form_data (JSON) + модель по умолчанию
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -F 'form_data=[{"feature_0": 1.2, "feature_1": -0.5}, {"feature_0": 0.3, "feature_1": 2.1}]' \
  --output result.csv
```

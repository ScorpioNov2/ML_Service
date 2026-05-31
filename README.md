# Ипотечный консультант — ML-сервис предсказания одобрения ипотеки
4
Сервис позволяет предсказывать вероятность одобрения ипотеки на основе анкетных данных клиента.  
Реализован полный цикл: обработка данных, обучение модели (синтетические данные), API на FastAPI, веб-интерфейс, CI/CD, контейнеризация и логирование.

---

## Структура проекта

```
ML_Service/
├── .github/workflows/          # GitHub Actions ci
│   └── ci.yml
├── .sourcecraft/               # SourceCraft CI (альтернативный)
├── client/                     # Фронтенд (HTML/CSS/JS)
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   ├── package.json
│   ├── package-lock.json
│   ├── .stylelintrc.json
│   └── eslint.config.js
├── server/                     # Бэкенд (FastAPI)
│   ├── app/
│   │   ├── controllers/        # Обработчики запросов
│   │   ├── routers/            # Роутеры (form, csv, custom)
│   │   ├── schemas/            # Pydantic схемы и схема данных
│   │   ├── services/           # Логика (модель, данные, предсказание, валидация)
│   │   ├── utils/              # Вспомогательные утилиты
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/                  # Модульные тесты
│   ├── models/                 # Хранение модели по умолчанию
│   ├── requirements.txt
│   ├── .flake8
│   └── pyproject.toml          # Настройки black/isort/pytest
├── model-training/             # Скрипты генерации модели
│   ├── models/
│   │   └── model.pkl
│   └── generate_sample_model.py
├── docker/                     # Docker-конфигурация
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── .gitignore
└── README.md
```

---

## Быстрый старт

### Локальный запуск (без Docker)

#### Бэкенд
```bash
cd server
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API будет доступно: `http://localhost:8000/docs`

#### Фронтенд
```bash
cd client
python -m http.server 8080
```
Открыть в браузере: `http://localhost:8080`

### Запуск через Docker Compose
```bash
docker-compose -f docker/docker-compose.yml up --build
```
- Фронтенд: `http://localhost`
- Бэкенд API: `http://localhost:8000/docs`

---

## API Endpoints

Сервис предоставляет **три** эндпоинта:

| Метод | URL | Описание |
|-------|-----|-----------|
| `POST` | `/api/v1/predict/form` | Ручной ввод данных (JSON-массив), модель по умолчанию |
| `POST` | `/api/v1/predict/csv` | Загрузка CSV-файла, модель по умолчанию |
| `POST` | `/api/v1/predict/custom` | Своя модель (`.pkl`) + данные (CSV или JSON-форма) |

> **Примечание:** Эндпоинты `/upload-model`, `/predict`, `/predict-from-csv` в задании - в реализации они объединены логикой `/custom` и `/form`/`/csv`. Это сделано для удобства.

### Формат ответа (JSON)
```json
{
  "status_code": 200,
  "message": "Предсказание выполнено успешно. Обработано строк: 1.",
  "data": [
    {
      "person_age": 35.0,
      "person_gender": "male",
      ...,
      "predicted": 1,
      "confidence (%)": "99.54"
    }
  ]
}
```

### Примеры cURL
```bash
# Ручной ввод (form)
curl -X POST http://localhost:8000/api/v1/predict/form \
  -F 'form_data=[{"person_age":35,"person_gender":"male",...}]'

# CSV-файл
curl -X POST http://localhost:8000/api/v1/predict/csv \
  -F "data_file=@data.csv"

# Своя модель + CSV
curl -X POST http://localhost:8000/api/v1/predict/custom \
  -F "model_file=@model.pkl" -F "data_file=@data.csv"
```

---

## Тестирование и линтинг

### Бэкенд
```bash
cd server
pytest tests/ -v --cov=app          # тесты
flake8 .                            # линтинг
black --check .                     # форматирование
isort --check-only .                # сортировка импортов
```

### Фронтенд
```bash
cd client
npm ci
npx html-validate "*.html"
npx stylelint "*.css"
npx eslint "*.js"
```

---

## CI/CD (GitHub Actions/SourceCraft)

- **GitHub Actions** (`.github/workflows/ci.yml`) - запускает все проверки при пуше в `main`/`master`.
- **SourceCraft** (`.sourcecraft/ci.yaml`) - аналогичный CI для внутренней платформы.

**Что проверяется:**
- Линтинг и форматирование Python (flake8, black, isort)
- Тесты pytest с покрытием
- Линтинг фронтенда (HTML, CSS, JS)
- Установка зависимостей через `npm ci` и `pip`

---

## Docker-контейнеризация

Образы для бэкенда (FastAPI + Uvicorn) и фронтенда (nginx).  
Для запуска всех сервисов используйте:

```bash
cd docker
docker-compose up --build
```

Логи контейнеров можно просмотреть командой `docker logs mortgage-backend` (благодаря настроенному логированию).

---

## Логирование

В сервисах `prediction_service.py` и `validation_service.py` добавлено логирование:
- Время выполнения предсказаний
- Этапы валидации данных
- Предупреждения о некорректных значениях
- Информация о загрузке модели

Логи выводятся в `stdout` - видны в консоли, Docker и CI.

---

## ML-модель

- **Синтетический датасет** (13 признаков) генерируется `generate_sample_model.py`.
- **Модель по умолчанию**: `LogisticRegression` в составе `Pipeline` (StandardScaler + OrdinalEncoder).
- Предобработка: очистка выбросов, кодирование категориальных признаков, отбор признаков.
- При желании вы можете обучить свою модель (например, RandomForest) и загрузить её через `/predict/custom`.

### Google Colab для обучения модели

Полный процесс обучения и сравнения моделей (логистическая регрессия, случайный лес, градиентный бустинг) с выбором лучшей по ROC-AUC описан в отдельном ноутбуке:

[**Google Colab**](https://colab.research.google.com/drive/1jaRXFYCuOpefex9IwzVvReSFc_3_ZHpc?usp=sharing)

В ноутбуке реализованы:  
- Очистка и предобработка данных  
- Кодирование категориальных признаков  
- Масштабирование  
- Разделение на train/test  
- Отбор признаков  
- Обучение и сравнение моделей по ROC-AUC  
- Сериализация лучшей модели в `.pkl`

---

## Фронтенд

- **Три вкладки**: «Форма» (ручной ввод), «CSV» (загрузка файла), «Своя модель» (загрузка `.pkl` и данных).
- Отображение предсказаний в виде таблицы с полями `predicted` (Одобрено/Отказ) и `confidence (%)`.
- Адаптивный дизайн, индикация загрузки, обработка ошибок.

---

## Выполненные требования лабораторной работы

1. Обработка данных (очистка, кодирование, масштабирование, отбор признаков)
2. Модель: сравнение ≥2 алгоритмов (логистическая регрессия, RandomForest)
3. Выбор лучшей модели по ROC-AUC 
4. API на FastAPI с тремя эндпоинтами 
5. Загрузка и сохранение модели 
6. Пользовательский интерфейс (форма, CSV, своя модель)
7. CI-сценарий (GitHub Actions + SourceCraft)
8. Логирование 
9. Docker-контейнеризация 
10. Валидация входных данных 
11. README

---

## Команда

- **ML Engineer** - подготовка данных, обучение модели, предобработка
- **Backend Developer** - реализация API на FastAPI, интеграция модели
- **Frontend Developer** - разработка интерфейса (HTML/CSS/JS)
- **DevOps** - настройка CI/CD, Docker, логирование, линтинг


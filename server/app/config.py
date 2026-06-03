"""
Конфигурация приложения: пути, CORS, сообщения об ошибках и допустимые форматы.
Все настройки собраны здесь, магические строки отсутствуют.
"""

from pathlib import Path

# Допустимые расширения файлов
SUPPORTED_MODEL_EXTENSIONS: list[str] = [".pkl"]
SUPPORTED_DATA_EXTENSIONS: list[str] = [".csv"]

# Модель по умолчанию
DEFAULT_MODEL_DIR: Path = Path("./models")
DEFAULT_MODEL_FILENAME: str = "model.pkl"

# Выходные данные
PREDICTED_COLUMN_NAME: str = "predicted"
PROBABILITY_COLUMN_NAME: str = "confidence (%)"

# CORS
CORS_ALLOW_ORIGINS: list[str] = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:3000",
    "http://localhost:8080",  # Html
    "http://localhost:5173",
    "https://ml-service-six.vercel.app"
]
CORS_ALLOW_METHODS: list[str] = ["*"]
CORS_ALLOW_HEADERS: list[str] = ["*"]
CORS_ALLOW_CREDENTIALS: bool = True

# Метаданные API
API_TITLE: str = "ML Prediction API"
API_VERSION: str = "1.0.0"
API_PREFIX: str = "/api/v1"

# Сообщения об ошибках и успехе
MSG_UNSUPPORTED_MODEL_FILE: str = "Формат файла модели не поддерживается. " "Допустимые форматы: {extensions}"
MSG_UNSUPPORTED_DATA_FILE: str = "Формат файла данных не поддерживается. " "Допустимые форматы: {extensions}"
MSG_NO_DATA: str = "Данные для предсказания не переданы. " "Загрузите CSV-файл или передайте form_data."
MSG_AMBIGUOUS_DATA_SOURCE: str = (
    "Переданы оба источника данных одновременно: data_file и form_data. "
    "Выберите один: либо CSV-файл, либо JSON-форму."
)
MSG_DEFAULT_MODEL_NOT_FOUND: str = (
    "Модель по умолчанию не найдена: {path}. " "Загрузите файл модели или поместите model.pkl в директорию ./models."
)
MSG_PREDICTION_SUCCESS: str = "Предсказание выполнено успешно. Обработано строк: {count}."
MSG_MODEL_LOAD_ERROR: str = "Не удалось загрузить модель: {detail}"
MSG_PREDICTION_ERROR: str = "Ошибка при выполнении предсказания: {detail}"
MSG_DATA_PARSE_ERROR: str = "Не удалось прочитать данные: {detail}"
MSG_FORM_DATA_INVALID: str = "Некорректный form_data (ожидается JSON-массив): {detail}"
MSG_NO_LOADER: str = "Загрузчик для расширения '{ext}' не зарегистрирован."

# Сообщения валидации данных
MSG_EMPTY_DATAFRAME: str = "Переданные данные не содержат ни одной строки."
MSG_MISSING_COLUMNS: str = "Отсутствуют обязательные колонки: {columns}"
MSG_INVALID_DTYPE: str = "Колонка '{column}' должна иметь тип {expected}, " "но содержит нечисловые значения: {values}"
MSG_INVALID_CATEGORY: str = (
    "Колонка '{column}' содержит недопустимые значения: {invalid}. " "Разрешённые значения: {allowed}"
)
MSG_VALIDATION_FAILED: str = "Данные не прошли валидацию:\n{details}"

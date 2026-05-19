"""
Centralized configuration — no magic strings, no magic numbers.
All tuneable values live here so the rest of the codebase stays clean.
"""

from pathlib import Path

# ── File extension allow-lists ────────────────────────────────────────────────
SUPPORTED_MODEL_EXTENSIONS: list[str] = [".pkl"]
SUPPORTED_DATA_EXTENSIONS: list[str] = [".csv"]

# ── Default model ─────────────────────────────────────────────────────────────
DEFAULT_MODEL_DIR: Path = Path("./models")
DEFAULT_MODEL_FILENAME: str = "model.pkl"

# ── Output ────────────────────────────────────────────────────────────────────
PREDICTED_COLUMN_NAME: str = "predicted"
OUTPUT_CSV_FILENAME: str = "prediction_result.csv"

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOW_ORIGINS: list[str] = ["*"]
CORS_ALLOW_METHODS: list[str] = ["*"]
CORS_ALLOW_HEADERS: list[str] = ["*"]
CORS_ALLOW_CREDENTIALS: bool = True

# ── API metadata ──────────────────────────────────────────────────────────────
API_TITLE: str = "ML Prediction API"
API_VERSION: str = "1.0.0"
API_PREFIX: str = "/api/v1"

# ── Messages (no magic strings scattered in code) ────────────────────────────
MSG_UNSUPPORTED_MODEL_FILE: str = (
    "Unsupported model file. Only {extensions} are accepted."
)
MSG_UNSUPPORTED_DATA_FILE: str = (
    "Unsupported data file. Only {extensions} are accepted."
)
MSG_NO_DATA: str = "No data available for prediction."

MSG_DEFAULT_MODEL_NOT_FOUND: str = (
    "Default model not found at {path}. "
    "Please upload a model file or place the default model in the ./models directory."
)
MSG_PREDICTION_SUCCESS: str = "Prediction completed successfully."
MSG_MODEL_LOAD_ERROR: str = "Failed to load model: {detail}"
MSG_PREDICTION_ERROR: str = "Error during prediction: {detail}"
MSG_DATA_PARSE_ERROR: str = "Failed to parse data: {detail}"

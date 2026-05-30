"""
* ModelLoader       — абстрактный базовый класс (ISP / DIP)
* PickleModelLoader — конкретная реализация для файлов .pkl
* ModelService      — оркестрирует выбор загрузчика и путь к файлу
"""

from __future__ import annotations

import io
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.config import (
    DEFAULT_MODEL_DIR,
    DEFAULT_MODEL_FILENAME,
    MSG_DEFAULT_MODEL_NOT_FOUND,
    MSG_MODEL_LOAD_ERROR,
    MSG_NO_LOADER,
    SUPPORTED_MODEL_EXTENSIONS,
)
from app.utils.file_validator import FileValidator


# ── Абстрактный загрузчик ─────────────────────────────────────────────────────

class ModelLoader(ABC):
    """Загружает модель машинного обучения из бинарного потока."""

    @abstractmethod
    def load(self, stream: io.IOBase) -> Any:
        """Десериализовать и вернуть объект модели."""


# ── Конкретные загрузчики ─────────────────────────────────────────────────────

class PickleModelLoader(ModelLoader):
    """Десериализует модель из pickle-формата (.pkl)."""

    def load(self, stream: io.IOBase) -> Any:
        # nosec — вызывающий код контролирует источник данных
        return pickle.load(stream)


# ── Сервис ────────────────────────────────────────────────────────────────────

class ModelService:
    """
    Отвечает за:
      — выбор правильного загрузчика по расширению файла;
      — загрузку модели из загруженных байт или из пути по умолчанию.
    """

    # Реестр расширений → классы загрузчиков.
    # Чтобы добавить новый формат — добавить одну строку здесь.
    _loader_registry: dict[str, type[ModelLoader]] = {
        ".pkl": PickleModelLoader,
    }

    def __init__(self) -> None:
        self._validator = FileValidator(SUPPORTED_MODEL_EXTENSIONS)

    # ── Публичный интерфейс ───────────────────────────────────────────────────

    def is_supported(self, filename: str) -> bool:
        """Проверить, поддерживается ли расширение файла."""
        return self._validator.is_supported(filename)

    def show_supported_extensions(self) -> str:
        """Вернуть строку допустимых расширений для вывода пользователю."""
        return self._validator.show_supported_extensions()

    def load_from_bytes(self, filename: str, model_bytes: bytes) -> Any:
        """Загрузить модель из сырых байт (загруженный файл)."""
        loader = self._resolve_loader(filename)
        try:
            return loader.load(io.BytesIO(model_bytes))
        except Exception as exc:
            raise ValueError(
                MSG_MODEL_LOAD_ERROR.format(detail=str(exc))
            ) from exc

    def load_default(self) -> Any:
        """Загрузить модель по умолчанию из директории ./models."""
        default_path: Path = DEFAULT_MODEL_DIR / DEFAULT_MODEL_FILENAME
        if not default_path.exists():
            raise FileNotFoundError(
                MSG_DEFAULT_MODEL_NOT_FOUND.format(path=default_path)
            )
        loader = self._resolve_loader(DEFAULT_MODEL_FILENAME)
        try:
            with default_path.open("rb") as fh:
                return loader.load(fh)
        except Exception as exc:
            raise ValueError(
                MSG_MODEL_LOAD_ERROR.format(detail=str(exc))
            ) from exc

    # ── Приватные вспомогательные методы ─────────────────────────────────────

    def _resolve_loader(self, filename: str) -> ModelLoader:
        """Вернуть экземпляр загрузчика для данного расширения файла."""
        ext = Path(filename).suffix.lower()
        loader_class = self._loader_registry.get(ext)
        if loader_class is None:
            raise KeyError(MSG_NO_LOADER.format(ext=ext))
        return loader_class()

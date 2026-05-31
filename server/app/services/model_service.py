"""
Сервис для загрузки моделей машинного обучения.

Реализованы:
    - загрузка из pickle-файла (.pkl)
    - загрузка модели по умолчанию из папки ./models

Добавление нового формата (например, joblib):
    1. Создать новый подкласс ModelLoader.
    2. Добавить запись в _loader_registry.
"""

from __future__ import annotations

import io
import logging
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

# Настройка логгера
logger = logging.getLogger("mortgage-api")

# Абстрактный загрузчик


class ModelLoader(ABC):
    """Абстрактный базовый класс для всех загрузчиков моделей."""

    @abstractmethod
    def load(self, stream: io.IOBase) -> Any:
        """Десериализация модели из бинарного потока."""


# Конкретные загрузчики


class PickleModelLoader(ModelLoader):
    """Загрузчик моделей из pickle-файлов (.pkl)."""

    def load(self, stream: io.IOBase) -> Any:
        """
        Загрузка модели из потока pickle.

        Raises: может вызывать исключения pickle при повреждённом файле.
        """
        # nosec - вызывающий код контролирует источник данных
        return pickle.load(stream)


# Сервис


class ModelService:
    """
    Фасад для загрузки моделей: выбор загрузчика по расширению, загрузка из байтов или из файла по умолчанию.
    """

    # Реестр расширений -> классы загрузчиков
    # Чтобы добавить новый формат - добавить одну строку здесь
    _loader_registry: dict[str, type[ModelLoader]] = {
        ".pkl": PickleModelLoader,
    }

    def __init__(self) -> None:
        self._validator = FileValidator(SUPPORTED_MODEL_EXTENSIONS)

    # Публичный интерфейс

    def is_supported(self, filename: str) -> bool:
        """Проверка, поддерживается ли расширение файла модели."""
        supported = self._validator.is_supported(filename)
        logger.debug(f"Checking support for '{filename}': {supported}")
        return supported

    def show_supported_extensions(self) -> str:
        """Возврат строки допустимых расширений для вывода пользователю."""
        extensions = self._validator.show_supported_extensions()
        logger.debug(f"Supported extensions: {extensions}")
        return extensions

    def load_from_bytes(self, filename: str, model_bytes: bytes) -> Any:
        """Загрузка модели из сырых байт (загруженный файл)."""
        logger.info(f"Loading model from bytes: {filename}")
        loader = self._resolve_loader(filename)
        try:
            model = loader.load(io.BytesIO(model_bytes))
            logger.info(f"Successfully loaded model from bytes: {filename}")
            return model
        except Exception as exc:
            logger.error(f"Failed to load model from bytes {filename}: {exc}")
            raise ValueError(MSG_MODEL_LOAD_ERROR.format(detail=str(exc))) from exc

    def load_default(self) -> Any:
        """Загрузка модели по умолчанию из директории ./models."""
        default_path: Path = DEFAULT_MODEL_DIR / DEFAULT_MODEL_FILENAME
        logger.info(f"Loading default model from {default_path}")
        if not default_path.exists():
            logger.error(f"Default model not found at {default_path}")
            raise FileNotFoundError(MSG_DEFAULT_MODEL_NOT_FOUND.format(path=default_path))
        loader = self._resolve_loader(DEFAULT_MODEL_FILENAME)
        try:
            with default_path.open("rb") as fh:
                model = loader.load(fh)
                logger.info(f"Default model loaded from {default_path}")
                return model
        except Exception as exc:
            logger.error(f"Failed to load default model from {default_path}: {exc}")
            raise ValueError(MSG_MODEL_LOAD_ERROR.format(detail=str(exc))) from exc

    # Приватные вспомогательные методы

    def _resolve_loader(self, filename: str) -> ModelLoader:
        """Возврат экземпляра загрузчика для данного расширения файла."""
        ext = Path(filename).suffix.lower()
        logger.debug(f"Resolving loader for extension '{ext}' from file '{filename}'")
        loader_class = self._loader_registry.get(ext)
        if loader_class is None:
            logger.error(f"No loader registered for extension '{ext}'")
            raise KeyError(MSG_NO_LOADER.format(ext=ext))
        logger.debug(f"Using loader {loader_class.__name__} for extension '{ext}'")
        return loader_class()

"""
Model loading layer.

Design decisions
────────────────
* ModelLoader  — abstract base (Interface Segregation / Dependency Inversion)
* PickleModelLoader — concrete implementation for .pkl files
* ModelService  — orchestrates "which loader?" and "where is the file?"

Adding support for a new format (e.g. joblib, ONNX) requires only:
  1. A new ModelLoader subclass.
  2. Registering it in ModelService._loader_registry.
  Nothing else changes (Open/Closed Principle).
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
    SUPPORTED_MODEL_EXTENSIONS,
)
from app.utils.file_validator import FileValidator


# ── Abstract loader ────────────────────────────────────────────────────────────

class ModelLoader(ABC):
    """Load a machine-learning model from a binary stream."""

    @abstractmethod
    def load(self, stream: io.IOBase) -> Any:
        """Deserialise and return the model object."""


# ── Concrete loaders ───────────────────────────────────────────────────────────

class PickleModelLoader(ModelLoader):
    """Deserialise a pickle-serialised model."""

    def load(self, stream: io.IOBase) -> Any:  # noqa: D102
        return pickle.load(stream)  # nosec — caller controls the source


# ── Service ────────────────────────────────────────────────────────────────────

class ModelService:
    """
    Responsible for:
      - Choosing the correct loader for a given file extension.
      - Loading models from uploaded bytes or from the default path.
    """

    # Map extension → loader class.  Extend here to support more formats.
    _loader_registry: dict[str, type[ModelLoader]] = {
        ".pkl": PickleModelLoader,
    }

    def __init__(self) -> None:
        self._validator = FileValidator(SUPPORTED_MODEL_EXTENSIONS)

    # ── Public API ─────────────────────────────────────────────────────────────

    def is_supported(self, filename: str) -> bool:
        return self._validator.is_supported(filename)

    def supported_extensions_display(self) -> str:
        return self._validator.extensions_display()

    def load_from_bytes(self, filename: str, model_bytes: bytes) -> Any:
        """Load a model from raw bytes (uploaded file)."""
        loader = self._resolve_loader(filename)
        try:
            return loader.load(io.BytesIO(model_bytes))
        except Exception as exc:
            raise ValueError(
                MSG_MODEL_LOAD_ERROR.format(detail=str(exc))
            ) from exc

    def load_default(self) -> Any:
        """Load the default model shipped with the backend."""
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

    # ── Private helpers ────────────────────────────────────────────────────────

    def _resolve_loader(self, filename: str) -> ModelLoader:
        ext = Path(filename).suffix.lower()
        loader_class = self._loader_registry.get(ext)
        if loader_class is None:
            raise KeyError(f"No loader registered for extension '{ext}'.")
        return loader_class()

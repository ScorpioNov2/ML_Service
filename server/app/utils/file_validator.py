"""
Валидатор расширений файлов.

Проверяет, соответствует ли расширение файла допустимому списку.
Закрыт для изменений (OCP): не нужно менять класс при добавлении форматов.
"""

from pathlib import Path
from typing import Sequence


class FileValidator:
    """Проверка имён файлов по списку допустимых расширений."""

    def __init__(self, supported_extensions: Sequence[str]) -> None:
        # Приводим к нижнему регистру для регистронезависимого сравнения
        self._supported: frozenset[str] = frozenset(ext.lower() for ext in supported_extensions)

    # Публичный интерфейс

    def is_supported(self, filename: str) -> bool:
        """Возврат True, если расширение файла допустимо."""
        return self._get_extension(filename) in self._supported

    def extensions_display(self) -> str:
        """Строка допустимых расширений для вывода пользователю (напр. '.pkl, .joblib')."""
        return ", ".join(sorted(self._supported))

    # Приватные вспомогательные методы

    @staticmethod
    def _get_extension(filename: str) -> str:
        """Возврат расширения файла (в нижнем регистре)."""
        return Path(filename).suffix.lower()

"""
FileValidator — единственная ответственность: проверка расширений файлов.

Зависит от внедрённого списка допустимых расширений, поэтому:
  - Закрыт для изменений (OCP): не нужно менять класс при добавлении форматов.
  - Открыт для расширения: передайте другой список — и тот же класс обработает
    любой домен (модели, данные, изображения и т.д.).
"""

from pathlib import Path
from typing import Sequence


class FileValidator:
    """Проверяет имена файлов по настраиваемому списку допустимых расширений."""

    def __init__(self, supported_extensions: Sequence[str]) -> None:
        # Приводим к нижнему регистру для регистронезависимого сравнения
        self._supported: frozenset[str] = frozenset(ext.lower() for ext in supported_extensions)

    # ── Публичный интерфейс ───────────────────────────────────────────────────

    def is_supported(self, filename: str) -> bool:
        """Вернуть True, если расширение filename входит в список допустимых."""
        return self._get_extension(filename) in self._supported

    def extensions_display(self) -> str:
        """Строка допустимых расширений для вывода пользователю (напр. '.pkl, .joblib')."""
        return ", ".join(sorted(self._supported))

    # ── Приватные вспомогательные методы ─────────────────────────────────────

    @staticmethod
    def _get_extension(filename: str) -> str:
        return Path(filename).suffix.lower()

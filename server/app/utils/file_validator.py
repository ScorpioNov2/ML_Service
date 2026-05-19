"""
FileValidator — Single Responsibility: validate file extensions.

Depends on an injected allow-list so it is closed for modification but open
for extension (OCP): pass a different list and the same class handles any
domain.
"""

from pathlib import Path
from typing import Sequence


class FileValidator:
    """Validates file names against a configurable list of extensions."""

    def __init__(self, supported_extensions: Sequence[str]) -> None:
        # Normalise to lower-case so comparisons are case-insensitive.
        self._supported: frozenset[str] = frozenset(
            ext.lower() for ext in supported_extensions
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def is_supported(self, filename: str) -> bool:
        """Return True when *filename*'s extension is in the allow-list."""
        return self._get_extension(filename) in self._supported

    def extensions_display(self) -> str:
        """Human-readable string of allowed extensions (e.g. '.pkl, .joblib')."""
        return ", ".join(sorted(self._supported))

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _get_extension(filename: str) -> str:
        return Path(filename).suffix.lower()

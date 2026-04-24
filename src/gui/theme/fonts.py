"""Регистрация шрифтов (если лежат в assets/fonts)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFontDatabase


def register_bundled_fonts() -> None:
    fonts_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    if not fonts_dir.exists():
        return
    for file in fonts_dir.glob("*.[to][tf][tf]"):
        QFontDatabase.addApplicationFont(str(file))

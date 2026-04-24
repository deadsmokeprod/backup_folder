"""Загрузка QSS-файлов темы."""
from __future__ import annotations

from pathlib import Path


def load_qss(name: str = "dark_anime.qss") -> str:
    path = Path(__file__).resolve().parent / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""

"""Тёмная палитра в аниме-стиле."""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette


# --- основные цвета ---
BG_DEEP = "#0F1020"          # фон окна
BG_PANEL = "#1A1B30"         # панели/карточки
BG_ELEVATED = "#22243F"      # поля ввода, выделенные строки
BORDER = "#2A2B45"           # тонкие линии

TEXT_PRIMARY = "#E6E8FF"
TEXT_SECONDARY = "#A0A3C5"
TEXT_DISABLED = "#5A5D7A"

ACCENT_PINK = "#FF6FA3"      # главный акцент
ACCENT_BLUE = "#8AB4FF"      # вторичный акцент
ACCENT_PURPLE = "#B88CFF"

SUCCESS = "#7CE0B3"
WARN = "#FFD166"
ERROR = "#FF8AA0"


def apply_dark_anime_palette(app) -> None:
    p = QPalette()
    p.setColor(QPalette.Window, QColor(BG_DEEP))
    p.setColor(QPalette.WindowText, QColor(TEXT_PRIMARY))
    p.setColor(QPalette.Base, QColor(BG_ELEVATED))
    p.setColor(QPalette.AlternateBase, QColor(BG_PANEL))
    p.setColor(QPalette.ToolTipBase, QColor(BG_PANEL))
    p.setColor(QPalette.ToolTipText, QColor(TEXT_PRIMARY))
    p.setColor(QPalette.Text, QColor(TEXT_PRIMARY))
    p.setColor(QPalette.Button, QColor(BG_PANEL))
    p.setColor(QPalette.ButtonText, QColor(TEXT_PRIMARY))
    p.setColor(QPalette.BrightText, QColor(ACCENT_PINK))
    p.setColor(QPalette.Highlight, QColor(ACCENT_PINK))
    p.setColor(QPalette.HighlightedText, QColor("#1A0B13"))
    p.setColor(QPalette.Link, QColor(ACCENT_BLUE))
    p.setColor(QPalette.PlaceholderText, QColor(TEXT_SECONDARY))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor(TEXT_DISABLED))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(TEXT_DISABLED))
    p.setColor(QPalette.Disabled, QPalette.WindowText, QColor(TEXT_DISABLED))
    app.setPalette(p)

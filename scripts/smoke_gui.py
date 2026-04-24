"""Запускает GUI, показывает окно на 1 секунду и закрывает — для smoke-проверки."""
from __future__ import annotations

import sys

from PySide6.QtCore import QLocale, QTimer
from PySide6.QtWidgets import QApplication

from src.core import db
from src.gui.main_window import MainWindow
from src.gui.theme.fonts import register_bundled_fonts
from src.gui.theme.palette import apply_dark_anime_palette
from src.gui.theme.qss_loader import load_qss


def main() -> int:
    db.init_db()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    QLocale.setDefault(QLocale(QLocale.Russian, QLocale.Russia))
    register_bundled_fonts()
    apply_dark_anime_palette(app)
    app.setStyleSheet(load_qss())
    window = MainWindow()
    window.show()
    QTimer.singleShot(1200, app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

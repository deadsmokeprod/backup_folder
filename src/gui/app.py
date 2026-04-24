"""Точка входа GUI."""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from src.core import db, events
from src.core.paths import gui_log_path
from src.gui.main_window import MainWindow
from src.gui.theme.fonts import register_bundled_fonts
from src.gui.theme.palette import apply_dark_anime_palette
from src.gui.theme.qss_loader import load_qss


def _configure_logging() -> None:
    handler = RotatingFileHandler(
        str(gui_log_path()),
        maxBytes=1_000_000,
        backupCount=2,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)


def main() -> int:
    _configure_logging()
    db.init_db()
    events.info("gui_started")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("BackupBots")
    QLocale.setDefault(QLocale(QLocale.Russian, QLocale.Russia))

    register_bundled_fonts()
    apply_dark_anime_palette(app)
    qss = load_qss()
    if qss:
        app.setStyleSheet(qss)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

"""Индикатор заполненности диска-приёмника."""
from __future__ import annotations

from pathlib import Path

import psutil
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from src.gui.i18n.strings import S


def _human_size(num: float) -> str:
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} ПБ"


class DiskBar(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._info = QLabel(S.LBL_DISK_UNKNOWN)
        self._info.setObjectName("Hint")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._bar)
        layout.addWidget(self._info)

    def update_for(self, destination: str | None) -> None:
        if not destination:
            self._bar.setValue(0)
            self._bar.setFormat("—")
            self._info.setText(S.LBL_DISK_UNKNOWN)
            return
        path = destination
        if not Path(path).exists():
            # psutil ожидает существующий путь; возьмём корень диска
            try:
                path = Path(destination).anchor or destination
            except (OSError, ValueError):
                pass
        try:
            usage = psutil.disk_usage(path)
        except OSError:
            self._bar.setValue(0)
            self._bar.setFormat("—")
            self._info.setText(S.LBL_DISK_UNKNOWN)
            return
        percent = int(usage.percent)
        self._bar.setValue(percent)
        self._bar.setFormat(f"{percent}%")
        self._info.setText(
            S.LBL_DISK_FREE.format(
                free=_human_size(usage.free),
                total=_human_size(usage.total),
            )
        )

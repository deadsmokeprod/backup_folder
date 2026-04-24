"""Журнал событий: красивый список с понятными формулировками + скачивание лога."""
from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.core import events
from src.core.event_codes import LEVEL_ERROR, LEVEL_INFO, LEVEL_WARNING
from src.gui.i18n.strings import S
from src.gui.widgets.hint_label import attach_hint


_LEVEL_ICON = {
    LEVEL_ERROR: ("●", QColor("#FF8AA0")),
    LEVEL_WARNING: ("●", QColor("#FFD166")),
    LEVEL_INFO: ("●", QColor("#7CE0B3")),
}


class EventLogDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(S.DLG_LOG_TITLE)
        self.setMinimumSize(880, 540)

        self._filter_level: str | None = None  # None = все

        # --- верхняя панель фильтров ---
        filter_card = QFrame()
        filter_card.setObjectName("Card")
        flayout = QHBoxLayout(filter_card)
        flayout.setContentsMargins(14, 10, 14, 10)
        flayout.setSpacing(10)

        self._all_btn = QPushButton(S.LOG_FILTER_ALL)
        self._warn_btn = QPushButton(S.LOG_FILTER_WARNINGS)
        self._err_btn = QPushButton(S.LOG_FILTER_ERRORS)
        self._group = QButtonGroup(self)
        for btn in (self._all_btn, self._warn_btn, self._err_btn):
            btn.setCheckable(True)
            btn.setObjectName("Secondary")
            self._group.addButton(btn)
            flayout.addWidget(btn)
        self._all_btn.setChecked(True)
        self._all_btn.clicked.connect(lambda: self._apply_filter(None))
        self._warn_btn.clicked.connect(lambda: self._apply_filter("WARN"))
        self._err_btn.clicked.connect(lambda: self._apply_filter(LEVEL_ERROR))

        flayout.addStretch(1)

        self._download_btn = QPushButton(S.BTN_LOG_DOWNLOAD)
        self._download_btn.setObjectName("Primary")
        attach_hint(self._download_btn, "btn_log_download")
        self._download_btn.clicked.connect(self._download_zip)
        flayout.addWidget(self._download_btn)

        self._clear_btn = QPushButton(S.BTN_LOG_CLEAR)
        self._clear_btn.setObjectName("Danger")
        attach_hint(self._clear_btn, "btn_log_clear")
        self._clear_btn.clicked.connect(self._clear)
        flayout.addWidget(self._clear_btn)

        # --- таблица ---
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels([S.LOG_COL_LEVEL, S.LOG_COL_TIME, S.LOG_COL_MESSAGE])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.doubleClicked.connect(lambda *_: self._show_details())

        # --- пустое состояние ---
        self._empty = QLabel(S.LOG_EMPTY)
        self._empty.setObjectName("Hint")
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(filter_card)
        layout.addWidget(self._table, 1)
        layout.addWidget(self._empty, 1)

        self._timer = QTimer(self)
        self._timer.setInterval(3000)
        self._timer.timeout.connect(self._reload)
        self._timer.start()
        self._reload()

    # --- логика ---
    def _apply_filter(self, level: str | None) -> None:
        self._filter_level = level
        self._reload()

    def _reload(self) -> None:
        all_events = events.read_events(limit=1000)
        if self._filter_level == LEVEL_ERROR:
            shown = [e for e in all_events if e.get("level") == LEVEL_ERROR]
        elif self._filter_level == "WARN":
            shown = [
                e for e in all_events
                if e.get("level") in (LEVEL_ERROR, LEVEL_WARNING)
            ]
        else:
            shown = all_events

        self._table.setRowCount(len(shown))
        for row, ev in enumerate(shown):
            level = ev.get("level", LEVEL_INFO)
            icon, color = _LEVEL_ICON.get(level, _LEVEL_ICON[LEVEL_INFO])
            icon_item = QTableWidgetItem(icon)
            icon_item.setForeground(QBrush(color))
            icon_item.setTextAlignment(Qt.AlignCenter)

            ts_text = _format_ts(ev.get("ts", ""))
            ts_item = QTableWidgetItem(ts_text)

            msg_item = QTableWidgetItem(ev.get("message", ""))
            msg_item.setData(Qt.UserRole, ev)

            self._table.setItem(row, 0, icon_item)
            self._table.setItem(row, 1, ts_item)
            self._table.setItem(row, 2, msg_item)

        self._table.setVisible(bool(shown))
        self._empty.setVisible(not shown)

    def _show_details(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        item = self._table.item(row, 2)
        if item is None:
            return
        ev = item.data(Qt.UserRole) or {}
        lines = [
            f"Время: {_format_ts(ev.get('ts', ''))}",
            f"Уровень: {ev.get('level', '')}",
            f"Код: {ev.get('code', '')}",
            "",
            ev.get("message", ""),
        ]
        fields = ev.get("fields") or {}
        if fields:
            lines.append("")
            lines.append("Подробности:")
            for k, v in fields.items():
                lines.append(f"  • {k}: {v}")
        QMessageBox.information(self, S.DLG_LOG_TITLE, "\n".join(lines))

    def _download_zip(self) -> None:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"backupbots-log-{ts}.zip"
        suggested = str(Path.home() / "Desktop" / default_name)
        path, _ = QFileDialog.getSaveFileName(
            self, S.BTN_LOG_DOWNLOAD, suggested, "ZIP-архив (*.zip)"
        )
        if not path:
            return
        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
                for src in events.all_log_files():
                    try:
                        z.write(str(src), arcname=src.name)
                    except OSError:
                        continue
        except OSError as exc:
            QMessageBox.critical(self, S.MSG_ERROR, str(exc))
            return
        QMessageBox.information(self, S.MSG_OK, S.MSG_LOG_DOWNLOADED.format(path=path))

    def _clear(self) -> None:
        reply = QMessageBox.question(self, S.BTN_LOG_CLEAR, S.MSG_CONFIRM_LOG_CLEAR)
        if reply != QMessageBox.Yes:
            return
        events.clear_events()
        from ...core.paths import logs_dir

        for f in logs_dir().glob("*.log*"):
            try:
                f.unlink()
            except OSError:
                pass
        self._reload()
        QMessageBox.information(self, S.MSG_OK, S.MSG_LOG_CLEARED)


def _format_ts(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
    except (ValueError, TypeError):
        return iso or ""
    return dt.strftime("%d.%m.%Y %H:%M:%S")

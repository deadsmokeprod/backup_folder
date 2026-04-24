"""Список веток бэкапа: размер, период, пауза."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ...core import config as cfg
from ...core import db, ipc
from ...core.models import BackupJob
from ..i18n.strings import S
from ..widgets.hint_label import attach_hint


def format_human_size(num: float) -> str:
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} ПБ"


def _format_period(oldest, newest) -> str:
    if not oldest or not newest:
        return "—"
    return f"{oldest.strftime('%d.%m.%Y %H:%M')} → {newest.strftime('%d.%m.%Y %H:%M')}"


class BackupListDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(S.DLG_LIST_TITLE)
        self.setMinimumSize(980, 480)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            [
                S.COL_NAME,
                S.COL_SOURCE,
                S.COL_LAST,
                S.COL_PERIOD,
                S.COL_SIZE,
                S.COL_STATE,
                "",
            ]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        self._table.doubleClicked.connect(lambda *_: self._open_detail())

        self._open_btn = QPushButton(S.BTN_OPEN_DETAIL)
        self._open_btn.setObjectName("Secondary")
        attach_hint(self._open_btn, "btn_open_detail")
        self._open_btn.clicked.connect(self._open_detail)

        self._edit_btn = QPushButton(S.BTN_EDIT)
        self._edit_btn.clicked.connect(self._edit_selected)

        self._run_btn = QPushButton(S.BTN_RUN_NOW)
        attach_hint(self._run_btn, "btn_run_now")
        self._run_btn.clicked.connect(self._run_now)

        self._pause_btn = QPushButton(S.BTN_PAUSE)
        attach_hint(self._pause_btn, "paused")
        self._pause_btn.clicked.connect(self._toggle_pause)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self._pause_btn)
        btn_row.addWidget(self._run_btn)
        btn_row.addWidget(self._edit_btn)
        btn_row.addWidget(self._open_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(self._table)
        layout.addLayout(btn_row)

        self._jobs: list[BackupJob] = []
        self._reload()

    def _reload(self) -> None:
        config = cfg.load_config()
        self._jobs = list(config.jobs)
        self._table.setRowCount(len(self._jobs))
        for row, job in enumerate(self._jobs):
            stats = db.get_job_stats(job.id)
            last = db.get_last_snapshot(job.id)
            last_str = last.created_at.strftime("%d.%m.%Y %H:%M") if last else "—"
            period = _format_period(stats.oldest_at, stats.newest_at)
            size = format_human_size(stats.total_size_bytes)
            state = S.STATE_PAUSED if job.paused else S.STATE_ACTIVE

            items = [
                QTableWidgetItem(job.name),
                QTableWidgetItem(job.source),
                QTableWidgetItem(last_str),
                QTableWidgetItem(period),
                QTableWidgetItem(size),
                QTableWidgetItem(state),
                QTableWidgetItem(f"{stats.snapshot_count} шт."),
            ]
            items[4].setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            items[0].setData(Qt.UserRole, job.id)
            for col, item in enumerate(items):
                self._table.setItem(row, col, item)
        self._table.resizeColumnsToContents()
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self._update_button_state()
        self._table.selectionModel().selectionChanged.connect(
            lambda *_: self._update_button_state()
        )

    def _selected_job(self) -> Optional[BackupJob]:
        row = self._table.currentRow()
        if row < 0 or row >= len(self._jobs):
            return None
        return self._jobs[row]

    def _update_button_state(self) -> None:
        job = self._selected_job()
        has = job is not None
        for btn in (self._open_btn, self._edit_btn, self._run_btn, self._pause_btn):
            btn.setEnabled(has)
        if job is not None:
            self._pause_btn.setText(S.BTN_RESUME if job.paused else S.BTN_PAUSE)

    def _open_detail(self) -> None:
        job = self._selected_job()
        if job is None:
            return
        from .backup_detail import BackupDetailDialog

        dlg = BackupDetailDialog(job, self)
        dlg.exec()
        self._reload()

    def _edit_selected(self) -> None:
        job = self._selected_job()
        if job is None:
            return
        from .add_backup import AddBackupDialog

        dlg = AddBackupDialog(job=job, parent=self)
        result = dlg.exec()
        if result == 2 and dlg.deleted:
            dlg.delete_from_config()
        self._reload()

    def _run_now(self) -> None:
        job = self._selected_job()
        if job is None:
            return
        resp = ipc.send_command("run_now", job_id=job.id)
        if resp is None:
            QMessageBox.information(
                self,
                S.MSG_OK,
                "Служба не отвечает — запуск выполнит при следующем тике.",
            )
        else:
            QMessageBox.information(self, S.MSG_OK, "Запуск отправлен службе.")

    def _toggle_pause(self) -> None:
        job = self._selected_job()
        if job is None:
            return
        new_paused = not job.paused
        resp = ipc.send_command("set_pause", job_id=job.id, paused=new_paused)
        if resp is None:
            # служба недоступна — пишем прямо в конфиг
            config = cfg.load_config()
            for j in config.jobs:
                if j.id == job.id:
                    j.paused = new_paused
                    break
            cfg.save_config(config)
        self._reload()

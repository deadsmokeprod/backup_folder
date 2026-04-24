"""Детали одной ветки: список снимков."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

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

from ...core import db
from ...core.models import BackupJob
from ..i18n.strings import S
from ..widgets.hint_label import attach_hint
from .backup_list import format_human_size


class BackupDetailDialog(QDialog):
    def __init__(self, job: BackupJob, parent=None) -> None:
        super().__init__(parent)
        self._job = job
        self.setWindowTitle(S.DLG_DETAIL_TITLE.format(name=job.name))
        self.setMinimumSize(780, 420)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(
            [S.COL_SNAPSHOT_DATE, S.COL_SNAPSHOT_SIZE, S.COL_SNAPSHOT_PATH]
        )
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        self._open_btn = QPushButton(S.BTN_OPEN_EXPLORER)
        self._open_btn.setObjectName("Secondary")
        attach_hint(self._open_btn, "btn_open_detail")
        self._open_btn.clicked.connect(self._open_in_explorer)

        self._del_btn = QPushButton(S.BTN_DELETE_SNAPSHOT)
        self._del_btn.setObjectName("Danger")
        attach_hint(self._del_btn, "btn_delete_snapshot")
        self._del_btn.clicked.connect(self._delete_selected)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self._del_btn)
        btn_row.addWidget(self._open_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(self._table)
        layout.addLayout(btn_row)

        self._reload()

    def _reload(self) -> None:
        snapshots = db.list_snapshots(self._job.id)
        self._table.setRowCount(len(snapshots))
        for row, snap in enumerate(snapshots):
            dt = snap.created_at.strftime("%d.%m.%Y %H:%M:%S")
            item_dt = QTableWidgetItem(dt)
            item_dt.setData(Qt.UserRole, snap.id)
            item_dt.setData(Qt.UserRole + 1, snap.path)
            item_size = QTableWidgetItem(format_human_size(snap.size_bytes))
            item_size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_path = QTableWidgetItem(snap.path)
            self._table.setItem(row, 0, item_dt)
            self._table.setItem(row, 1, item_size)
            self._table.setItem(row, 2, item_path)

    def _selected_snapshot(self) -> tuple[int, str] | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        if item is None:
            return None
        snap_id = int(item.data(Qt.UserRole))
        path = str(item.data(Qt.UserRole + 1))
        return snap_id, path

    def _open_in_explorer(self) -> None:
        picked = self._selected_snapshot()
        if picked is None:
            return
        _, path = picked
        if Path(path).exists():
            os.startfile(path)  # noqa: S606
        else:
            QMessageBox.warning(self, S.MSG_ERROR, f"Папка не найдена: {path}")

    def _delete_selected(self) -> None:
        picked = self._selected_snapshot()
        if picked is None:
            return
        snap_id, path = picked
        reply = QMessageBox.question(
            self,
            S.BTN_DELETE_SNAPSHOT,
            S.MSG_CONFIRM_DELETE_SNAPSHOT.format(path=path),
        )
        if reply != QMessageBox.Yes:
            return
        p = Path(path)
        if p.exists():
            try:
                shutil.rmtree(p)
            except OSError as exc:
                QMessageBox.critical(self, S.MSG_ERROR, str(exc))
                return
        db.delete_snapshot(snap_id)
        self._reload()

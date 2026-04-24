"""Диалог глобальных настроек."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.core import config as cfg
from src.gui.i18n.strings import S
from src.gui.widgets.disk_bar import DiskBar
from src.gui.widgets.hint_label import LabelWithHint
from src.gui.widgets.schedule_form import ScheduleForm


class GlobalSettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(S.DLG_GLOBAL_TITLE)
        self.setMinimumWidth(620)

        self._config = cfg.load_config()

        # --- карточка «диск» ---
        disk_card = QFrame()
        disk_card.setObjectName("Card")
        disk_layout = QVBoxLayout(disk_card)
        disk_layout.setContentsMargins(16, 12, 16, 12)
        title = QLabel(S.LBL_DISK_USAGE)
        title.setObjectName("H2")
        self._disk_bar = DiskBar()
        disk_layout.addWidget(title)
        disk_layout.addWidget(self._disk_bar)

        # --- карточка «форма» ---
        form_card = QFrame()
        form_card.setObjectName("Card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(16, 12, 16, 12)

        self._form = ScheduleForm(show_default_destination=True)

        # кнопка «Обзор» рядом с дефолтной папкой
        browse_container = QHBoxLayout()
        browse_container.setContentsMargins(0, 0, 0, 0)
        browse_btn = QPushButton(S.BTN_BROWSE)
        browse_btn.clicked.connect(self._choose_default_dest)
        browse_container.addWidget(browse_btn)
        browse_container.addStretch(1)

        form_layout.addWidget(self._form)
        form_layout.addLayout(browse_container)

        # --- кнопки диалога ---
        buttons = QDialogButtonBox()
        save_btn = buttons.addButton(S.BTN_SAVE, QDialogButtonBox.AcceptRole)
        save_btn.setObjectName("Primary")
        cancel_btn = buttons.addButton(S.BTN_CANCEL, QDialogButtonBox.RejectRole)
        cancel_btn.setObjectName("Secondary")
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        root.addWidget(disk_card)
        root.addWidget(form_card)
        root.addWidget(buttons)

        self._form.load(self._config.globals_)
        self._disk_bar.update_for(self._config.globals_.default_destination)
        self._form.default_destination.textChanged.connect(self._disk_bar.update_for)

    def _choose_default_dest(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, S.LBL_DEFAULT_DEST, self._form.default_destination.text()
        )
        if path:
            self._form.default_destination.setText(path)

    def _on_save(self) -> None:
        new_settings = self._form.dump(self._config.globals_)
        self._config.globals_ = new_settings
        try:
            cfg.save_config(self._config)
        except OSError as exc:
            QMessageBox.critical(self, S.MSG_ERROR, str(exc))
            return
        self.accept()

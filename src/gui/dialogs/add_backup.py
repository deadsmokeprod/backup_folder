"""Диалог добавления/редактирования ветки бэкапа."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.core import config as cfg
from src.core.models import BackupJob, GlobalSettings
from src.gui.i18n.strings import S
from src.gui.widgets.hint_label import LabelWithHint, attach_hint
from src.gui.widgets.schedule_form import ScheduleForm


class AddBackupDialog(QDialog):
    def __init__(self, job: Optional[BackupJob] = None, parent=None) -> None:
        super().__init__(parent)
        self._editing = job is not None
        self.setWindowTitle(S.DLG_EDIT_TITLE if self._editing else S.DLG_ADD_TITLE)
        self.setMinimumWidth(640)

        self._config = cfg.load_config()
        self._job = job.model_copy(deep=True) if job else BackupJob(name="", source="")

        # --- основные поля ---
        self.name_edit = QLineEdit(self._job.name)
        attach_hint(self.name_edit, "name")
        self.source_edit = QLineEdit(self._job.source)
        attach_hint(self.source_edit, "source")
        self.dest_edit = QLineEdit(self._job.destination or "")
        self.dest_edit.setPlaceholderText(S.LBL_DESTINATION_PLACEHOLDER)
        attach_hint(self.dest_edit, "destination")

        src_btn = QPushButton(S.BTN_BROWSE)
        src_btn.clicked.connect(self._choose_source)
        dst_btn = QPushButton(S.BTN_BROWSE)
        dst_btn.clicked.connect(self._choose_dest)

        def pair(edit, btn):
            w = QHBoxLayout()
            w.setContentsMargins(0, 0, 0, 0)
            w.addWidget(edit, 1)
            w.addWidget(btn)
            return w

        main_card = QFrame()
        main_card.setObjectName("Card")
        form = QFormLayout(main_card)
        form.setContentsMargins(16, 12, 16, 12)
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(12)
        form.addRow(LabelWithHint(S.LBL_NAME, "name"), self.name_edit)
        form.addRow(LabelWithHint(S.LBL_SOURCE, "source"), pair(self.source_edit, src_btn))
        form.addRow(LabelWithHint(S.LBL_DESTINATION, "destination"), pair(self.dest_edit, dst_btn))

        # --- чекбокс «использовать глобальные» + частные настройки ---
        self.use_global = QCheckBox(S.LBL_USE_GLOBAL)
        attach_hint(self.use_global, "use_global_settings")
        self.use_global.setChecked(self._job.use_global_settings)
        self.use_global.toggled.connect(self._toggle_overrides)

        self._overrides_card = QFrame()
        self._overrides_card.setObjectName("Card")
        ov_layout = QVBoxLayout(self._overrides_card)
        ov_layout.setContentsMargins(16, 12, 16, 12)
        from PySide6.QtWidgets import QLabel

        title = QLabel(S.LBL_OVERRIDES_GROUP)
        title.setObjectName("H2")
        self._overrides_form = ScheduleForm(show_default_destination=False)
        ov_layout.addWidget(title)
        ov_layout.addWidget(self._overrides_form)

        base_for_overrides = self._job.overrides or self._config.globals_.model_copy()
        self._overrides_form.load(base_for_overrides)
        self._overrides_card.setVisible(not self._job.use_global_settings)

        # --- кнопки ---
        buttons = QDialogButtonBox()
        save_btn = buttons.addButton(S.BTN_SAVE, QDialogButtonBox.AcceptRole)
        save_btn.setObjectName("Primary")
        cancel_btn = buttons.addButton(S.BTN_CANCEL, QDialogButtonBox.RejectRole)
        cancel_btn.setObjectName("Secondary")
        if self._editing:
            del_btn = buttons.addButton(S.BTN_DELETE, QDialogButtonBox.DestructiveRole)
            del_btn.setObjectName("Danger")
            del_btn.clicked.connect(self._on_delete)
            self._deleted = False
        else:
            self._deleted = False
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)
        root.addWidget(main_card)
        root.addWidget(self.use_global)
        root.addWidget(self._overrides_card)
        root.addWidget(buttons)

    # --- обработчики ---
    def _toggle_overrides(self, checked: bool) -> None:
        self._overrides_card.setVisible(not checked)

    def _choose_source(self) -> None:
        path = QFileDialog.getExistingDirectory(self, S.LBL_SOURCE, self.source_edit.text())
        if path:
            self.source_edit.setText(path)

    def _choose_dest(self) -> None:
        path = QFileDialog.getExistingDirectory(self, S.LBL_DESTINATION, self.dest_edit.text())
        if path:
            self.dest_edit.setText(path)

    def _on_delete(self) -> None:
        reply = QMessageBox.question(
            self,
            S.BTN_DELETE,
            S.MSG_CONFIRM_DELETE_JOB.format(name=self._job.name),
        )
        if reply != QMessageBox.Yes:
            return
        self._deleted = True
        self.done(2)  # нестандартный код «удалено»

    def _on_save(self) -> None:
        name = self.name_edit.text().strip()
        source = self.source_edit.text().strip()
        dest = self.dest_edit.text().strip()
        if not name:
            QMessageBox.warning(self, S.MSG_ERROR, S.MSG_NAME_REQUIRED)
            return
        if not source or not Path(source).is_dir():
            QMessageBox.warning(self, S.MSG_ERROR, S.MSG_SOURCE_MISSING)
            return
        if not dest and not self._config.globals_.default_destination:
            QMessageBox.warning(self, S.MSG_ERROR, S.MSG_DEST_REQUIRED)
            return

        self._job.name = name
        self._job.source = source
        self._job.destination = dest or None
        self._job.use_global_settings = bool(self.use_global.isChecked())
        if self._job.use_global_settings:
            self._job.overrides = None
        else:
            base = self._job.overrides or self._config.globals_.model_copy()
            self._job.overrides = self._overrides_form.dump(base)

        if self._editing:
            for i, existing in enumerate(self._config.jobs):
                if existing.id == self._job.id:
                    self._config.jobs[i] = self._job
                    break
            else:
                self._config.jobs.append(self._job)
        else:
            self._config.jobs.append(self._job)

        try:
            cfg.save_config(self._config)
        except OSError as exc:
            QMessageBox.critical(self, S.MSG_ERROR, str(exc))
            return
        self.accept()

    # --- внешний API ---
    @property
    def job(self) -> BackupJob:
        return self._job

    @property
    def deleted(self) -> bool:
        return self._deleted

    def delete_from_config(self) -> None:
        """Фактическое удаление — вызывается снаружи после кода 2."""
        self._config.jobs = [j for j in self._config.jobs if j.id != self._job.id]
        cfg.save_config(self._config)

"""Форма параметров расписания — используется и в глобальных настройках,
и в частных настройках ветки.
"""
from __future__ import annotations

from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QTimeEdit,
    QWidget,
)

from src.core.models import ALL_WEEKDAYS, DEFAULT_NAME_TEMPLATE, GlobalSettings
from src.gui.i18n.strings import S
from src.gui.widgets.hint_label import LabelWithHint, attach_hint


class ScheduleForm(QWidget):
    """Редактор полей GlobalSettings (кроме default_destination, чтобы диалоги сами решали)."""

    def __init__(self, show_default_destination: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._show_default_destination = show_default_destination

        self.interval = QSpinBox()
        self.interval.setRange(1, 100000)
        self.interval.setSuffix(" мин")
        attach_hint(self.interval, "interval_minutes")

        self.daily_from = QTimeEdit()
        self.daily_from.setDisplayFormat("HH:mm")
        attach_hint(self.daily_from, "daily_from")

        self.daily_to = QTimeEdit()
        self.daily_to.setDisplayFormat("HH:mm")
        attach_hint(self.daily_to, "daily_to")

        self._weekday_boxes: list[QCheckBox] = []
        wd_labels = [S.WEEKDAY_1, S.WEEKDAY_2, S.WEEKDAY_3, S.WEEKDAY_4, S.WEEKDAY_5, S.WEEKDAY_6, S.WEEKDAY_7]
        wd_container = QWidget()
        wd_layout = QHBoxLayout(wd_container)
        wd_layout.setContentsMargins(0, 0, 0, 0)
        wd_layout.setSpacing(6)
        for label in wd_labels:
            box = QCheckBox(label)
            attach_hint(box, "weekdays")
            self._weekday_boxes.append(box)
            wd_layout.addWidget(box)
        wd_layout.addStretch(1)

        self.threshold = QSpinBox()
        self.threshold.setRange(1, 100)
        self.threshold.setSuffix(" %")
        attach_hint(self.threshold, "disk_threshold_percent")

        self.auto_prune = QCheckBox(S.LBL_AUTO_PRUNE)
        attach_hint(self.auto_prune, "auto_prune")

        self.template = QLineEdit()
        self.template.setPlaceholderText(DEFAULT_NAME_TEMPLATE)
        attach_hint(self.template, "name_template")

        self.default_destination = QLineEdit()
        self.default_destination.setPlaceholderText(r"D:\Backups")
        attach_hint(self.default_destination, "default_destination")

        form = QFormLayout(self)
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(12)

        if self._show_default_destination:
            form.addRow(LabelWithHint(S.LBL_DEFAULT_DEST, "default_destination"),
                        self.default_destination)

        form.addRow(LabelWithHint(S.LBL_INTERVAL, "interval_minutes"), self.interval)

        time_container = QWidget()
        t_layout = QHBoxLayout(time_container)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(6)
        t_layout.addWidget(self.daily_from)
        from PySide6.QtWidgets import QLabel

        sep = QLabel(S.LBL_DAILY_TO)
        t_layout.addWidget(sep)
        t_layout.addWidget(self.daily_to)
        t_layout.addStretch(1)
        form.addRow(LabelWithHint(S.LBL_DAILY_FROM, "daily_from"), time_container)

        form.addRow(LabelWithHint(S.LBL_WEEKDAYS, "weekdays"), wd_container)
        form.addRow(LabelWithHint(S.LBL_DISK_THRESHOLD, "disk_threshold_percent"), self.threshold)
        form.addRow("", self.auto_prune)
        form.addRow(LabelWithHint(S.LBL_NAME_TEMPLATE, "name_template"), self.template)

    # --- загрузка/сохранение ---
    def load(self, settings: GlobalSettings) -> None:
        if self._show_default_destination:
            self.default_destination.setText(settings.default_destination)
        self.interval.setValue(int(settings.interval_minutes))
        self.daily_from.setTime(_parse_qtime(settings.daily_from, QTime(0, 0)))
        self.daily_to.setTime(_parse_qtime(settings.daily_to, QTime(23, 59)))
        selected = set(settings.weekdays or ALL_WEEKDAYS)
        for idx, box in enumerate(self._weekday_boxes, start=1):
            box.setChecked(idx in selected)
        self.threshold.setValue(int(settings.disk_threshold_percent))
        self.auto_prune.setChecked(bool(settings.auto_prune))
        self.template.setText(settings.name_template or DEFAULT_NAME_TEMPLATE)

    def dump(self, base: GlobalSettings | None = None) -> GlobalSettings:
        src = base.model_copy() if base else GlobalSettings()
        if self._show_default_destination:
            src.default_destination = self.default_destination.text().strip()
        src.interval_minutes = int(self.interval.value())
        src.daily_from = self.daily_from.time().toString("HH:mm")
        src.daily_to = self.daily_to.time().toString("HH:mm")
        src.weekdays = [
            idx for idx, box in enumerate(self._weekday_boxes, start=1) if box.isChecked()
        ] or list(ALL_WEEKDAYS)
        src.disk_threshold_percent = int(self.threshold.value())
        src.auto_prune = bool(self.auto_prune.isChecked())
        src.name_template = self.template.text().strip() or DEFAULT_NAME_TEMPLATE
        return src


def _parse_qtime(value: str, default: QTime) -> QTime:
    try:
        hh, mm = value.split(":", 1)
        t = QTime(int(hh), int(mm))
        if t.isValid():
            return t
    except (ValueError, AttributeError):
        pass
    return default

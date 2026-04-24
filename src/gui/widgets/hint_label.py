"""Метка с иконкой «?», показывающая подробное описание при наведении."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from src.gui.i18n import hints


class HintIcon(QLabel):
    """Маленькая круглая иконка «?» с подробной подсказкой."""

    def __init__(self, hint_key: str, parent: QWidget | None = None) -> None:
        super().__init__("?", parent)
        self.setObjectName("HintIcon")
        text = hints.get(hint_key)
        if text:
            self.setToolTip(text)
            self.setWhatsThis(text)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.WhatsThisCursor)


class LabelWithHint(QWidget):
    """Текстовая метка + иконка «?» справа, с общей подсказкой."""

    def __init__(
        self,
        text: str,
        hint_key: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._label = QLabel(text)
        self._icon = HintIcon(hint_key)
        tip = hints.get(hint_key)
        if tip:
            self._label.setToolTip(tip)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._label)
        layout.addWidget(self._icon)
        layout.addStretch(1)

    def setText(self, text: str) -> None:
        self._label.setText(text)


def attach_hint(widget: QWidget, hint_key: str) -> QWidget:
    """Просто навесить подсказку на любой виджет."""
    text = hints.get(hint_key)
    if text:
        widget.setToolTip(text)
        widget.setWhatsThis(text)
    return widget

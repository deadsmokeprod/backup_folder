"""Главное окно: 3 крупные кнопки, статус службы, индикатор диска."""
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core import config as cfg
from ..core import events, ipc
from .dialogs.add_backup import AddBackupDialog
from .dialogs.backup_list import BackupListDialog
from .dialogs.event_log import EventLogDialog
from .dialogs.global_settings import GlobalSettingsDialog
from .i18n.strings import S
from .widgets.disk_bar import DiskBar
from .widgets.hint_label import attach_hint


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(S.APP_TITLE)
        self.resize(920, 560)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        root.addWidget(self._build_header())
        root.addWidget(self._build_status_card())
        root.addWidget(self._build_actions_card(), 1)
        root.addStretch(1)

        self._log_seen_ts = events.now_ts()

        self._timer = QTimer(self)
        self._timer.setInterval(3000)
        self._timer.timeout.connect(self._refresh_status)
        self._timer.start()
        self._refresh_status()

    # --- построение интерфейса ---
    def _build_header(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        title = QLabel(S.APP_TITLE)
        title.setObjectName("H1")
        subtitle = QLabel(S.APP_SUBTITLE)
        subtitle.setObjectName("Hint")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return container

    def _build_status_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(20)

        self._status_label = QLabel(S.SERVICE_STATUS_UNKNOWN)
        self._status_label.setObjectName("StatusUnknown")

        self._install_btn = QPushButton(S.BTN_INSTALL_SERVICE)
        self._install_btn.setObjectName("Secondary")
        attach_hint(self._install_btn, "btn_install_service")
        self._install_btn.clicked.connect(self._install_service)
        self._install_btn.setVisible(False)

        self._disk_bar = DiskBar()
        self._disk_bar.setMinimumWidth(320)

        layout.addWidget(self._status_label)
        layout.addWidget(self._install_btn)
        layout.addStretch(1)
        layout.addWidget(self._disk_bar, 1)
        return card

    def _build_actions_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("Card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        add_btn = QPushButton(S.BTN_ADD_BACKUP)
        add_btn.setObjectName("Primary")
        add_btn.setMinimumHeight(56)
        attach_hint(add_btn, "btn_add_backup")
        add_btn.clicked.connect(self._open_add)

        list_btn = QPushButton(S.BTN_OPEN_LIST)
        list_btn.setMinimumHeight(56)
        attach_hint(list_btn, "btn_open_list")
        list_btn.clicked.connect(self._open_list)

        settings_btn = QPushButton(S.BTN_OPEN_GLOBAL)
        settings_btn.setMinimumHeight(56)
        attach_hint(settings_btn, "btn_open_global")
        settings_btn.clicked.connect(self._open_global)

        self._log_btn = QPushButton(S.BTN_OPEN_LOG)
        self._log_btn.setMinimumHeight(56)
        attach_hint(self._log_btn, "btn_open_log")
        self._log_btn.clicked.connect(self._open_log)

        layout.addWidget(add_btn, 2)
        layout.addWidget(list_btn, 1)
        layout.addWidget(settings_btn, 1)
        layout.addWidget(self._log_btn, 1)
        return card

    # --- действия ---
    def _open_add(self) -> None:
        dlg = AddBackupDialog(parent=self)
        dlg.exec()
        self._refresh_status()

    def _open_list(self) -> None:
        dlg = BackupListDialog(self)
        dlg.exec()
        self._refresh_status()

    def _open_global(self) -> None:
        dlg = GlobalSettingsDialog(self)
        dlg.exec()
        self._refresh_status()

    def _open_log(self) -> None:
        dlg = EventLogDialog(self)
        dlg.exec()
        self._log_seen_ts = events.now_ts()
        self._refresh_status()

    def _install_service(self) -> None:
        module = "src.installer.install_service"
        # Если запущены из .exe — используем BackupService.exe install
        exe_dir = Path(sys.argv[0]).resolve().parent
        service_exe = exe_dir / "BackupService.exe"
        if getattr(sys, "frozen", False) and service_exe.exists():
            cmd = [str(service_exe), "install", "--startup", "auto"]
            start_cmd = [str(service_exe), "start"]
        else:
            py = sys.executable
            cmd = [py, "-m", module, "install"]
            start_cmd = [py, "-m", module, "start"]

        try:
            _run_elevated(cmd)
            _run_elevated(start_cmd)
        except OSError as exc:
            QMessageBox.critical(self, S.MSG_ERROR, str(exc))
            return
        QMessageBox.information(
            self,
            S.MSG_OK,
            "Команда установки отправлена. Дождитесь запуска службы.",
        )

    # --- обновление статуса ---
    def _refresh_status(self) -> None:
        alive = ipc.is_service_alive()
        if alive:
            self._status_label.setText(S.SERVICE_STATUS_OK)
            self._status_label.setObjectName("StatusOk")
            self._install_btn.setVisible(False)
        else:
            self._status_label.setText(S.SERVICE_STATUS_BAD)
            self._status_label.setObjectName("StatusBad")
            self._install_btn.setVisible(True)
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

        config = cfg.load_config()
        self._disk_bar.update_for(config.globals_.default_destination)

        # бейдж: число новых ошибок с момента последнего открытия журнала
        n = events.unread_error_count(self._log_seen_ts)
        if n > 0:
            self._log_btn.setText(f"{S.BTN_OPEN_LOG}  •  {n}")
            self._log_btn.setObjectName("Primary")
        else:
            self._log_btn.setText(S.BTN_OPEN_LOG)
            self._log_btn.setObjectName("")
        self._log_btn.style().unpolish(self._log_btn)
        self._log_btn.style().polish(self._log_btn)


def _run_elevated(cmd: list[str]) -> None:
    """Запустить команду с UAC-повышением через ShellExecute 'runas'."""
    if sys.platform != "win32":
        subprocess.Popen(cmd)  # noqa: S603
        return
    params = " ".join(f'"{a}"' for a in cmd[1:])
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", cmd[0], params, None, 1
    )
    if int(ret) <= 32:
        raise OSError(f"Не удалось запустить с повышением: код {ret}")

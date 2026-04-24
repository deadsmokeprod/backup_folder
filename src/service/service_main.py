"""Точка входа службы Windows и отладочный запуск в консоли."""
from __future__ import annotations

import logging
import sys
import time
from logging.handlers import RotatingFileHandler

from src.core import db, events
from src.core.paths import service_log_path
from src.service.ipc_server import CommandDispatcher
from src.service.scheduler import Scheduler


SERVICE_NAME = "BackupBotsService"
SERVICE_DISPLAY = "BackupBots — служба резервного копирования"
SERVICE_DESCRIPTION = (
    "Выполняет плановые снимки папок по расписанию и автоматически удаляет "
    "старые снимки при переполнении диска."
)


def _configure_logging() -> None:
    handler = RotatingFileHandler(
        str(service_log_path()),
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


class _Core:
    """Логика службы без зависимости от pywin32 — легко тестировать/отлаживать."""

    def __init__(self) -> None:
        self.scheduler = Scheduler()
        self.ipc = CommandDispatcher(self.scheduler)

    def start(self) -> None:
        db.init_db()
        self.scheduler.start()
        self.ipc.start()
        events.info("service_started")

    def stop(self) -> None:
        self.scheduler.stop()
        self.ipc.stop()
        events.info("service_stopped")


def _run_debug() -> None:
    """Запуск в консоли (Ctrl+C для остановки) — без установки как службы."""
    _configure_logging()
    core = _Core()
    core.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        core.stop()


try:
    import servicemanager
    import win32event
    import win32service
    import win32serviceutil

    class BackupBotsService(win32serviceutil.ServiceFramework):
        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY
        _svc_description_ = SERVICE_DESCRIPTION

        def __init__(self, args) -> None:
            super().__init__(args)
            self._stop_event = win32event.CreateEvent(None, 0, 0, None)
            self._core = _Core()

        def SvcStop(self) -> None:
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self._core.stop()
            win32event.SetEvent(self._stop_event)

        def SvcDoRun(self) -> None:
            _configure_logging()
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            self._core.start()
            win32event.WaitForSingleObject(self._stop_event, win32event.INFINITE)

    HAS_SERVICE = True
except ImportError:  # pragma: no cover
    HAS_SERVICE = False


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        _run_debug()
        return
    if not HAS_SERVICE:
        print("pywin32 не установлен. Используйте 'debug' для запуска в консоли.")
        sys.exit(1)
    win32serviceutil.HandleCommandLine(BackupBotsService)


if __name__ == "__main__":
    main()

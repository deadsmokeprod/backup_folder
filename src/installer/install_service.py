"""Установка/удаление/запуск/остановка службы BackupBots.

Использование:
    python -m src.installer.install_service install
    python -m src.installer.install_service start
    python -m src.installer.install_service stop
    python -m src.installer.install_service restart
    python -m src.installer.install_service uninstall
    python -m src.installer.install_service status
"""
from __future__ import annotations

import sys

try:
    import win32serviceutil

    from src.service.service_main import BackupBotsService
except ImportError as exc:  # pragma: no cover
    print("pywin32 не установлен:", exc)
    sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    argv = argv or sys.argv[1:]
    if not argv:
        print(__doc__)
        return
    # win32serviceutil ожидает имя скрипта в argv[0]
    full = ["install_service.py"] + argv
    # для install_service делаем startType=auto по умолчанию
    if argv[0] == "install" and "--startup" not in " ".join(argv):
        full += ["--startup", "auto"]
    win32serviceutil.HandleCommandLine(BackupBotsService, argv=full)


if __name__ == "__main__":
    main()

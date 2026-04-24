"""Smoke-проверка IPC: запускаем ядро службы в потоке, шлём команды, останавливаем."""
from __future__ import annotations

import sys
import time

from src.core import ipc
from src.service.service_main import _Core


def main() -> int:
    core = _Core()
    core.start()
    try:
        time.sleep(0.6)
        print("ping:", ipc.send_command("ping"))
        print("status:", ipc.send_command("status"))
    finally:
        core.stop()
        time.sleep(0.2)
    return 0


if __name__ == "__main__":
    sys.exit(main())

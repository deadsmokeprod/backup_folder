"""Именованный канал Windows для связи GUI и службы.

Протокол: одна команда = одна строка JSON, заканчивается '\\n'.
Ответ службы — одна строка JSON с полем ok (bool) и полезной нагрузкой.
"""
from __future__ import annotations

import json
import threading
import time
from typing import Any, Callable, Optional

from src.core.paths import PIPE_NAME


try:
    import win32file
    import win32pipe
    import pywintypes
    import winerror

    HAS_PYWIN32 = True
except ImportError:  # pragma: no cover
    HAS_PYWIN32 = False


BUFFER_SIZE = 64 * 1024


# --------- клиент (GUI) ---------

def send_command(cmd: str, timeout_ms: int = 2000, **payload: Any) -> Optional[dict]:
    """Отправить команду службе и получить ответ. Вернёт None при ошибке."""
    if not HAS_PYWIN32:
        return None
    message = json.dumps({"cmd": cmd, **payload}, ensure_ascii=False) + "\n"
    try:
        win32pipe.WaitNamedPipe(PIPE_NAME, timeout_ms)
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )
    except pywintypes.error:
        return None
    try:
        win32pipe.SetNamedPipeHandleState(
            handle, win32pipe.PIPE_READMODE_MESSAGE, None, None
        )
        win32file.WriteFile(handle, message.encode("utf-8"))
        _, data = win32file.ReadFile(handle, BUFFER_SIZE)
        text = data.decode("utf-8", errors="replace").strip()
        if not text:
            return None
        return json.loads(text)
    except (pywintypes.error, json.JSONDecodeError):
        return None
    finally:
        try:
            win32file.CloseHandle(handle)
        except pywintypes.error:
            pass


def is_service_alive() -> bool:
    return send_command("ping") is not None


# --------- сервер (служба) ---------

Handler = Callable[[dict], dict]


class PipeServer:
    """Принимает одно подключение за раз, вызывает handler и возвращает ответ."""

    def __init__(self, handler: Handler) -> None:
        self._handler = handler
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if not HAS_PYWIN32:
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="PipeServer")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:  # pragma: no cover — тестируется вручную
        while not self._stop.is_set():
            try:
                handle = win32pipe.CreateNamedPipe(
                    PIPE_NAME,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE
                    | win32pipe.PIPE_READMODE_MESSAGE
                    | win32pipe.PIPE_WAIT,
                    win32pipe.PIPE_UNLIMITED_INSTANCES,
                    BUFFER_SIZE,
                    BUFFER_SIZE,
                    0,
                    None,
                )
            except pywintypes.error:
                time.sleep(0.5)
                continue
            try:
                try:
                    win32pipe.ConnectNamedPipe(handle, None)
                except pywintypes.error as err:
                    if err.winerror != winerror.ERROR_PIPE_CONNECTED:
                        continue
                try:
                    _, data = win32file.ReadFile(handle, BUFFER_SIZE)
                    text = data.decode("utf-8", errors="replace").strip()
                    try:
                        request = json.loads(text)
                    except json.JSONDecodeError:
                        response = {"ok": False, "error": "bad_json"}
                    else:
                        try:
                            response = self._handler(request)
                        except Exception as exc:  # noqa: BLE001
                            response = {"ok": False, "error": str(exc)}
                    win32file.WriteFile(
                        handle,
                        (json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"),
                    )
                except pywintypes.error:
                    pass
            finally:
                try:
                    win32pipe.DisconnectNamedPipe(handle)
                except pywintypes.error:
                    pass
                try:
                    win32file.CloseHandle(handle)
                except pywintypes.error:
                    pass

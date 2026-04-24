"""Загрузка и сохранение config.json с простой файловой блокировкой."""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

from src.core.models import AppConfig
from src.core.paths import app_data_dir, config_path


def _lock_path() -> Path:
    return app_data_dir() / "config.lock"


class _FileLock:
    """Очень простой межпроцессный лок через монопольное создание файла."""

    def __init__(self, path: Path, timeout: float = 5.0) -> None:
        self.path = path
        self.timeout = timeout
        self._fd: Optional[int] = None

    def __enter__(self) -> "_FileLock":
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self._fd = os.open(
                    str(self.path),
                    os.O_CREAT | os.O_EXCL | os.O_RDWR,
                )
                return self
            except FileExistsError:
                if time.monotonic() >= deadline:
                    try:
                        self.path.unlink()
                    except OSError:
                        pass
                    continue
                time.sleep(0.05)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            finally:
                try:
                    self.path.unlink()
                except OSError:
                    pass


def load_config() -> AppConfig:
    path = config_path()
    if not path.exists():
        return AppConfig()
    with _FileLock(_lock_path()):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return AppConfig()
    return AppConfig.model_validate(data)


def save_config(config: AppConfig) -> None:
    path = config_path()
    data = config.model_dump(by_alias=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    with _FileLock(_lock_path()):
        tmp = tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=str(path.parent),
            encoding="utf-8",
            suffix=".tmp",
        )
        try:
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
        finally:
            tmp.close()
        os.replace(tmp.name, str(path))

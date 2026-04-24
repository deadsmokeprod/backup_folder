"""Пути к данным приложения в %ProgramData%\\BackupBots."""
from __future__ import annotations

import os
from pathlib import Path

APP_DIR_NAME = "BackupBots"


def _program_data() -> Path:
    base = os.environ.get("ProgramData") or os.environ.get("PROGRAMDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Local")
    return Path(base)


def app_data_dir() -> Path:
    path = _program_data() / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return app_data_dir() / "config.json"


def db_path() -> Path:
    return app_data_dir() / "history.db"


def logs_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def service_log_path() -> Path:
    return logs_dir() / "service.log"


def gui_log_path() -> Path:
    return logs_dir() / "gui.log"


PIPE_NAME = r"\\.\pipe\BackupBots"

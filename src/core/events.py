"""Шина событий: пишет структурированные записи в events.ndjson + дублирует в logging.

Файл events.ndjson — newline-delimited JSON, по одной записи на строку. Удобно читать с конца
для отображения в журнале GUI. Также применяется простая ротация по размеру.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from src.core import event_codes
from src.core.paths import logs_dir


EVENTS_FILE_NAME = "events.ndjson"
MAX_FILE_BYTES = 2_000_000


_lock = threading.Lock()
_log = logging.getLogger("events")


def events_path() -> Path:
    return logs_dir() / EVENTS_FILE_NAME


def _rotate_if_needed(path: Path) -> None:
    try:
        if path.exists() and path.stat().st_size > MAX_FILE_BYTES:
            backup = path.with_suffix(".ndjson.1")
            try:
                if backup.exists():
                    backup.unlink()
            except OSError:
                pass
            try:
                path.rename(backup)
            except OSError:
                pass
    except OSError:
        pass


def emit(level: str, code: str, **fields: Any) -> None:
    """Зафиксировать событие. Уровни: INFO/WARNING/ERROR."""
    level_norm = (level or event_codes.LEVEL_INFO).upper()
    human = event_codes.render(code, **fields)
    record = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "level": level_norm,
        "code": code,
        "message": human,
        "fields": fields,
    }
    try:
        path = events_path()
        with _lock:
            _rotate_if_needed(path)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass

    log_level = {
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
    }.get(level_norm, logging.INFO)
    try:
        _log.log(log_level, "%s %s", code, human)
    except Exception:  # noqa: BLE001
        pass


def info(code: str, **fields: Any) -> None:
    emit(event_codes.LEVEL_INFO, code, **fields)


def warn(code: str, **fields: Any) -> None:
    emit(event_codes.LEVEL_WARNING, code, **fields)


def error(code: str, **fields: Any) -> None:
    emit(event_codes.LEVEL_ERROR, code, **fields)


def read_events(limit: int = 500) -> list[dict]:
    """Прочитать последние N событий, новые — первыми."""
    path = events_path()
    if not path.exists():
        return []
    buf: deque[str] = deque(maxlen=limit)
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    buf.append(line)
    except OSError:
        return []
    out: list[dict] = []
    for raw in reversed(buf):
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return out


def clear_events() -> None:
    path = events_path()
    with _lock:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
        backup = path.with_suffix(".ndjson.1")
        try:
            if backup.exists():
                backup.unlink()
        except OSError:
            pass


def all_log_files() -> list[Path]:
    """Все файлы логов для скачивания пользователем."""
    base = logs_dir()
    paths: list[Path] = []
    for name in ("service.log", "gui.log", "events.ndjson", "events.ndjson.1"):
        p = base / name
        if p.exists():
            paths.append(p)
    for backup in base.glob("service.log.*"):
        if backup.is_file():
            paths.append(backup)
    for backup in base.glob("gui.log.*"):
        if backup.is_file():
            paths.append(backup)
    return paths


def unread_error_count(since_ts: float) -> int:
    """Сколько ошибок в журнале новее заданной метки времени (для бейджа)."""
    n = 0
    for ev in read_events(limit=200):
        if ev.get("level") != event_codes.LEVEL_ERROR:
            continue
        try:
            ts = datetime.fromisoformat(ev["ts"]).timestamp()
        except (KeyError, ValueError):
            continue
        if ts > since_ts:
            n += 1
    return n


def now_ts() -> float:
    return time.time()


# Вспомогательная функция для форматирования размера
def human_size(num: float) -> str:
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} ПБ"


def iter_codes() -> Iterable[str]:
    return event_codes.CODE_TO_HUMAN.keys()

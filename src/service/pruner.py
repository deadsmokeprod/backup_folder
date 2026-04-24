"""Автоочистка старых снимков при превышении порога заполненности диска."""
from __future__ import annotations

import shutil
from pathlib import Path

import psutil

from src.core import db, events
from src.core.models import GlobalSettings


def _disk_percent(path: str) -> float | None:
    try:
        return float(psutil.disk_usage(path).percent)
    except (OSError, ValueError):
        return None


def prune_if_needed(settings: GlobalSettings) -> None:
    """Удаляет самые старые снимки, пока занятость диска выше порога."""
    if not settings.auto_prune:
        return
    dest = settings.default_destination
    if not dest:
        return
    threshold = float(settings.disk_threshold_percent)

    while True:
        percent = _disk_percent(dest)
        if percent is None or percent <= threshold:
            return
        oldest = db.get_oldest_snapshot_excluding_last_per_job()
        if oldest is None:
            events.warn("prune_nothing_to_delete", percent=f"{percent:.1f}")
            return
        path = Path(oldest.path)
        try:
            if path.exists():
                shutil.rmtree(path)
        except OSError as exc:
            events.error("prune_failed", path=str(path), reason=str(exc))
            return
        db.delete_snapshot(oldest.id)
        events.info("prune_deleted", path=str(path), percent=f"{percent:.1f}")

"""Выполнение одного прохода бэкапа: копирование источника в новую папку."""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from ..core import db, events, naming
from ..core.events import human_size
from ..core.models import BackupJob, GlobalSettings


def _calculate_size(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        try:
            if child.is_file():
                total += child.stat().st_size
        except OSError:
            pass
    return total


def run_backup(job: BackupJob, settings: GlobalSettings) -> bool:
    """Выполнить один бэкап. Возвращает True при успехе."""
    source = Path(job.source)
    if not source.exists() or not source.is_dir():
        events.warn("source_missing", job=job.name, path=str(job.source))
        return False

    dest_root_str = job.effective_destination(settings)
    if not dest_root_str:
        events.error("dest_missing", job=job.name)
        return False
    dest_root = Path(dest_root_str)
    try:
        dest_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        events.error("dest_not_writable", job=job.name, path=str(dest_root), reason=str(exc))
        return False

    ts = datetime.now().replace(microsecond=0)
    folder_name = naming.build_folder_name(job.name, settings.name_template, ts)
    final_dir = dest_root / folder_name
    tmp_dir = dest_root / (folder_name + ".partial")

    if final_dir.exists():
        folder_name = f"{folder_name}_{int(ts.timestamp())}"
        final_dir = dest_root / folder_name
        tmp_dir = dest_root / (folder_name + ".partial")

    if tmp_dir.exists():
        try:
            shutil.rmtree(tmp_dir)
        except OSError:
            pass

    events.info("backup_started", job=job.name)
    try:
        shutil.copytree(str(source), str(tmp_dir))
    except (OSError, shutil.Error) as exc:
        events.error("backup_failed_copy", job=job.name, reason=str(exc))
        try:
            shutil.rmtree(tmp_dir)
        except OSError:
            pass
        return False

    try:
        tmp_dir.rename(final_dir)
    except OSError as exc:
        events.error("backup_failed_rename", job=job.name, reason=str(exc))
        return False

    size = _calculate_size(final_dir)
    db.insert_snapshot(job.id, str(final_dir), size, ts)
    events.info("backup_done", job=job.name, size=human_size(size), path=str(final_dir))
    return True

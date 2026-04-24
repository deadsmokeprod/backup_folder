"""End-to-end smoke: создать джоб, выполнить бэкап, проверить снимок."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

from src.core import config as cfg
from src.core import db
from src.core.models import AppConfig, BackupJob, GlobalSettings
from src.core.paths import app_data_dir, config_path, db_path
from src.service import runner


def main() -> int:
    # Работаем в изолированной директории, чтобы не мешать реальным данным
    sandbox = Path(tempfile.mkdtemp(prefix="bb_smoke_"))
    os.environ["ProgramData"] = str(sandbox)
    # перезагружаем модули, которые кэшировали путь
    for mod in ("src.core.paths",):
        sys.modules.pop(mod, None)
    from src.core import paths as paths2  # noqa: F401

    # Создаём исходную папку с файлом
    src = sandbox / "src"
    src.mkdir()
    (src / "hello.txt").write_text("hello world", encoding="utf-8")
    (src / "sub").mkdir()
    (src / "sub" / "a.bin").write_bytes(b"\x00" * 1024)

    dst = sandbox / "dst"
    dst.mkdir()

    gs = GlobalSettings(default_destination=str(dst), interval_minutes=1)
    job = BackupJob(name="MyDocs", source=str(src))
    c = AppConfig(globals_=gs, jobs=[job])
    cfg.save_config(c)

    db.init_db()

    ok = runner.run_backup(job, gs)
    print("run_backup ok:", ok)

    snapshots = list(dst.iterdir())
    print("snapshot dirs:", [p.name for p in snapshots])
    assert ok, "backup failed"
    assert len(snapshots) == 1
    snap_dir = snapshots[0]
    assert snap_dir.name.startswith("MyDocs_")
    assert (snap_dir / "hello.txt").read_text(encoding="utf-8") == "hello world"
    assert (snap_dir / "sub" / "a.bin").exists()

    stats = db.get_job_stats(job.id)
    print("stats:", stats)
    assert stats.snapshot_count == 1
    assert stats.total_size_bytes > 1000

    # чистим
    shutil.rmtree(sandbox, ignore_errors=True)
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

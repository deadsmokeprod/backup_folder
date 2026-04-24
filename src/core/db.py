"""История снимков в SQLite."""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator, Optional

from src.core.models import JobStats, Snapshot
from src.core.paths import db_path


_DDL = """
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshots_job_created
    ON snapshots(job_id, created_at);
"""

_lock = threading.Lock()


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(db_path()))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _lock, _connect() as conn:
        conn.executescript(_DDL)


def _row_to_snapshot(row: sqlite3.Row) -> Snapshot:
    return Snapshot(
        id=row["id"],
        job_id=row["job_id"],
        path=row["path"],
        size_bytes=row["size_bytes"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def insert_snapshot(job_id: str, path: str, size_bytes: int, created_at: datetime) -> int:
    with _lock, _connect() as conn:
        cur = conn.execute(
            "INSERT INTO snapshots (job_id, path, size_bytes, created_at) VALUES (?, ?, ?, ?)",
            (job_id, path, size_bytes, created_at.isoformat(timespec="seconds")),
        )
        return int(cur.lastrowid)


def delete_snapshot(snapshot_id: int) -> None:
    with _lock, _connect() as conn:
        conn.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))


def list_snapshots(job_id: str) -> list[Snapshot]:
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM snapshots WHERE job_id = ? ORDER BY created_at DESC",
            (job_id,),
        ).fetchall()
    return [_row_to_snapshot(r) for r in rows]


def get_last_snapshot(job_id: str) -> Optional[Snapshot]:
    with _lock, _connect() as conn:
        row = conn.execute(
            "SELECT * FROM snapshots WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
            (job_id,),
        ).fetchone()
    return _row_to_snapshot(row) if row else None


def get_job_stats(job_id: str) -> JobStats:
    with _lock, _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt, COALESCE(SUM(size_bytes), 0) AS total, "
            "MIN(created_at) AS oldest, MAX(created_at) AS newest "
            "FROM snapshots WHERE job_id = ?",
            (job_id,),
        ).fetchone()
    return JobStats(
        job_id=job_id,
        snapshot_count=int(row["cnt"]),
        total_size_bytes=int(row["total"]),
        oldest_at=datetime.fromisoformat(row["oldest"]) if row["oldest"] else None,
        newest_at=datetime.fromisoformat(row["newest"]) if row["newest"] else None,
    )


def get_oldest_snapshot_excluding_last_per_job() -> Optional[Snapshot]:
    """Самый старый снимок, но не единственный для своего джоба."""
    with _lock, _connect() as conn:
        row = conn.execute(
            """
            SELECT s.* FROM snapshots s
            WHERE (SELECT COUNT(*) FROM snapshots s2 WHERE s2.job_id = s.job_id) > 1
            ORDER BY s.created_at ASC
            LIMIT 1
            """
        ).fetchone()
    return _row_to_snapshot(row) if row else None

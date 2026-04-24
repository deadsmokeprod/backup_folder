"""Планировщик: решает, какие ветки пора запустить, и выполняет их."""
from __future__ import annotations

import threading
from datetime import datetime, time as dtime
from typing import Optional

from src.core import config as cfg
from src.core import db, events
from src.core.models import BackupJob, GlobalSettings
from src.service import pruner, runner


def _parse_hhmm(value: str, default: dtime) -> dtime:
    try:
        hh, mm = value.split(":", 1)
        return dtime(int(hh), int(mm))
    except (ValueError, AttributeError):
        return default


def _within_daily_window(now: datetime, settings: GlobalSettings) -> bool:
    start = _parse_hhmm(settings.daily_from, dtime(0, 0))
    end = _parse_hhmm(settings.daily_to, dtime(23, 59))
    cur = now.time().replace(second=0, microsecond=0)
    if start <= end:
        return start <= cur <= end
    return cur >= start or cur <= end


def _weekday_1based(now: datetime) -> int:
    return now.isoweekday()  # 1=Пн ... 7=Вс


def _is_due(job: BackupJob, settings: GlobalSettings, now: datetime) -> bool:
    if job.paused:
        return False
    if _weekday_1based(now) not in settings.weekdays:
        return False
    if not _within_daily_window(now, settings):
        return False
    last = db.get_last_snapshot(job.id)
    if last is None:
        return True
    delta_min = (now - last.created_at).total_seconds() / 60.0
    return delta_min >= float(settings.interval_minutes)


class Scheduler:
    """Цикл tick() раз в минуту."""

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running_jobs: set[str] = set()
        self._lock = threading.Lock()

    def start(self) -> None:
        db.init_db()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="Scheduler")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def tick_once(self) -> None:
        """Один проход — полезно для отладки и тестов."""
        self._tick()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as exc:  # noqa: BLE001
                events.error("unknown_error", reason=str(exc))
            # спим по 5 секунд, чтобы быстро реагировать на stop
            for _ in range(12):
                if self._stop.is_set():
                    break
                self._stop.wait(5)

    def _tick(self) -> None:
        config = cfg.load_config()
        now = datetime.now().replace(microsecond=0)
        for job in config.jobs:
            settings = job.effective_settings(config.globals_)
            with self._lock:
                if job.id in self._running_jobs:
                    continue
            if not _is_due(job, settings, now):
                continue
            with self._lock:
                self._running_jobs.add(job.id)
            threading.Thread(
                target=self._run_and_release,
                args=(job, settings),
                daemon=True,
                name=f"Run-{job.name}",
            ).start()

    def _run_and_release(self, job: BackupJob, settings: GlobalSettings) -> None:
        try:
            ok = runner.run_backup(job, settings)
            if ok:
                # глобальные настройки берём свежие: пользователь мог поменять порог диска
                latest = cfg.load_config().globals_
                pruner.prune_if_needed(latest)
        finally:
            with self._lock:
                self._running_jobs.discard(job.id)

    def run_now(self, job_id: str) -> bool:
        """Принудительно запустить ветку прямо сейчас."""
        config = cfg.load_config()
        job = next((j for j in config.jobs if j.id == job_id), None)
        if job is None:
            return False
        with self._lock:
            if job.id in self._running_jobs:
                return False
            self._running_jobs.add(job.id)
        settings = job.effective_settings(config.globals_)
        threading.Thread(
            target=self._run_and_release,
            args=(job, settings),
            daemon=True,
            name=f"RunNow-{job.name}",
        ).start()
        return True

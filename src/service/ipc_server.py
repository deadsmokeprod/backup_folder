"""Обработка команд от GUI через именованный канал."""
from __future__ import annotations

import logging
from typing import Any

import psutil

from ..core import config as cfg
from ..core import db, events, ipc
from .scheduler import Scheduler


log = logging.getLogger("service.ipc")


class CommandDispatcher:
    def __init__(self, scheduler: Scheduler) -> None:
        self._scheduler = scheduler
        self.pipe = ipc.PipeServer(self.handle)

    def start(self) -> None:
        self.pipe.start()

    def stop(self) -> None:
        self.pipe.stop()

    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        cmd = request.get("cmd")
        if cmd == "ping":
            return {"ok": True, "alive": True}
        if cmd == "status":
            return {"ok": True, **self._status()}
        if cmd == "set_pause":
            return self._set_pause(request)
        if cmd == "run_now":
            job_id = request.get("job_id")
            if not isinstance(job_id, str):
                return {"ok": False, "error": "job_id required"}
            job_name = self._job_name(job_id)
            if job_name:
                events.info("run_now_requested", job=job_name)
            ok = self._scheduler.run_now(job_id)
            return {"ok": ok}
        if cmd == "reload":
            return {"ok": True}
        return {"ok": False, "error": f"unknown cmd: {cmd}"}

    def _status(self) -> dict[str, Any]:
        config = cfg.load_config()
        dest = config.globals_.default_destination
        disk: dict[str, Any] = {}
        if dest:
            try:
                usage = psutil.disk_usage(dest)
                disk = {
                    "total": int(usage.total),
                    "used": int(usage.used),
                    "free": int(usage.free),
                    "percent": float(usage.percent),
                }
            except OSError:
                disk = {}
        return {
            "jobs": [
                {
                    "id": j.id,
                    "name": j.name,
                    "paused": j.paused,
                    "last_snapshot": _last_iso(j.id),
                }
                for j in config.jobs
            ],
            "disk": disk,
        }

    def _set_pause(self, request: dict[str, Any]) -> dict[str, Any]:
        job_id = request.get("job_id")
        paused = bool(request.get("paused", True))
        if not isinstance(job_id, str):
            return {"ok": False, "error": "job_id required"}
        config = cfg.load_config()
        changed = False
        target_name = ""
        for j in config.jobs:
            if j.id == job_id:
                j.paused = paused
                target_name = j.name
                changed = True
                break
        if not changed:
            return {"ok": False, "error": "job not found"}
        cfg.save_config(config)
        events.info("paused_manual" if paused else "resumed_manual", job=target_name)
        return {"ok": True}

    def _job_name(self, job_id: str) -> str | None:
        config = cfg.load_config()
        for j in config.jobs:
            if j.id == job_id:
                return j.name
        return None


def _last_iso(job_id: str) -> str | None:
    snap = db.get_last_snapshot(job_id)
    return snap.created_at.isoformat(timespec="seconds") if snap else None

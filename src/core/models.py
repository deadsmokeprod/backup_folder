"""Модели данных: глобальные настройки, ветка бэкапа, снимок."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


DEFAULT_NAME_TEMPLATE = "{name}_{YYYY}-{MM}-{DD}_{HH}-{mm}-{ss}"
ALL_WEEKDAYS = [1, 2, 3, 4, 5, 6, 7]  # 1=Пн ... 7=Вс


class GlobalSettings(BaseModel):
    """Глобальные настройки бэкапа и автоочистки."""

    default_destination: str = ""
    name_template: str = DEFAULT_NAME_TEMPLATE
    interval_minutes: int = 60
    daily_from: str = "00:00"
    daily_to: str = "23:59"
    weekdays: list[int] = Field(default_factory=lambda: list(ALL_WEEKDAYS))
    disk_threshold_percent: int = 80
    auto_prune: bool = True


class BackupJob(BaseModel):
    """Ветка бэкапа — одна связка «источник → приёмник» с расписанием."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    source: str
    destination: Optional[str] = None  # None = брать из глобальных
    paused: bool = False
    use_global_settings: bool = True
    overrides: Optional[GlobalSettings] = None

    def effective_settings(self, globals_: GlobalSettings) -> GlobalSettings:
        if self.use_global_settings or self.overrides is None:
            return globals_
        return self.overrides

    def effective_destination(self, globals_: GlobalSettings) -> str:
        return self.destination or globals_.default_destination


class AppConfig(BaseModel):
    """Весь конфиг приложения."""

    globals_: GlobalSettings = Field(default_factory=GlobalSettings, alias="globals")
    jobs: list[BackupJob] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


@dataclass
class Snapshot:
    """Один готовый снимок бэкапа (запись в БД истории)."""

    id: int
    job_id: str
    path: str
    size_bytes: int
    created_at: datetime


@dataclass
class JobStats:
    """Агрегированные показатели для ветки."""

    job_id: str
    snapshot_count: int
    total_size_bytes: int
    oldest_at: Optional[datetime]
    newest_at: Optional[datetime]

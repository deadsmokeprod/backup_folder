"""Формирование имени папки снимка по шаблону."""
from __future__ import annotations

import re
from datetime import datetime

from .models import DEFAULT_NAME_TEMPLATE


_INVALID_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize(name: str) -> str:
    """Убирает недопустимые в именах папок символы."""
    cleaned = _INVALID_FS_CHARS.sub("_", name).strip()
    return cleaned or "backup"


def build_folder_name(name: str, template: str | None, when: datetime) -> str:
    """
    Подставляет имя ветки и дату в шаблон.

    Поддерживаемые плейсхолдеры:
      {name} {YYYY} {MM} {DD} {HH} {mm} {ss}
    """
    tpl = template or DEFAULT_NAME_TEMPLATE
    parts = {
        "name": sanitize(name),
        "YYYY": f"{when.year:04d}",
        "MM": f"{when.month:02d}",
        "DD": f"{when.day:02d}",
        "HH": f"{when.hour:02d}",
        "mm": f"{when.minute:02d}",
        "ss": f"{when.second:02d}",
    }
    try:
        result = tpl.format(**parts)
    except (KeyError, IndexError, ValueError):
        result = DEFAULT_NAME_TEMPLATE.format(**parts)
    return sanitize(result)

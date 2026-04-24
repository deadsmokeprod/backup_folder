"""Коды событий и человеческие формулировки на русском.

Каждый код соответствует одной ситуации в работе приложения.
В шаблонах поддерживается str.format с любыми именованными полями.
"""
from __future__ import annotations


# Уровни — соответствуют logging.LEVEL
LEVEL_INFO = "INFO"
LEVEL_WARNING = "WARNING"
LEVEL_ERROR = "ERROR"


CODE_TO_HUMAN: dict[str, str] = {
    # --- запуск/остановка ---
    "service_started": "Служба резервного копирования запущена",
    "service_stopped": "Служба резервного копирования остановлена",
    "gui_started": "Приложение открыто",

    # --- бэкапы ---
    "backup_started": "Начинаю бэкап ветки «{job}»",
    "backup_done": "Бэкап ветки «{job}» завершён, сохранено {size}",
    "backup_failed_copy": "Не удалось скопировать файлы ветки «{job}»: {reason}",
    "backup_failed_rename": "Не удалось завершить запись бэкапа ветки «{job}»: {reason}",
    "backup_skipped_running": "Пропускаю ветку «{job}» — предыдущий бэкап ещё выполняется",

    # --- источник/приёмник ---
    "source_missing": "Источник ветки «{job}» недоступен: {path}",
    "dest_missing": "Для ветки «{job}» не задана папка-приёмник",
    "dest_not_writable": "Не удалось создать папку-приёмник «{path}»: {reason}",

    # --- автоочистка ---
    "prune_deleted": "Автоочистка: удалён старый снимок «{path}» (диск был заполнен на {percent}%)",
    "prune_failed": "Не удалось удалить старый снимок «{path}»: {reason}",
    "prune_nothing_to_delete": (
        "Диск заполнен на {percent}%, но автоочистка не нашла что удалить — у каждой ветки"
        " остался только один снимок (защита от потери данных)"
    ),

    # --- управление ---
    "paused_manual": "Ветка «{job}» поставлена на паузу",
    "resumed_manual": "Ветка «{job}» возобновлена",
    "run_now_requested": "Запрошен немедленный бэкап ветки «{job}»",

    # --- конфиг ---
    "config_load_error": "Не удалось прочитать настройки: {reason}",
    "config_save_error": "Не удалось сохранить настройки: {reason}",

    # --- общее ---
    "unknown_error": "Внутренняя ошибка: {reason}",
}


def render(code: str, **fields) -> str:
    template = CODE_TO_HUMAN.get(code)
    if not template:
        return f"{code}: {fields}"
    try:
        return template.format(**fields)
    except (KeyError, IndexError):
        return template

"""Строки интерфейса (русский). Централизованно — чтобы легко поддерживать."""
from __future__ import annotations


class S:
    # --- приложение ---
    APP_TITLE = "BackupBots — резервное копирование"
    APP_SUBTITLE = "Плановые снимки ваших папок с автоочисткой по заполненности диска"

    # --- главное окно ---
    BTN_ADD_BACKUP = "Добавить папку для бэкапа"
    BTN_OPEN_LIST = "Список бэкапов"
    BTN_OPEN_GLOBAL = "Глобальные настройки"
    BTN_OPEN_LOG = "Журнал событий"
    BTN_INSTALL_SERVICE = "Установить службу"
    BTN_REFRESH = "Обновить"

    SERVICE_STATUS_OK = "Служба работает"
    SERVICE_STATUS_BAD = "Служба не запущена"
    SERVICE_STATUS_UNKNOWN = "Статус службы неизвестен"

    EMPTY_NO_JOBS = (
        "Пока нет ни одной ветки бэкапа.\n"
        "Нажмите «Добавить папку для бэкапа», чтобы начать."
    )

    # --- диалог добавления/редактирования ---
    DLG_ADD_TITLE = "Новая ветка бэкапа"
    DLG_EDIT_TITLE = "Редактирование ветки бэкапа"
    LBL_NAME = "Название"
    LBL_SOURCE = "Исходная папка"
    LBL_DESTINATION = "Куда сохранять"
    LBL_DESTINATION_PLACEHOLDER = "По умолчанию — глобальная папка"
    LBL_USE_GLOBAL = "Использовать глобальные параметры"
    LBL_OVERRIDES_GROUP = "Частные параметры этой ветки"
    BTN_BROWSE = "Обзор…"
    BTN_SAVE = "Сохранить"
    BTN_CANCEL = "Отмена"
    BTN_DELETE = "Удалить ветку"

    # --- параметры (общие и частные) ---
    LBL_INTERVAL = "Интервал между снимками, мин"
    LBL_DAILY_FROM = "Делать бэкапы с"
    LBL_DAILY_TO = "до"
    LBL_WEEKDAYS = "Дни недели"
    LBL_DISK_THRESHOLD = "Порог автоочистки диска, %"
    LBL_AUTO_PRUNE = "Включить автоочистку"
    LBL_NAME_TEMPLATE = "Шаблон имени папки снимка"
    LBL_DEFAULT_DEST = "Папка для бэкапов по умолчанию"

    WEEKDAY_1 = "Пн"
    WEEKDAY_2 = "Вт"
    WEEKDAY_3 = "Ср"
    WEEKDAY_4 = "Чт"
    WEEKDAY_5 = "Пт"
    WEEKDAY_6 = "Сб"
    WEEKDAY_7 = "Вс"

    # --- список бэкапов ---
    DLG_LIST_TITLE = "Список бэкапов"
    COL_NAME = "Название"
    COL_SOURCE = "Источник"
    COL_LAST = "Последний снимок"
    COL_PERIOD = "Период"
    COL_SIZE = "Общий размер"
    COL_STATE = "Статус"
    COL_PAUSE = "Пауза"
    STATE_ACTIVE = "Активна"
    STATE_PAUSED = "На паузе"
    BTN_OPEN_DETAIL = "Открыть"
    BTN_RUN_NOW = "Запустить сейчас"
    BTN_PAUSE = "Пауза"
    BTN_RESUME = "Продолжить"
    BTN_EDIT = "Редактировать"

    # --- детали ветки ---
    DLG_DETAIL_TITLE = "Ветка: {name}"
    COL_SNAPSHOT_DATE = "Дата снимка"
    COL_SNAPSHOT_SIZE = "Размер"
    COL_SNAPSHOT_PATH = "Путь"
    BTN_OPEN_EXPLORER = "Открыть в Проводнике"
    BTN_DELETE_SNAPSHOT = "Удалить снимок"

    # --- глобальные настройки ---
    DLG_GLOBAL_TITLE = "Глобальные настройки"
    LBL_DISK_USAGE = "Занятость диска-приёмника"
    LBL_DISK_FREE = "Свободно {free} из {total}"
    LBL_DISK_UNKNOWN = "Не удаётся прочитать состояние диска"

    # --- общее ---
    MSG_ERROR = "Ошибка"
    MSG_OK = "Готово"
    MSG_CONFIRM_DELETE_JOB = "Удалить ветку «{name}»?\nСами снимки на диске не удаляются."
    MSG_CONFIRM_DELETE_SNAPSHOT = "Удалить снимок {path}?\nЭто действие необратимо."
    MSG_SERVICE_INSTALL_HINT = (
        "Служба BackupBots не запущена. Без неё снимки не будут создаваться по расписанию.\n\n"
        "Нажмите «Установить службу», чтобы зарегистрировать её в Windows (потребуются права администратора)."
    )
    MSG_SOURCE_MISSING = "Выберите существующую исходную папку."
    MSG_NAME_REQUIRED = "Укажите название ветки."
    MSG_DEST_REQUIRED = (
        "Не указана папка-приёмник: ни у ветки, ни в глобальных настройках."
    )

    # --- журнал событий ---
    DLG_LOG_TITLE = "Журнал событий"
    LOG_FILTER_ALL = "Все события"
    LOG_FILTER_ERRORS = "Только ошибки"
    LOG_FILTER_WARNINGS = "Ошибки и предупреждения"
    LOG_COL_TIME = "Время"
    LOG_COL_LEVEL = ""
    LOG_COL_MESSAGE = "Что произошло"
    BTN_LOG_DOWNLOAD = "Скачать лог…"
    BTN_LOG_CLEAR = "Очистить журнал"
    LOG_EMPTY = (
        "Пока в журнале пусто.\n"
        "Здесь будут появляться события: успешные бэкапы, ошибки и предупреждения."
    )
    MSG_LOG_DOWNLOADED = "Лог сохранён в файл:\n{path}"
    MSG_LOG_CLEARED = "Журнал очищен."
    MSG_CONFIRM_LOG_CLEAR = "Очистить журнал событий? Файлы логов на диске также будут удалены."

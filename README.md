# BackupBots

Десктопное Windows-приложение для резервного копирования папок.

- GUI на **Python + PySide6** в тёмной аниме-теме, интерфейс полностью на русском
- Фоновое копирование по расписанию через настоящую **службу Windows** (pywin32)
- Полные папочные снимки с датой и временем в имени: `Documents_2026-04-24_14-30-00`
- Глобальные и частные настройки для каждой ветки бэкапа
- Список веток с размером, периодом, кнопкой паузы
- Индикатор свободного места и автоочистка старых снимков по порогу занятости диска

## Установка окружения разработки

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Запуск в режиме разработки

GUI:
```powershell
python -m src.gui.app
```

Служба (в консольном режиме, без установки — для отладки):
```powershell
python -m src.service.service_main debug
```

## Установка службы в систему (требует прав администратора)

```powershell
python -m src.installer.install_service install
python -m src.installer.install_service start
```

Удаление:

```powershell
python -m src.installer.install_service stop
python -m src.installer.install_service uninstall
```

## Сборка .exe

```powershell
pyinstaller build/gui.spec
pyinstaller build/service.spec
```

Результат — `dist/BackupApp.exe` и `dist/BackupService.exe`.

## Где хранятся данные

- Конфигурация: `%ProgramData%\BackupBots\config.json`
- История снимков: `%ProgramData%\BackupBots\history.db`
- Логи службы: `%ProgramData%\BackupBots\logs\service.log`
- Снимки: в папке-приёмнике, которую вы выбрали (глобальная или у каждой ветки своя)

## Архитектура

```
[BackupApp.exe (GUI)]  <-- named pipe -->  [BackupService.exe (служба)]
         |                                          |
         +------ ProgramData\BackupBots\config.json ------+
                        history.db
```

GUI только редактирует конфиг и показывает историю. Реальное копирование и автоочистку делает служба.

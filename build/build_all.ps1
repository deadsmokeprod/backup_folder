# BackupBots — полная сборка установщика.
# Использование: powershell -ExecutionPolicy Bypass -File build\build_all.ps1
#
# Что делает:
#   1. Чистит dist\ и build\work-*\
#   2. Запускает PyInstaller для GUI и службы (onedir)
#   3. Запускает Inno Setup и собирает dist\installer\BackupBotsSetup.exe

param(
    [string]$Python = ".\.venv\Scripts\python.exe",
    [string]$Iscc = ""
)

if ([string]::IsNullOrWhiteSpace($Iscc)) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $Iscc = $c; break }
    }
}

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== Очистка dist\ и build\work-* ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force "dist\BackupApp" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "dist\BackupService" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "dist\installer" -ErrorAction SilentlyContinue
Get-ChildItem "build" -Filter "work-*" -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

Write-Host "=== PyInstaller: BackupApp (GUI) ===" -ForegroundColor Cyan
& $Python -m PyInstaller --noconfirm --workpath "build\work-gui" --distpath "dist" "build\gui.spec"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller GUI failed" }

Write-Host "=== PyInstaller: BackupService ===" -ForegroundColor Cyan
& $Python -m PyInstaller --noconfirm --workpath "build\work-service" --distpath "dist" "build\service.spec"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller Service failed" }

Write-Host "=== Inno Setup: установщик ===" -ForegroundColor Cyan
if (-not (Test-Path $Iscc)) {
    throw "ISCC.exe не найден: $Iscc. Установите Inno Setup: winget install JRSoftware.InnoSetup"
}
& $Iscc "build\installer.iss"
if ($LASTEXITCODE -ne 0) { throw "ISCC failed" }

$setup = Get-ChildItem "dist\installer\BackupBotsSetup.exe" -ErrorAction SilentlyContinue
if ($setup) {
    Write-Host "" -ForegroundColor Green
    Write-Host "[OK] Установщик готов: $($setup.FullName)" -ForegroundColor Green
    Write-Host "     Размер: $([math]::Round($setup.Length / 1MB, 1)) МБ" -ForegroundColor Green
} else {
    throw "Установщик не создался"
}

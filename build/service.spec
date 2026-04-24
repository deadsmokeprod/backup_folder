# PyInstaller spec для службы (onedir)
# Сборка: pyinstaller build/service.spec --noconfirm

from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH).resolve().parent  # noqa: F821
src_root = project_root / "src"

a = Analysis(
    [str(src_root / "service" / "service_main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "win32timezone",
        "servicemanager",
        "win32event",
        "win32service",
        "win32serviceutil",
        "win32api",
        "win32con",
        "pywintypes",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["PySide6"],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BackupService",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="BackupService",
)

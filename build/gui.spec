# PyInstaller spec для GUI (onedir)
# Сборка: pyinstaller build/gui.spec --noconfirm

from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH).resolve().parent  # noqa: F821
src_root = project_root / "src"

a = Analysis(
    [str(src_root / "gui" / "app.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(src_root / "gui" / "theme" / "dark_anime.qss"), "src/gui/theme"),
        (str(src_root / "gui" / "assets"), "src/gui/assets"),
    ],
    hiddenimports=["PySide6.QtSvg"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

icon_path = src_root / "gui" / "assets" / "app.ico"
icon_arg = str(icon_path) if icon_path.exists() else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BackupApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon_arg,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="BackupApp",
)

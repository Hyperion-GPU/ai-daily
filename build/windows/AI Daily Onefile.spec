# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPEC).resolve().parents[2]
ICON = ROOT / "assets" / "branding" / "ai-daily.ico"

datas = [
    (str(ROOT / "config.yaml"), "."),
    (str(ROOT / "prompts"), "prompts"),
    (str(ROOT / "assets" / "branding"), "assets/branding"),
    (str(ROOT / "assets" / "fonts"), "assets/fonts"),
    (str(ROOT / "src" / "desktop" / "resources.rcc"), "src/desktop"),
]

hiddenimports = collect_submodules("keyring.backends") + [
    "src.desktop.qml_app",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickControls2",
]

a = Analysis(
    [str(ROOT / "desktop_main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AI Daily",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=str(ICON),
)

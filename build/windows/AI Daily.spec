# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPEC).resolve().parents[2]
ICON = ROOT / "assets" / "branding" / "ai-daily.ico"

datas = [
    (str(ROOT / "config.yaml"), "."),
    (str(ROOT / "prompts"), "prompts"),
    (str(ROOT / "assets" / "branding"), "assets/branding"),
]

hiddenimports = collect_submodules("keyring.backends")

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
    [],
    exclude_binaries=True,
    name="AI Daily",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=str(ICON),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AI Daily",
)


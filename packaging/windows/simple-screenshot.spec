# -*- mode: python ; coding: utf-8 -*-
# Сборка: pyinstaller simple-screenshot.spec  (запускать на Windows)
import os
from pathlib import Path

block_cipher = None

# SPECPATH — каталог, где лежит этот .spec (packaging/windows)
spec_dir = Path(SPECPATH)
src_dir = (spec_dir / ".." / ".." / "src").resolve()

a = Analysis(
    [str(src_dir / "main.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[
        (str(src_dir / "assets"), "assets"),
    ],
    hiddenimports=[
        "hotkey.windows",
        "autostart.windows",
        "region_overlay",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Xlib используется только на Linux (X11) и на Windows не нужен —
    # исключаем его, чтобы избежать лишних предупреждений при анализе.
    excludes=["Xlib"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SimpleScreenshot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # без консольного окна — фоновое приложение с треем
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(src_dir / "assets" / "simple-screenshot.ico"),
)

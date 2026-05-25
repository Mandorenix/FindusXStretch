# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path.cwd()
icon_path = project_root / "assets" / "findus_stretching_icon.ico"
version_info_path = project_root / "assets" / "version_info.txt"
datas = []

if (project_root / "assets" / "findus_stretching_icon.png").exists():
    datas.append((str(project_root / "assets" / "findus_stretching_icon.png"), "assets"))

if (project_root / "assets" / "icon_variants").exists():
    for splash_path in (project_root / "assets" / "icon_variants").glob("findus_cat_*.png"):
        datas.append((str(splash_path), "assets/icon_variants"))


a = Analysis(
    ["app.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    name="findus_stretching",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
    version=str(version_info_path) if version_info_path.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="findus_stretching",
)

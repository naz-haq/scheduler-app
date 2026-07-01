# -*- mode: python ; coding: utf-8 -*-

import sys


a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[('templates', 'templates'), ('static', 'static'), ('scheduler.py', '.')],
    hiddenimports=['openpyxl', 'scheduler', 'reportlab', 'webview'],
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
    name='app',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app',
)

# Di macOS, bungkus jadi .app agar bisa dobel-klik seperti aplikasi biasa.
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Jadwal Farmasi.app',
        icon=None,
        bundle_identifier='id.farmasi.jadwal',
    )

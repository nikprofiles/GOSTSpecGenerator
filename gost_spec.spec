# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file для Генератора спецификаций ГОСТ 21.110

a = Analysis(
    ['main.py'],
    pathex=['C:/GOSTSpec'],
    binaries=[],
    datas=[
        ('fonts/*.ttf', 'fonts'),
        ('resources/*.xlsx', 'resources'),
    ],
    hiddenimports=[
        'reportlab.graphics.barcode.common',
        'reportlab.graphics.barcode.code128',
        'reportlab.rl_config',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GOSTSpecGenerator',
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

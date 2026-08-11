# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Collect static web assets and sample datasets
datas = [
    ('linelist_cleaner/web/static', 'linelist_cleaner/web/static'),
    ('linelist_cleaner/datasets', 'linelist_cleaner/datasets'),
]

hiddenimports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespans',
    'uvicorn.lifespans.on',
    'fastapi',
    'fastapi.staticfiles',
    'starlette',
    'starlette.staticfiles',
    'starlette.responses',
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',
    'pydantic',
    'pydantic_core',
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.utils',
    'rapidfuzz',
    'python_dateutil',
    'dateutil',
    'dateutil.parser',
    'pandas',
    'numpy',
    'jinja2',
    'multipart',
    'python_multipart',
]

a = Analysis(
    ['desktop_launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy'],
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
    name='Linelist_Cleaner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect MediaPipe data files and modules
mediapipe_datas = collect_data_files('mediapipe')
mediapipe_hidden = collect_submodules('mediapipe')

added_files = [
    ('models', 'models'),
    ('assets', 'assets'),
    ('../shared/config.json', 'shared'),
    ('highscore.json', '.'),
] + mediapipe_datas

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'cv2',
        'pygame',
        'numpy',
        'PIL',
        'wave',
        'struct',
        'json',
        'math',
        'random',
        'time',
    ] + mediapipe_hidden,
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
    [],
    exclude_binaries=True,
    name='FruitNinja_AI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Useful for logs and diagnostics; set False for pure windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FruitNinja_AI',
)

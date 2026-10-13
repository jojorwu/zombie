# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import platform
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

machine = platform.machine().lower()
if 'arm' in machine or 'aarch64' in machine:
    target_arch = 'arm64'
elif 'x86_64' in machine or 'amd64' in machine:
    target_arch = 'x86_64'
else:
    target_arch = None

datas = [
    ('config.json', '.'),
    ('mods', 'mods'),
]

hiddenimports = [
    'pygame',
    'torch',
    'numpy',
    'lupa',
    'utils.p_np_math',
    'utils.mod_utility',
    'utils.dev_utility',
] + collect_submodules('src') + collect_submodules('utils')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='zombie_simulation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
)

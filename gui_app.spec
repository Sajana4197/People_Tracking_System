# -*- mode: python ; coding: utf-8 -*-
import sys ; sys.setrecursionlimit(sys.getrecursionlimit() * 5)
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Add all AI modules explicitly
datas = [
    ('human-eye.jpg', '.'),
    ('app.ico', '.'),
    ('yolov8n.pt', '.'),
    ('detector.py', '.'),
    ('tracker.py', '.'),
    ('counter.py', '.'),
    ('visualizer.py', '.'),
]

# Collect data for all dependencies
def get_datas():
    extra_datas = []
    for package in ['ultralytics', 'torch', 'torchvision', 'opencv-python', 'deep-sort-realtime']:
        try:
            datas, binaries, hiddenimports = collect_all(package)
            extra_datas.extend(datas)
        except:
            pass
    return extra_datas

datas = datas + get_datas()

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'detector',
        'tracker', 
        'counter',
        'visualizer',
        'cv2',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'numpy',
        'ultralytics',
        'ultralytics.models',
        'ultralytics.nn',
        'ultralytics.utils',
        'torch',
        'torchvision',
        'deep_sort_realtime',
        'deep_sort_realtime.deepsort_tracker',
    ],
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
    name='Real Time People Counting & Tracking System',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Keep console visible for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Real Time People Counting & Tracking System'
)
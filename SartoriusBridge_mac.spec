# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SartoriusBridge on macOS
Creates a menu bar app bundle
"""

import os
import sys

block_cipher = None

# Find libusb library
libusb_paths = [
    '/opt/homebrew/lib/libusb-1.0.dylib',  # Apple Silicon
    '/opt/homebrew/lib/libusb-1.0.0.dylib',
    '/usr/local/lib/libusb-1.0.dylib',  # Intel Mac
    '/usr/local/lib/libusb-1.0.0.dylib',
]

libusb_binary = None
for path in libusb_paths:
    if os.path.exists(path):
        libusb_binary = path
        break

binaries = []
if libusb_binary:
    binaries.append((libusb_binary, '.'))

a = Analysis(
    ['sartorius_menubar.py'],
    pathex=[],
    binaries=binaries,
    datas=[
        ('sartorius_web_server.py', '.'),
        ('sartorius_core.py', '.'),
        ('sartorius_scale_base.py', '.'),
        ('sartorius_scale_macos.py', '.'),
        ('menubar_green.png', '.'),
        ('menubar_yellow.png', '.'),
        ('menubar_gray.png', '.'),
    ],
    hiddenimports=[
        'usb',
        'usb.core',
        'usb.util',
        'usb.backend',
        'usb.backend.libusb1',
        'websockets',
        'websockets.server',
        'websockets.asyncio',
        'websockets.asyncio.server',
        'websockets.exceptions',
        'rumps',
        'asyncio',
        'json',
        'threading',
        'sartorius_core',
        'sartorius_scale_base',
        'sartorius_scale_macos',
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
    [],
    exclude_binaries=True,
    name='SartoriusBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SartoriusBridge',
)

app = BUNDLE(
    coll,
    name='SartoriusBridge.app',
    icon='assets/SartoriusBridge.icns',
    bundle_identifier='com.focalfinishes.sartoriusbridge',
    info_plist={
        'CFBundleName': 'SartoriusBridge',
        'CFBundleDisplayName': 'Sartorius Bridge',
        'CFBundleVersion': '1.4.1',
        'CFBundleShortVersionString': '1.4.1',
        'LSUIElement': True,  # Hide from dock (menu bar app)
        'NSHighResolutionCapable': True,
    },
)

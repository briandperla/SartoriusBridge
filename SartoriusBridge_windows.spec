# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SartoriusBridge on Windows
Creates a system tray app executable using pyserial for COM port communication
"""

block_cipher = None

a = Analysis(
    ['sartorius_tray_windows.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('sartorius_web_server_windows.py', '.'),
        ('sartorius_scale_windows.py', '.'),
    ],
    hiddenimports=[
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'serial.tools.list_ports_common',
        'serial.tools.list_ports_windows',
        'websockets',
        'websockets.server',
        'websockets.asyncio',
        'websockets.asyncio.server',
        'pystray',
        'pystray._win32',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'asyncio',
        'json',
        'threading',
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
    name='SartoriusBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/SartoriusBridge.ico',
)

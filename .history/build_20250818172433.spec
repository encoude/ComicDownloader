# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 替换为您的实际脚本文件名
script_name = 'Jm_Downloader.py'

a = Analysis(
    [script_name],
    pathex=[],
    binaries=[],
    datas=[
        ('pink Gril.png', '.'),  # 包含背景图片
        ('black.ico', '.'),# 包含ico图片
        ('config.ini', '.'), # 包含配置文件
    ],
    hiddenimports=[
        'jmcomic',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'requests',
        'bs4',
        'lxml',
        'configparser',
        're',
        'logging',
        'datetime',
        'os',
        'sys',
        'jmcomic.api',
        'jmcomic.utils'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt5', 
        'PyQt5.QtCore', 
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'tkinter',
        'unittest',
    ],
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
    name='JmComicDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='black.ico',  # 修正为正确的图标文件
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=False,
)
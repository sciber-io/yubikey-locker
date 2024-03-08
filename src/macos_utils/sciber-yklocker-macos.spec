# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['../sciber_yklocker/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='sciber-yklocker-macos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['../../images/sciber_yklocker.png'],
)
app = BUNDLE(
    exe,
    name='sciber-yklocker-macos.app',
    icon='../../images/sciber_yklocker.png',
    bundle_identifier='io.sciber.sciberyklocker',
    version='0.0.55',
)

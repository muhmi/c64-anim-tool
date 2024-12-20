# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/animation_converter/main.py'],
    pathex=['src', 'src/animation_converter'],
    binaries=[],
    datas=[('src/resources/test-program', 'src/resources/test-program'), ('bins', 'bins')],
    hiddenimports=['numba'],
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
    name='animation-tool',
    debug=False,
    bootloader_ignore_signals=True,
    strip=False,
    upx=False,
    console=True,
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
    upx=False,
    upx_exclude=[],
    name='animation-tool',
)

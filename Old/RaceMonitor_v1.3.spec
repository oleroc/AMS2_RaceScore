# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['RaceMonitor_v1.3.py'],
    pathex=[],
    binaries=[],
    datas=[('Bronse.png', '.'), ('Gold.png', '.'), ('lastplace.png', '.'), ('Name.png', '.'), ('Place.png', '.'), ('Points.png', '.'), ('Silver.png', '.'), ('Table_background.png', '.'), ('LiveRace_LiveView.jpg', '.'), ('LiveRace_Status.jpg', '.'), ('RockyTM.ico', '.')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='AMS2 RaceMonitor_v1.3',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='RockyTM.ico',	
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
    name='AMS2 RaceMonitor_v1.3'
)
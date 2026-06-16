# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置（在 macOS 上构建，产出 视频一键发布.app）。

要点：
- 通过 collect_all('playwright') 收集 Playwright 的 node 驱动与随附浏览器；
- 构建前需用 PLAYWRIGHT_BROWSERS_PATH=0 安装 chromium，使其落在包内被一起收集；
- 静态网页与默认配置一并打包。
"""
from PyInstaller.utils.hooks import collect_all

datas = [("app/static", "app/static"), ("config/settings.json", "config")]
binaries = []
hiddenimports = [
    "uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto",
    "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan", "uvicorn.lifespan.on",
]

for _pkg in ("playwright",):
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name="视频一键发布",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="视频一键发布",
)

app = BUNDLE(
    coll,
    name="视频一键发布.app",
    icon=None,
    bundle_identifier="com.fabu.videopublisher",
    info_plist={
        "CFBundleName": "视频一键发布",
        "CFBundleDisplayName": "视频一键发布",
        "LSBackgroundOnly": False,
        "NSHighResolutionCapable": True,
    },
)

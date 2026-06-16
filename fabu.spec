# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置（在 macOS 上构建，产出 视频一键发布.app）。

要点：
- 通过 collect_all('playwright') 收集 Playwright 的 node 驱动与随附浏览器；
- 构建前需用 PLAYWRIGHT_BROWSERS_PATH=0 安装 chromium，使其落在包内被一起收集；
- 静态网页与默认配置一并打包。
"""
import os
import playwright as _pw
from PyInstaller.utils.hooks import collect_all
from PyInstaller.building.datastruct import Tree

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

# 关键：把随附的 Chromium 浏览器从 binaries 中剔除，改为「数据原样拷贝」。
# 否则 PyInstaller 会尝试对 Chromium.app 内的可执行文件逐个 codesign，在 macOS 上会失败。
_BROWSERS_MARK = os.path.join("driver", "package", ".local-browsers")
binaries = [e for e in binaries if _BROWSERS_MARK not in (e[0] or "") and _BROWSERS_MARK not in (e[1] or "")]
datas = [e for e in datas if _BROWSERS_MARK not in (e[0] or "") and _BROWSERS_MARK not in (e[1] or "")]

_browsers_src = os.path.join(os.path.dirname(_pw.__file__), "driver", "package", ".local-browsers")
if os.path.isdir(_browsers_src):
    datas += Tree(
        _browsers_src,
        prefix=os.path.join("playwright", "driver", "package", ".local-browsers"),
    )

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

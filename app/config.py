"""配置加载与路径解析。

区分两类路径：
- BUNDLE_ROOT：只读资源（网页静态文件、默认配置）。打包后在解压目录 sys._MEIPASS。
- DATA_ROOT  ：可写持久数据（登录态 cookies、日志、视频、任务记录、用户配置）。
               打包后放用户主目录下的「视频一键发布数据」，便于持久化且可写。
开发态下两者都是项目根目录。
"""
import json
import sys
from pathlib import Path

_FROZEN = getattr(sys, "frozen", False)

if _FROZEN:
    BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    DATA_ROOT = Path.home() / "视频一键发布数据"
else:
    BUNDLE_ROOT = Path(__file__).resolve().parent.parent
    DATA_ROOT = BUNDLE_ROOT

DATA_ROOT.mkdir(parents=True, exist_ok=True)

# 兼容旧引用
ROOT = DATA_ROOT

_BUNDLED_SETTINGS = BUNDLE_ROOT / "config" / "settings.json"
_USER_SETTINGS = DATA_ROOT / "config" / "settings.json"

_DEFAULTS = {
    "server": {"host": "127.0.0.1", "port": 8800},
    "browser": {
        "headless": False,
        "channel": "chrome",
        "slow_mo_ms": 0,
        "login_timeout_sec": 180,
        "action_timeout_sec": 60,
        "upload_timeout_sec": 1800,
        "keep_open_seconds": 600,
    },
    "paths": {
        "cookies_dir": "data/cookies",
        "logs_dir": "logs",
        "videos_dir": "videos",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load() -> dict:
    cfg = dict(_DEFAULTS)
    for f in (_BUNDLED_SETTINGS, _USER_SETTINGS):  # 用户配置可覆盖打包默认
        if f.exists():
            try:
                cfg = _deep_merge(cfg, json.loads(f.read_text(encoding="utf-8")))
            except Exception as e:  # noqa: BLE001
                print(f"[config] {f} 解析失败，忽略: {e}")
    return cfg


SETTINGS = load()


def abspath(relative: str) -> Path:
    """把配置里的相对路径转为绝对路径（数据类路径基于可写的 DATA_ROOT）。"""
    p = Path(relative)
    return p if p.is_absolute() else (DATA_ROOT / p)


def static_dir() -> Path:
    return BUNDLE_ROOT / "app" / "static"


def cookies_dir() -> Path:
    d = abspath(SETTINGS["paths"]["cookies_dir"])
    d.mkdir(parents=True, exist_ok=True)
    return d


def logs_dir() -> Path:
    d = abspath(SETTINGS["paths"]["logs_dir"])
    d.mkdir(parents=True, exist_ok=True)
    return d


def videos_dir() -> Path:
    d = abspath(SETTINGS["paths"]["videos_dir"])
    d.mkdir(parents=True, exist_ok=True)
    return d

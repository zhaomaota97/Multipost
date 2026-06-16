"""启动入口：python run.py"""
import sys

# Windows 控制台默认编码（cp1252/cp936）打印中文会崩溃，统一改为 UTF-8。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 -- 老环境无 reconfigure 时忽略
        pass

from app.main import run

if __name__ == "__main__":
    run()

"""打包版启动入口：双击后启动本地服务并自动打开浏览器。

与 run.py 的区别：打包态下让 Playwright 使用随程序一起打包的 Chromium，
并在服务起来后自动打开默认浏览器。
"""
import os
import sys

# 打包态：让 Playwright 在程序内部（随附）查找 Chromium，无需用户另装浏览器。
# 必须在导入 playwright/app 之前设置。
if getattr(sys, "frozen", False):
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

import threading  # noqa: E402
import time  # noqa: E402
import webbrowser  # noqa: E402

from app import config  # noqa: E402
from app.main import app  # noqa: E402


def _open_browser(url: str):
    time.sleep(2.5)
    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001
        pass


def main():
    import uvicorn

    s = config.SETTINGS["server"]
    url = f"http://{s['host']}:{s['port']}"
    threading.Thread(target=_open_browser, args=(url,), daemon=True).start()
    print(f"\n  视频一键发布已启动 → {url}\n  （关闭本程序即停止服务）\n")
    uvicorn.run(app, host=s["host"], port=s["port"], log_level="info")


if __name__ == "__main__":
    main()

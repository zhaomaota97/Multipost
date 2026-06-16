"""打包版启动入口：双击后启动本地服务并自动打开浏览器。

与 run.py 的区别：打包态下让 Playwright 使用随程序一起打包的 Chromium，
并在服务起来后自动打开默认浏览器。
"""
import os
import sys

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


def _ensure_browser():
    """确保 Chromium 内核已安装；首次运行时自动下载（约 150MB，仅一次）。"""
    from pathlib import Path

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            if Path(p.chromium.executable_path).exists():
                return  # 已安装
    except Exception:  # noqa: BLE001
        pass

    print("首次运行：正在下载浏览器内核（约 150MB，仅需一次，请耐心等待）……")
    try:
        import subprocess
        from playwright._impl._driver import compute_driver_executable, get_driver_env

        node, cli = compute_driver_executable()
        subprocess.run([node, cli, "install", "chromium"], env=get_driver_env(), check=False)
        print("浏览器内核准备完成。")
    except Exception as e:  # noqa: BLE001
        print(f"浏览器内核下载失败：{e}\n请确保电脑能联网后重新打开本程序。")


def main():
    import uvicorn

    _ensure_browser()
    s = config.SETTINGS["server"]
    url = f"http://{s['host']}:{s['port']}"
    threading.Thread(target=_open_browser, args=(url,), daemon=True).start()
    print(f"\n  视频一键发布已启动 → {url}\n  （关闭本程序即停止服务）\n")
    uvicorn.run(app, host=s["host"], port=s["port"], log_level="info")


if __name__ == "__main__":
    main()

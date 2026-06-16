"""Playwright 浏览器管理（同步 API，跑在后台线程里）。

- 登录：打开平台登录页，等待用户扫码，成功后把登录态保存到 cookies 文件。
- 复用：发布时用已保存的 storage_state 启动上下文，免去重复登录。
"""
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from . import config

_BROWSER_CFG = config.SETTINGS["browser"]


def cookie_file(platform_key: str) -> Path:
    return config.cookies_dir() / f"{platform_key}.json"


def has_cookie(platform_key: str) -> bool:
    return cookie_file(platform_key).exists()


def _launch(p, headless: bool) -> Browser:
    """启动浏览器。优先用系统安装的 Chrome（channel=chrome），失败回退到 Playwright 自带 Chromium。"""
    channel = _BROWSER_CFG.get("channel") or None
    slow_mo = _BROWSER_CFG.get("slow_mo_ms", 0)
    launch_args = ["--disable-blink-features=AutomationControlled"]
    try:
        return p.chromium.launch(
            headless=headless, channel=channel, slow_mo=slow_mo, args=launch_args
        )
    except Exception:  # noqa: BLE001 -- 没装 Chrome 时回退
        return p.chromium.launch(headless=headless, slow_mo=slow_mo, args=launch_args)


def _new_context(browser: Browser, storage_state: Path | None) -> BrowserContext:
    kwargs = {
        "viewport": {"width": 1440, "height": 900},
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
    }
    if storage_state and storage_state.exists():
        kwargs["storage_state"] = str(storage_state)
    ctx = browser.new_context(**kwargs)
    ctx.set_default_timeout(_BROWSER_CFG.get("action_timeout_sec", 60) * 1000)
    # 抹掉 navigator.webdriver
    ctx.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
    )
    return ctx


@contextmanager
def session(platform_key: str, headless: bool | None = None):
    """打开一个带登录态的浏览器会话，yield (context, page)。"""
    if headless is None:
        headless = _BROWSER_CFG.get("headless", False)
    storage = cookie_file(platform_key)
    with sync_playwright() as p:
        browser = _launch(p, headless)
        ctx = _new_context(browser, storage if storage.exists() else None)
        page = ctx.new_page()
        try:
            yield ctx, page
        finally:
            try:
                ctx.close()
            except Exception:  # noqa: BLE001
                pass
            try:
                browser.close()
            except Exception:  # noqa: BLE001
                pass


def save_state(ctx: BrowserContext, platform_key: str) -> None:
    ctx.storage_state(path=str(cookie_file(platform_key)))

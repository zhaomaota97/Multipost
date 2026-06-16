"""账号管理：扫码登录、登录态检查。

登录是长耗时操作（要等人扫码），放后台线程执行，网页端轮询状态。
"""
import threading
import traceback

from . import browser as browser_mod, logger as log_mod
from .publishers import get_publisher, platform_list

# 每个平台的登录任务状态
IDLE = "idle"
WAITING = "waiting"   # 浏览器已打开，等待扫码
SUCCESS = "success"
FAILED = "failed"

_login_state: dict[str, dict] = {}
_lock = threading.Lock()


def _set_state(platform: str, status: str, message: str = ""):
    with _lock:
        _login_state[platform] = {"status": status, "message": message}


def get_login_state(platform: str) -> dict:
    with _lock:
        return dict(_login_state.get(platform, {"status": IDLE, "message": ""}))


def start_login(platform: str) -> dict:
    """启动一个登录后台线程；若已在进行则直接返回当前状态。"""
    with _lock:
        cur = _login_state.get(platform)
        if cur and cur["status"] == WAITING:
            return dict(cur)
    _set_state(platform, WAITING, "正在打开浏览器，请扫码……")
    t = threading.Thread(target=_login_worker, args=(platform,), daemon=True)
    t.start()
    return get_login_state(platform)


def _login_worker(platform: str):
    tl = log_mod.root
    try:
        pub = get_publisher(platform)
    except KeyError as e:
        _set_state(platform, FAILED, str(e))
        return
    try:
        # 登录必须有头（headless=False）才能扫码
        with browser_mod.session(platform, headless=False) as (ctx, page):
            pub.login(page, ctx, tl)
        _set_state(platform, SUCCESS, "登录成功，登录态已保存")
    except Exception as e:  # noqa: BLE001
        tl.error(f"[{platform}] 登录失败：{e}")
        tl.error(traceback.format_exc())
        _set_state(platform, FAILED, str(e))


def check_login(platform: str) -> dict:
    """打开浏览器用已保存登录态检查是否仍有效。"""
    if not browser_mod.has_cookie(platform):
        return {"platform": platform, "logged_in": False, "message": "未登录"}
    try:
        pub = get_publisher(platform)
        with browser_mod.session(platform, headless=True) as (ctx, page):
            ok = pub.check_login(page, log_mod.root)
        return {
            "platform": platform,
            "logged_in": ok,
            "message": "登录态有效" if ok else "登录态已失效，请重新扫码",
        }
    except Exception as e:  # noqa: BLE001
        return {"platform": platform, "logged_in": False, "message": f"检查出错：{e}"}


def accounts_overview() -> list[dict]:
    out = []
    for p in platform_list():
        key = p["key"]
        st = get_login_state(key)
        out.append(
            {
                "key": key,
                "name": p["name"],
                "has_cookie": browser_mod.has_cookie(key),
                "login_status": st["status"],
                "login_message": st["message"],
            }
        )
    return out

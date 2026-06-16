"""发布任务管理：创建任务、后台逐平台执行、状态与日志跟踪、持久化。

线程模型：每个任务在独立后台线程里跑（用同步版 Playwright）。
单个任务内部按平台顺序执行，互不影响——某平台失败不影响其它平台。
"""
import json
import threading
import traceback
from datetime import datetime
from pathlib import Path

from . import config, logger as log_mod, browser as browser_mod
from .publishers import get_publisher
from .publishers.base import LoginExpired, PublishError

_TASKS_FILE = config.abspath("data/tasks.json")
_LOCK = threading.Lock()

# 平台执行状态
PENDING = "pending"
RUNNING = "running"
SUCCESS = "success"
FAILED = "failed"
LOGIN_EXPIRED = "login_expired"  # 需要人工重新登录

_tasks: dict[str, dict] = {}


def _now_id() -> str:
    # 调用方在锁内生成，保证唯一
    base = datetime.now().strftime("%Y%m%d-%H%M%S")
    n = 0
    tid = base
    while tid in _tasks:
        n += 1
        tid = f"{base}-{n}"
    return tid


def _load():
    global _tasks
    if _TASKS_FILE.exists():
        try:
            _tasks = json.loads(_TASKS_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            _tasks = {}


def _persist():
    try:
        _TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _TASKS_FILE.write_text(
            json.dumps(_tasks, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:  # noqa: BLE001
        log_mod.root.error(f"持久化任务失败: {e}")


_load()


def create_task(
    *,
    title: str,
    description: str,
    tags: list[str],
    video_path: str,
    platforms: list[str],
    publish_at: str | None,
) -> dict:
    with _LOCK:
        tid = _now_id()
        task = {
            "id": tid,
            "title": title,
            "description": description,
            "tags": tags,
            "video_path": video_path,
            "publish_at": publish_at,  # ISO 字符串或 None
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "platforms": {
                p: {"status": PENDING, "message": ""} for p in platforms
            },
            "done": False,
        }
        _tasks[tid] = task
        _persist()
    # 启动后台线程执行
    t = threading.Thread(target=_run_task, args=(tid,), daemon=True)
    t.start()
    return task


def _update_platform(tid: str, platform: str, status: str, message: str = ""):
    with _LOCK:
        task = _tasks.get(tid)
        if not task:
            return
        task["platforms"][platform]["status"] = status
        if message:
            task["platforms"][platform]["message"] = message
        _persist()


def _mark_done(tid: str):
    with _LOCK:
        task = _tasks.get(tid)
        if task:
            task["done"] = True
            _persist()


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:  # noqa: BLE001
        return None


def _linger(page, tl, platform_name: str):
    """发布结束后保持浏览器窗口打开，直到用户手动关闭或超时。"""
    secs = config.SETTINGS["browser"].get("keep_open_seconds", 600)
    if secs <= 0:
        return
    tl.info(
        f"[{platform_name}] 流程结束，浏览器窗口保持打开（最多 {secs} 秒），"
        f"你可以核对结果，处理完手动关闭该窗口即可。"
    )
    waited, step = 0, 2000
    while waited < secs * 1000:
        try:
            if page.is_closed():
                tl.info(f"[{platform_name}] 窗口已手动关闭。")
                return
            page.wait_for_timeout(step)
        except Exception:  # noqa: BLE001 -- 窗口/上下文被关闭
            return
        waited += step
    tl.info(f"[{platform_name}] 窗口保持已超时，自动关闭。")


def _run_task(tid: str):
    task = _tasks.get(tid)
    if not task:
        return
    tl = log_mod.get_task_logger(tid)
    tl.info("=" * 60)
    tl.info(f"任务 {tid} 开始")
    tl.info(f"标题：{task['title']}")
    tl.info(f"视频：{task['video_path']}")
    tl.info(f"平台：{', '.join(task['platforms'].keys())}")
    tl.info(f"定时：{task['publish_at'] or '立即发布'}")

    video = task["video_path"]
    if not Path(video).exists():
        for p in task["platforms"]:
            _update_platform(tid, p, FAILED, "视频文件不存在")
        tl.error(f"视频文件不存在：{video}")
        _mark_done(tid)
        return

    publish_at = _parse_dt(task["publish_at"])

    for platform_key in list(task["platforms"].keys()):
        _update_platform(tid, platform_key, RUNNING)
        try:
            pub = get_publisher(platform_key)
        except KeyError as e:
            _update_platform(tid, platform_key, FAILED, str(e))
            continue

        tl.info("-" * 60)
        tl.info(f"开始处理平台：{pub.platform_name}")

        if not browser_mod.has_cookie(platform_key):
            msg = "尚未登录，请到「账号管理」扫码登录"
            tl.warning(f"[{pub.platform_name}] {msg}")
            _update_platform(tid, platform_key, LOGIN_EXPIRED, msg)
            continue

        try:
            with browser_mod.session(platform_key) as (ctx, page):
                try:
                    pub.publish(
                        page,
                        tl,
                        video_path=video,
                        title=task["title"],
                        description=task["description"],
                        tags=task["tags"],
                        publish_at=publish_at,
                    )
                    _update_platform(tid, platform_key, SUCCESS, "发布完成")
                except LoginExpired as e:
                    tl.warning(str(e))
                    _update_platform(tid, platform_key, LOGIN_EXPIRED, str(e))
                except PublishError as e:
                    tl.error(f"[{pub.platform_name}] 发布失败：{e}")
                    _update_platform(tid, platform_key, FAILED, str(e))
                except Exception as e:  # noqa: BLE001
                    tl.error(f"[{pub.platform_name}] 未预期错误：{e}")
                    tl.error(traceback.format_exc())
                    _update_platform(tid, platform_key, FAILED, str(e))
                # 发布结束后保持窗口打开，便于查看结果/处理异常，直到手动关闭或超时
                _linger(page, tl, pub.platform_name)
        except Exception as e:  # noqa: BLE001 -- 浏览器启动等会话级错误
            tl.error(f"[{pub.platform_name}] 浏览器会话错误：{e}")
            _update_platform(tid, platform_key, FAILED, str(e))

    tl.info("=" * 60)
    tl.info(f"任务 {tid} 结束")
    _mark_done(tid)


def get_task(tid: str) -> dict | None:
    return _tasks.get(tid)


def list_tasks() -> list[dict]:
    return sorted(_tasks.values(), key=lambda t: t["id"], reverse=True)

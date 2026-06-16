"""验证小红书：定时设置 + 发布按钮定位（设合法未来时间，定位到按钮但不点击发布）。"""
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import browser as b  # noqa: E402
from app.publishers import _utils as u  # noqa: E402
from app.publishers.xiaohongshu import XiaohongshuPublisher  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("dry")
vids = [p for p in (ROOT / "videos").iterdir() if p.suffix.lower() in {".mp4", ".mov", ".m4v"}]
pub = XiaohongshuPublisher()
publish_at = (datetime.now() + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)

with b.session("xiaohongshu", headless=False) as (ctx, page):
    page.goto(pub.publish_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    fi = u.find_file_input(page, 20000, "input.upload-input") or u.find_file_input(page, 10000)
    fi.set_input_files(str(vids[0]))
    u.first_visible(page, ["text=上传成功", "text=分辨率", "text=重新上传"], 120000)
    page.wait_for_timeout(2000)
    ti = u.first_visible(page, ["input[placeholder*='填写标题']"], 8000)
    if ti: ti.click(); page.keyboard.type("按钮定位验证-请勿发布")

    log.info(f">>> 设置定时 {publish_at}")
    scheduled = pub._set_schedule(page, log, publish_at)
    log.info(f">>> scheduled={scheduled}")

    btn_text = "定时发布" if scheduled else "发布"
    btn = pub._find_submit_button(page, btn_text) or (pub._find_submit_button(page, "发布") if scheduled else None)
    if btn:
        box = btn.bounding_box()
        log.info(f">>> ✅ 找到提交按钮『{btn_text}』 文本={btn.inner_text()!r} 位置y={box['y'] if box else '?'}")
        btn.scroll_into_view_if_needed()
        log.info(">>> 已滚动到按钮（未点击发布）")
    else:
        log.info(">>> ❌ 仍未找到提交按钮")
    page.screenshot(path=str(ROOT / "logs" / "dryrun_xhs2.png"), full_page=True)
    log.info("已截图 logs/dryrun_xhs2.png。6 秒后关闭。")
    page.wait_for_timeout(6000)

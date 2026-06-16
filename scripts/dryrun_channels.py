"""视频号发布演练：真实执行上传/填写，但在点击「发表」前停下（不真正发布）。"""
import logging
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import browser as b  # noqa: E402
from app.publishers import _utils as u  # noqa: E402

log = logging.getLogger("dryrun")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# 取 videos/ 里第一个视频
vids = [p for p in (ROOT / "videos").iterdir() if p.suffix.lower() in {".mp4", ".mov", ".m4v"}]
if not vids:
    print("videos/ 目录里没有视频，请先放一个"); sys.exit(1)
video = str(vids[0])
print("使用视频:", video)

URL = "https://channels.weixin.qq.com/platform/post/create"
with b.session("weixin_channels", headless=False) as (ctx, page):
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)

    log.info("定位文件上传框…")
    fi = u.first_visible(page, ['input[type="file"]'], 20000) or page.locator('input[type="file"]').first
    log.info("上传视频…")
    fi.set_input_files(video)

    log.info("等待上传完成（发表按钮变可用）…")
    ok = False
    for _ in range(300):
        try:
            btn = page.get_by_role("button", name="发表")
            if btn.count() > 0:
                cls = btn.first.get_attribute("class") or ""
                if "weui-desktop-btn_disabled" not in cls:
                    ok = True
                    break
        except Exception:
            pass
        page.wait_for_timeout(2000)
    log.info(f"上传完成: {ok}")

    log.info("填写描述编辑器…")
    editor = u.first_visible(page, ["div.input-editor", "div[contenteditable='true']"], 10000)
    log.info(f"找到描述编辑器: {editor is not None}")
    if editor:
        editor.click()
        page.keyboard.type("演练标题-请勿发布")
        page.keyboard.press("Enter")
        page.keyboard.type("这是发布流程演练，不会真正发表。")
        page.keyboard.type(" #测试")
        page.wait_for_timeout(1500)
        page.keyboard.press("Enter")

    log.info("定位「发表」按钮（不点击）…")
    pubbtn = u.first_visible(page, ["div.form-btns button:has-text('发表')", "button:has-text('发表')"], 8000)
    log.info(f"找到发表按钮: {pubbtn is not None}")

    log.info("定位「定时」选项…")
    labels = page.locator("label:has-text('定时')")
    log.info(f"「定时」label 数量: {labels.count()}")

    page.screenshot(path=str(ROOT / "logs" / "dryrun_channels.png"), full_page=True)
    log.info("已截图 logs/dryrun_channels.png；演练结束，未发表。3 秒后关闭。")
    page.wait_for_timeout(3000)

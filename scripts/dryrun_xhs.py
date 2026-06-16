"""小红书发布演练：真实走上传/填写流程并逐步报告选择器命中情况，停在发布前不真发。"""
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
from app.publishers.xiaohongshu import XiaohongshuPublisher  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("dryrun")

vids = [p for p in (ROOT / "videos").iterdir() if p.suffix.lower() in {".mp4", ".mov", ".m4v"}]
video = str(vids[0])
pub = XiaohongshuPublisher()
print("视频:", video)
print("发布页:", pub.publish_url)


def report(name, loc):
    print(f"  [{'命中' if loc else '未命中'}] {name}")
    return loc


with b.session("xiaohongshu", headless=False) as (ctx, page):
    page.goto(pub.publish_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    print("当前 URL:", page.url)

    print("\n— 上传视频 —")
    fi = report("文件输入框", u.first_visible(
        page,
        ["div[class^='upload-content'] input[class='upload-input']", "input.upload-input", "input[type=file]"],
        15000,
    ))
    if not fi:
        # 跨 frame 兜底
        for fr in page.frames:
            if fr.locator("input[type=file]").count():
                fi = fr.locator("input[type=file]").first
                print("  (在 iframe 找到文件框:", fr.url, ")")
                break
    if fi:
        fi.set_input_files(video)
        log.info("已选择文件，等待上传完成…")
        done = report("上传完成标志", u.first_visible(
            page, ["text=上传成功", "text=分辨率", ".preview-new:has-text('100%')", "text=重新上传"], 120000))
        page.wait_for_timeout(2000)

    print("\n— 填写信息 —")
    ti = report("标题输入框", u.first_visible(
        page, ["input[placeholder*='填写标题']", "input[placeholder*='标题']"], 8000))
    if ti:
        ti.click(); page.keyboard.type("小红书演练-请勿发布")
    ed = report("正文编辑器", u.first_visible(
        page, ["p[data-placeholder*='输入正文描述']", "div[contenteditable='true']", ".ql-editor"], 6000))
    if ed:
        ed.click(); page.keyboard.type("这是发布流程演练。")

    print("\n— 定时开关 —")
    try:
        sw = page.locator(".custom-switch-card", has_text="定时发布").locator(".d-switch")
        report("定时开关 .custom-switch-card", sw.first if sw.count() else None)
    except Exception as e:
        print("  定时开关探测出错:", e)

    print("\n— 发布按钮 —")
    report("发布按钮", u.first_visible(page, ["button:has-text('发布')", ".publishBtn", "text=发布笔记"], 8000))

    print("\n— 页面候选 input/button 兜底转储 —")
    try:
        info = page.evaluate(
            """() => {
                const ins = [...document.querySelectorAll('input')].slice(0,12).map(e=>({t:e.type,p:e.placeholder,c:e.className}));
                const bs = [...document.querySelectorAll('button')].map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<12);
                return {ins, bs:[...new Set(bs)].slice(0,20)};
            }"""
        )
        for i, el in enumerate(info["ins"]):
            print(f"   input[{i}] type={el['t']} placeholder={el['p']} class={el['c']}")
        print("   buttons:", info["bs"])
    except Exception as e:
        print("  转储出错:", e)

    page.screenshot(path=str(ROOT / "logs" / "dryrun_xhs.png"), full_page=True)
    log.info("已截图 logs/dryrun_xhs.png（未发布）。8 秒后关闭。")
    page.wait_for_timeout(8000)

"""探测小红书发布按钮真实结构 + 定时弹层关闭方式。"""
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

vids = [p for p in (ROOT / "videos").iterdir() if p.suffix.lower() in {".mp4", ".mov", ".m4v"}]
video = str(vids[0])
URL = "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=video"

with b.session("xiaohongshu", headless=False) as (ctx, page):
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    fi = u.find_file_input(page, 20000, "input.upload-input") or u.find_file_input(page, 10000)
    fi.set_input_files(video)
    u.first_visible(page, ["text=上传成功", "text=分辨率", "text=重新上传"], 120000)
    page.wait_for_timeout(2000)

    # 转储所有含“发布”文本的可点击元素
    print("\n=== 含『发布』的可见元素 ===")
    info = page.evaluate(
        """() => {
            const out = [];
            document.querySelectorAll("*").forEach(el => {
                const t = (el.innerText||'').trim();
                const r = el.getBoundingClientRect();
                if (r.width>0 && r.height>0 && (t==='发布'||t==='定时发布'||t==='发布笔记'||t==='暂存离开')) {
                    out.push({tag: el.tagName, role: el.getAttribute('role'), cls: el.className, txt: t});
                }
            });
            // 去重（取最内层：文本最短的祖先链末端）
            return out.slice(0, 25);
        }"""
    )
    for el in info:
        print(f"  <{el['tag']}> role={el['role']} text={el['txt']!r} class={el['cls']}")

    # 打开定时并设时间，看弹层
    print("\n=== 打开定时发布 ===")
    try:
        sw = page.locator(".custom-switch-card", has_text="定时发布").locator(".d-switch")
        sw.first.click()
        page.wait_for_timeout(1000)
        di = u.first_visible(page, [".d-datepicker-input-filter input.d-text", "input.d-text"], 5000)
        print("  时间输入框 readonly:", di.get_attribute("readonly") if di else "N/A")
        if di:
            di.click()
            page.wait_for_timeout(800)
            print("  点击后是否出现日期弹层:", page.locator(".d-datepicker, [class*='picker']").count())
            di.fill("2026-06-18 15:00")
            page.wait_for_timeout(500)
            # 尝试用 ESC / 点别处关闭弹层
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            print("  ESC 后弹层数:", page.locator(".d-datepicker, [class*='picker']:visible").count())
            print("  时间框现值:", di.input_value())
    except Exception as e:
        print("  出错:", e)

    page.screenshot(path=str(ROOT / "logs" / "debug_xhs_btn.png"), full_page=True)
    print("\n已截图 logs/debug_xhs_btn.png；8 秒后关闭。")
    page.wait_for_timeout(8000)

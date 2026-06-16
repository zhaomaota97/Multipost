"""探测视频号「定时发表」日期选择器的真实结构。"""
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
print("视频:", video)

URL = "https://channels.weixin.qq.com/platform/post/create"
with b.session("weixin_channels", headless=False) as (ctx, page):
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    page.locator('input[type="file"]').first.set_input_files(video)

    print("等待上传完成…")
    for _ in range(120):
        btn = page.get_by_role("button", name="发表")
        if btn.count() and "weui-desktop-btn_disabled" not in (btn.first.get_attribute("class") or ""):
            break
        page.wait_for_timeout(2000)
    print("上传完成。")

    # 点击“定时”
    labels = page.locator("label:has-text('定时')")
    print("定时 label 数:", labels.count())
    (labels.nth(1) if labels.count() > 1 else labels.first).click()
    page.wait_for_timeout(1500)

    # 点击只读日期输入框，弹出选择器
    date_input = page.locator("input[placeholder='请选择发表时间']").first
    print("日期输入框存在:", date_input.count() > 0)
    date_input.click()
    page.wait_for_timeout(2000)

    # 转储所有 class 含 picker 的元素
    print("\n=== class 含 'picker' 的元素 ===")
    picker_html = page.evaluate(
        """() => {
            const out = [];
            document.querySelectorAll("[class*='picker']").forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.width>0 && r.height>0)
                    out.push(el.className + ' :: ' + (el.innerText||'').slice(0,60).replace(/\\n/g,'|'));
            });
            return out.slice(0, 40);
        }"""
    )
    for line in picker_html:
        print(" ", line)

    # 弹层里的可点击日期单元格与时间项
    print("\n=== 弹层内 input ===")
    pin = page.locator("[class*='picker'] input")
    for i in range(min(pin.count(), 10)):
        el = pin.nth(i)
        print(f"  input[{i}] readonly={el.get_attribute('readonly')} placeholder={el.get_attribute('placeholder')} class={el.get_attribute('class')}")

    page.screenshot(path=str(ROOT / "logs" / "debug_schedule.png"), full_page=True)
    print("\n已截图 logs/debug_schedule.png；10 秒后关闭，可手动观察弹层。")
    page.wait_for_timeout(10000)

import sys
from pathlib import Path
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import browser as b
from app.publishers import _utils as u
vids = [p for p in (ROOT/"videos").iterdir() if p.suffix.lower() in {".mp4",".mov",".m4v"}]
URL="https://creator.xiaohongshu.com/publish/publish?from=homepage&target=video"
with b.session("xiaohongshu", headless=False) as (ctx,page):
    page.goto(URL, wait_until="domcontentloaded", timeout=60000); page.wait_for_timeout(4000)
    fi=u.find_file_input(page,20000,"input.upload-input") or u.find_file_input(page,10000)
    fi.set_input_files(str(vids[0]))
    u.first_visible(page,["text=上传成功","text=分辨率","text=重新上传"],120000); page.wait_for_timeout(2500)
    # 填标题，确保提交栏出现
    ti=u.first_visible(page,["input[placeholder*='填写标题']"],8000)
    if ti: ti.click(); page.keyboard.type("探测标题")
    page.wait_for_timeout(1000)
    rb=page.get_by_role("button")
    print("role=button 数量:", rb.count())
    for i in range(rb.count()):
        el=rb.nth(i)
        try:
            box=el.bounding_box()
            print(f"  [{i}] text={el.inner_text()[:20]!r} visible={el.is_visible()} box={box}")
        except Exception as e:
            print(f"  [{i}] err {e}")
    # 滚到底（尝试多种滚动）
    page.keyboard.press("End")
    page.mouse.wheel(0,5000); page.wait_for_timeout(800)
    try: page.locator(".has-tips").last.scroll_into_view_if_needed()
    except Exception: pass
    page.wait_for_timeout(800)
    page.screenshot(path=str(ROOT/"logs"/"xhs_viewport_bottom.png"))  # 视口截图(非full_page)
    print("已截图 logs/xhs_viewport_bottom.png")
    page.wait_for_timeout(1000)

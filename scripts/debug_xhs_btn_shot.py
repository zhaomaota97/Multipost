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
    ti=u.first_visible(page,["input[placeholder*='填写标题']"],8000)
    if ti: ti.click(); page.keyboard.type("探测标题")
    page.wait_for_timeout(1000)
    el=page.locator("xhs-publish-btn")
    el.screenshot(path=str(ROOT/"logs"/"xhs_btn_only.png"))
    # 用 JS 找红色像素中心：截图分析交给人看，这里只给几何
    print("box:", el.bounding_box())
    page.wait_for_timeout(800)

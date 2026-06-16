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
    print("frames:", len(page.frames))
    for i,fr in enumerate(page.frames):
        for txt in ["暂存离开","定时发布","发布"]:
            try:
                loc=fr.get_by_text(txt, exact=True)
                n=loc.count()
                if n: print(f"  frame[{i}] {fr.url[:60]} | get_by_text('{txt}',exact) -> {n}")
            except Exception as e:
                pass
    # 也试 button 角色
    for i,fr in enumerate(page.frames):
        try:
            rb=fr.get_by_role("button")
            print(f"  frame[{i}] role=button 数量={rb.count()}")
        except Exception: pass
    page.wait_for_timeout(1000)

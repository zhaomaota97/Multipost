import sys
from pathlib import Path
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app import browser as b  # noqa: E402
from app.publishers import _utils as u  # noqa: E402

vids = [p for p in (ROOT / "videos").iterdir() if p.suffix.lower() in {".mp4", ".mov", ".m4v"}]
URL = "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=video"
with b.session("xiaohongshu", headless=False) as (ctx, page):
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    fi = u.find_file_input(page, 20000, "input.upload-input") or u.find_file_input(page, 10000)
    fi.set_input_files(str(vids[0]))
    u.first_visible(page, ["text=上传成功", "text=分辨率", "text=重新上传"], 120000)
    page.wait_for_timeout(2500)
    # 滚到底
    page.mouse.wheel(0, 4000)
    page.wait_for_timeout(1500)

    data = page.evaluate(
        """() => {
            const out=[];
            [...document.querySelectorAll('*')].forEach(e=>{
                const t=(e.textContent||'').replace(/\\s+/g,'');
                if(t!=='发布' && t!=='定时发布' && t!=='暂存离开') return;
                if([...e.children].some(c=>(c.textContent||'').replace(/\\s+/g,'')===t)) return;
                const r=e.getBoundingClientRect();
                const cs=getComputedStyle(e);
                out.push({tag:e.tagName, cls:e.className, txt:t,
                          x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
                          bg:cs.backgroundColor, cursor:cs.cursor, vis:cs.visibility});
            });
            return out.sort((a,b)=>a.y-b.y);
        }"""
    )
    print(f"共 {len(data)} 个 (发布/定时发布/暂存离开) 叶子元素：")
    for e in data:
        print(f"<{e['tag']}> '{e['txt']}' pos=({e['x']},{e['y']}) {e['w']}x{e['h']} bg={e['bg']} cursor={e['cursor']} vis={e['vis']}")
        print(f"     class={e['cls']}")
    page.wait_for_timeout(1500)

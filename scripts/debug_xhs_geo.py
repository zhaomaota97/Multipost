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
    page.locator(".custom-switch-card", has_text="定时发布").locator(".d-switch").first.click()
    page.wait_for_timeout(1200)
    r = page.evaluate("""() => {
        const sy=window.scrollY, out=[];
        [...document.querySelectorAll('*')].forEach(e=>{
            const rc=e.getBoundingClientRect();
            const absY=rc.y+sy;
            if(absY>1750 && absY<2050 && rc.width>=60 && rc.width<=280 && rc.height>=26 && rc.height<=72){
                const cs=getComputedStyle(e);
                if(cs.cursor==='pointer' || cs.backgroundColor!=='rgba(0, 0, 0, 0)'){
                    const childBtn=[...e.children].some(c=>{const ccs=getComputedStyle(c);return ccs.cursor==='pointer';});
                    out.push({tag:e.tagName,cls:e.className,bg:cs.backgroundColor,cur:cs.cursor,
                              x:Math.round(rc.x),absY:Math.round(absY),w:Math.round(rc.width),h:Math.round(rc.height),
                              txt:(e.textContent||'').replace(/\\s+/g,'').slice(0,8)});
                }
            }
        });
        return out;
    }""")
    print(f"底部区域按钮候选 {len(r)} 个：")
    for e in r:
        print(f"<{e['tag']}> txt='{e['txt']}' bg={e['bg']} cur={e['cur']} pos=({e['x']},{e['absY']}) {e['w']}x{e['h']}")
        print(f"   class={e['cls']}")
    page.wait_for_timeout(1200)

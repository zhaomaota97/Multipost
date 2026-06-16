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
    for i,fr in enumerate(page.frames):
        print(f"\n=== frame[{i}] {fr.url[:70]} ===")
        try:
            r = fr.evaluate("""() => {
                const out=[];
                [...document.querySelectorAll('*')].forEach(e=>{
                    const t=(e.textContent||'').replace(/\\s+/g,'');
                    if((t==='发布'||t==='定时发布'||t==='暂存离开') &&
                       ![...e.children].some(c=>(c.textContent||'').replace(/\\s+/g,'')===t)){
                        const rc=e.getBoundingClientRect(); const cs=getComputedStyle(e);
                        out.push(e.tagName+" '"+t+"' "+Math.round(rc.x)+","+Math.round(rc.y)+" "+Math.round(rc.width)+"x"+Math.round(rc.height)+" bg="+cs.backgroundColor+" cls="+e.className);
                    }
                });
                return out;
            }""")
            for line in r: print("  ", line)
            if not r: print("   (无匹配)")
        except Exception as e:
            print("   eval出错:", e)
    page.wait_for_timeout(1200)

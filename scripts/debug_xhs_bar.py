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
    r = page.evaluate("""() => {
        const W=window.innerWidth,H=window.innerHeight,seen=new Set(),out=[];
        for(let x=W*0.35;x<W*0.8;x+=15){
          const el=document.elementFromPoint(x,H-45);
          if(!el) continue;
          const key=el.tagName+'|'+el.className;
          if(seen.has(key))continue; seen.add(key);
          const cs=getComputedStyle(el),rc=el.getBoundingClientRect();
          out.push({tag:el.tagName,cls:el.className,bg:cs.backgroundColor,cur:cs.cursor,
                    t:(el.textContent||'').replace(/\\s+/g,'').slice(0,8),
                    x:Math.round(rc.x),y:Math.round(rc.y),w:Math.round(rc.width),h:Math.round(rc.height)});
        }
        return out;
    }""")
    print("底部固定栏 (y=H-45) 元素：")
    for e in r:
        print(f"<{e['tag']}> t='{e['t']}' bg={e['bg']} cur={e['cur']} pos=({e['x']},{e['y']}) {e['w']}x{e['h']}")
        print(f"   class={e['cls']}")
    page.wait_for_timeout(1000)

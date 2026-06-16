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
    # 开定时
    page.locator(".custom-switch-card", has_text="定时发布").locator(".d-switch").first.click()
    page.wait_for_timeout(1200)
    info = page.evaluate("""() => {
        const W=window.innerWidth, H=window.innerHeight, seen=new Set(), out=[];
        // 扫描底部 110px 区域
        for(let y=H-10; y>H-110; y-=12){
          for(let x=W*0.3; x<W*0.85; x+=30){
            const el=document.elementFromPoint(x,y);
            if(!el) continue;
            const t=(el.textContent||'').replace(/\\s+/g,'').slice(0,10);
            const key=el.tagName+'|'+el.className+'|'+t;
            if(seen.has(key)) continue; seen.add(key);
            const cs=getComputedStyle(el); const r=el.getBoundingClientRect();
            if(cs.cursor==='pointer' || /发布|暂存/.test(t))
              out.push({tag:el.tagName, cls:el.className, t, bg:cs.backgroundColor,
                        x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
          }
        }
        return {W,H,out};
    }""")
    print("viewport:", info["W"], "x", info["H"])
    for e in info["out"]:
        print(f"<{e['tag']}> t='{e['t']}' bg={e['bg']} pos=({e['x']},{e['y']}) {e['w']}x{e['h']} class={e['cls']}")
    page.wait_for_timeout(1500)

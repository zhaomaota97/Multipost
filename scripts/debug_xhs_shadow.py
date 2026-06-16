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
    r = page.evaluate("""() => {
        // 子串扫描 + shadowRoot 探测
        let hasZancun=0, shadowHosts=[];
        const walk=(root)=>{
          root.querySelectorAll('*').forEach(e=>{
            if((e.textContent||'').includes('暂存')) hasZancun++;
            if(e.shadowRoot){ shadowHosts.push(e.tagName+'.'+e.className); walk(e.shadowRoot); }
          });
        };
        walk(document);
        // 同时找含“暂存离开”的最内层（穿透 open shadow）
        let leaf=null;
        const walk2=(root)=>{
          for(const e of root.querySelectorAll('*')){
            if((e.textContent||'').replace(/\\s/g,'').includes('暂存离开')){
              if(![...e.children].some(c=>(c.textContent||'').includes('暂存'))){ leaf=e.tagName+'.'+e.className; }
            }
            if(e.shadowRoot) walk2(e.shadowRoot);
          }
        };
        walk2(document);
        return {hasZancun, shadowHostsCount:shadowHosts.length, shadowHosts:shadowHosts.slice(0,10), leaf};
    }""")
    print("含'暂存'元素数(穿透open shadow):", r["hasZancun"])
    print("shadowRoot 宿主数:", r["shadowHostsCount"], r["shadowHosts"])
    print("暂存离开 最内层:", r["leaf"])
    page.wait_for_timeout(1200)

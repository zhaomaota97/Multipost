"""列出所有『定时发布』元素的几何与祖先，找出真正的提交按钮。"""
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
    page.wait_for_timeout(2000)
    # 开启定时
    page.locator(".custom-switch-card", has_text="定时发布").locator(".d-switch").first.click()
    page.wait_for_timeout(1500)

    data = page.evaluate(
        """() => {
            const out=[];
            const els=[...document.querySelectorAll('*')].filter(e=>(e.innerText||'').trim()==='定时发布');
            els.forEach(e=>{
                const r=e.getBoundingClientRect();
                if(r.width===0&&r.height===0) return;
                // 最内层优先
                const childSame=[...e.children].some(c=>(c.innerText||'').trim()==='定时发布');
                // 找最近的“按钮样”祖先
                let anc=e, hint='';
                for(let k=0;k<5 && anc;k++){
                    const cs=getComputedStyle(anc);
                    if(cs.cursor==='pointer' || /btn|button|submit/i.test(anc.className)){
                        hint=anc.tagName+'.'+anc.className+' (cursor='+cs.cursor+',bg='+cs.backgroundColor+')';
                        break;
                    }
                    anc=anc.parentElement;
                }
                out.push({tag:e.tagName, cls:e.className, leaf:!childSame,
                          x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
                          clickableAnc:hint});
            });
            return out;
        }"""
    )
    print(f"共 {len(data)} 个『定时发布』元素：")
    for i, e in enumerate(data):
        print(f"\n[{i}] <{e['tag']}> leaf={e['leaf']} pos=({e['x']},{e['y']}) size={e['w']}x{e['h']}")
        print(f"    class={e['cls']}")
        print(f"    可点击祖先={e['clickableAnc']}")
    page.wait_for_timeout(2000)

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
    # 底部区域(y>740) 里文本含 发布/暂存 的最内层元素
    info = page.evaluate(
        """() => {
            const out=[];
            document.querySelectorAll("div,button,span").forEach(el=>{
              const t=(el.innerText||'').trim();
              const r=el.getBoundingClientRect();
              if(r.top>740 && r.width>0 && r.height>0 && (t==='发布'||t==='定时发布'||t==='暂存离开')){
                // 仅最内层：没有同文本子节点
                const childSame=[...el.children].some(c=>(c.innerText||'').trim()===t && c.getBoundingClientRect().width>0);
                if(!childSame) out.push({tag:el.tagName,cls:el.className,txt:t,y:Math.round(r.top)});
              }
            });
            return out;
        }"""
    )
    print("=== 底部按钮(最内层) ===")
    for el in info:
        print(f"  <{el['tag']}> text={el['txt']!r} y={el['y']} class={el['cls']}")
    page.wait_for_timeout(1500)

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

    js = """() => {
        const vh = window.innerHeight, out=[];
        document.querySelectorAll("div,button,span,a").forEach(el=>{
          const r=el.getBoundingClientRect();
          const t=(el.innerText||'').trim();
          // 视口底部栏内、像按钮的元素
          if(r.bottom>vh-90 && r.bottom<=vh+5 && r.width>=50 && r.width<260 && r.height>=24 && t && t.length<=8){
            const childSame=[...el.children].some(c=>(c.innerText||'').trim()===t);
            if(!childSame) out.push({tag:el.tagName,cls:el.className,txt:t,w:Math.round(r.width)});
          }
        });
        return out;
    }"""
    print("=== 非定时：底部栏按钮 ===")
    for el in page.evaluate(js):
        print(f"  <{el['tag']}> w={el['w']} text={el['txt']!r} class={el['cls']}")

    # 开启定时再看一次
    try:
        page.locator(".custom-switch-card", has_text="定时发布").locator(".d-switch").first.click()
        page.wait_for_timeout(1500)
    except Exception as e:
        print("开定时出错:", e)
    print("\n=== 定时开启：底部栏按钮 ===")
    for el in page.evaluate(js):
        print(f"  <{el['tag']}> w={el['w']} text={el['txt']!r} class={el['cls']}")
    page.wait_for_timeout(1500)

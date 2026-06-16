"""通过『暂存离开』定位底部按钮栏，dump 提交按钮的真实结构。"""
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
    page.locator(".custom-switch-card", has_text="定时发布").locator(".d-switch").first.click()
    page.wait_for_timeout(1500)

    info = page.evaluate(
        """() => {
            const save=[...document.querySelectorAll('*')].find(e=>(e.innerText||'').trim()==='暂存离开'
                && ![...e.children].some(c=>(c.innerText||'').trim()==='暂存离开'));
            if(!save) return {err:'没找到 暂存离开'};
            // 向上找同时包含“暂存离开”和“发布”的容器
            let bar=save;
            for(let k=0;k<6;k++){ bar=bar.parentElement; if(!bar) break;
                if(/发布/.test(bar.innerText||'')) break; }
            const kids=[...bar.children].map(c=>{
                const r=c.getBoundingClientRect();
                return {tag:c.tagName, cls:c.className, txt:(c.innerText||'').trim().slice(0,12),
                        x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width)};
            });
            return {barTag:bar.tagName, barCls:bar.className, kids};
        }"""
    )
    print("底部栏容器:", info.get("barTag"), "class=", info.get("barCls"))
    print("子元素：")
    for k in info.get("kids", []):
        print(f"  <{k['tag']}> text={k['txt']!r} pos=({k['x']},{k['y']}) w={k['w']} class={k['cls']}")
    if info.get("err"): print("ERR:", info["err"])
    page.wait_for_timeout(1500)
